import logging
import re
from decimal import Decimal

import anthropic
from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..config import ANTHROPIC_API_KEY
from ..database import get_pool, get_write_pool
from ..limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])

SCHEMA_CONTEXT = """
You are a SQL query generator for a college policy debate database (PostgreSQL).

## Core Tables

tournament(id, name, season, start_date, end_date, is_active, year)
round(id, tournament_id FK, round_number, round_type ['prelim'/'elim'], source, is_active)
team(id, tournament_id FK, team_name, is_active)
  - team_name format: "School XY" (e.g., "Northwestern FM", "Kansas LS")
  - XY are alphabetically sorted initials of the two debaters
  - To find teams from a school: WHERE t.team_name LIKE 'Northwestern %'
debater(id, debater_id, first_name, last_name, tournament_id FK, is_active)
  - debater_id is a code like 'JSMITH' (first initial + last name, uppercase)
  - Same person across tournaments shares debater_id + first_name + last_name
  - Each tournament creates a separate debater row for the same person
judge(id, name, tournament_id FK, is_active)
  - Each tournament creates a separate judge row for the same person
  - To find a judge across tournaments: WHERE j.name ILIKE '%LastName%'
team_debater(team_id FK, debater_id FK) - links debaters to their team
round_result(id, round_id FK, aff_team_id FK, neg_team_id FK, winner, ballot_count, result_type, is_active)
  - winner: 0=Tie (1-1 split, 2-judge panel), 1=Aff won, 2=Neg won, -1=Closeout (same school)
  - result_type: NULL=normal, 'bye', 'forfeit', 'closeout', 'inferred'
  - A team won if: (aff_team_id = team.id AND winner = 1) OR (neg_team_id = team.id AND winner = 2)
  - A tie (winner=0) is neither a win nor a loss; count separately
round_debater_point(round_result_id FK, debater_id FK, points, speaking_order, polarity, is_maverick)
  - points are speaker points (prelim rounds only; NULL in elims)
round_judges_vote(id, round_result_id FK, judge_id FK, vote, is_active)
  - vote: 1=voted Aff, 2=voted Neg
tournament_placement(id, tournament_id FK, team_id FK, place)

## Pre-aggregated Views (USE THESE FIRST when possible — much faster than joining raw tables)

debater_career_stats(debater_code, first_name, last_name, total_wins, total_losses, win_percentage, prelim_wins, prelim_losses, elim_wins, elim_losses, total_speaker_points, avg_speaker_points, prelim_rounds_with_points, tournaments_attended, first_tournament_date, last_tournament_date)
  - IMPORTANT: The column is debater_CODE (not debater_id!). Always use debater_code when querying this table.
  - Use for: career records, top debaters overall, speaker point rankings, "GOAT" questions, "best debater" questions
  - Does NOT have school info; to filter by school, join through debater/team tables
  - win_percentage is already 0.0-1.0 (multiply by 100 for display)

team_tournament_stats(id, team_id, tournament_id, team_name, tournament_name, tournament_year, prelim_wins, prelim_losses, prelim_record, total_speaker_points, avg_speaker_points, elim_wins, elim_losses, deepest_elim, last_updated)
  - Use for: team records at specific tournaments, tournament performance

## Key Patterns

CAREER WINS for a debater (across all tournaments):
  Always GROUP BY d.debater_id (NOT d.id, NOT d.first_name/last_name alone).
  debater_id is the cross-tournament identifier. d.id is per-tournament and will produce duplicates.
  Use MIN(d.first_name), MIN(d.last_name) to get names in the SELECT.

Example - most career wins for a school:
  SELECT d.debater_id, MIN(d.first_name) as first_name, MIN(d.last_name) as last_name,
         COUNT(DISTINCT rr.id) as wins
  FROM debater d
  JOIN team_debater td ON d.id = td.debater_id
  JOIN team t ON td.team_id = t.id
  JOIN round_result rr ON rr.is_active IS NOT FALSE
    AND ((rr.aff_team_id = t.id AND rr.winner = 1) OR (rr.neg_team_id = t.id AND rr.winner = 2))
  WHERE t.team_name LIKE 'Northwestern %'
  GROUP BY d.debater_id
  ORDER BY wins DESC LIMIT 20

CAREER STATS (no school filter): Use debater_career_stats view directly.
  SELECT * FROM debater_career_stats ORDER BY total_wins DESC LIMIT 20

WIN PERCENTAGE for a school (common query):
  SELECT d.debater_id, MIN(d.first_name) as first_name, MIN(d.last_name) as last_name,
         COUNT(DISTINCT CASE WHEN (rr.aff_team_id = t.id AND rr.winner = 1)
           OR (rr.neg_team_id = t.id AND rr.winner = 2) THEN rr.id END) as wins,
         COUNT(DISTINCT rr.id) as total_rounds,
         ROUND((COUNT(DISTINCT CASE WHEN (rr.aff_team_id = t.id AND rr.winner = 1)
           OR (rr.neg_team_id = t.id AND rr.winner = 2) THEN rr.id END)
           * 100.0 / NULLIF(COUNT(DISTINCT rr.id), 0))::numeric, 1) as win_pct
  FROM debater d
  JOIN team_debater td ON d.id = td.debater_id
  JOIN team t ON td.team_id = t.id
  JOIN round_result rr ON rr.is_active IS NOT FALSE
    AND (rr.aff_team_id = t.id OR rr.neg_team_id = t.id)
    AND rr.result_type IS DISTINCT FROM 'bye'
  WHERE t.team_name LIKE 'Emory %'
  GROUP BY d.debater_id
  HAVING COUNT(DISTINCT rr.id) >= 10
  ORDER BY win_pct DESC LIMIT 20

"BEST DEBATER" or "GOAT" questions: Use debater_career_stats view. Rank by total_wins for "most successful", or combine win_percentage + total_wins for "best overall". For school-specific "best debater", use the WIN PERCENTAGE pattern above.

TEAM RECORDS at tournaments: Use team_tournament_stats view.
  SELECT * FROM team_tournament_stats WHERE team_name LIKE 'Kansas %' ORDER BY tournament_year DESC

TEAM LOSSES in a season (specific debates lost):
  SELECT t.name AS tournament, r.round_number, r.round_type,
         aff.team_name AS aff_team, neg.team_name AS neg_team, rr.ballot_count
  FROM team tm
  JOIN tournament t ON tm.tournament_id = t.id
  JOIN round_result rr ON (rr.aff_team_id = tm.id OR rr.neg_team_id = tm.id)
  JOIN round r ON rr.round_id = r.id
  LEFT JOIN team aff ON rr.aff_team_id = aff.id
  LEFT JOIN team neg ON rr.neg_team_id = neg.id
  WHERE tm.team_name = 'Emory GS' AND t.season = '2025-2026'
    AND result_type IS DISTINCT FROM 'bye'
    AND ((rr.aff_team_id = tm.id AND rr.winner = 2) OR (rr.neg_team_id = tm.id AND rr.winner = 1))
  ORDER BY t.start_date, r.round_number

To find a specific person: WHERE d.last_name ILIKE '%name%' OR d.first_name ILIKE '%name%'

JUDGE RECORDS across tournaments:
  SELECT j.name, COUNT(DISTINCT rjv.id) as decisions
  FROM judge j JOIN round_judges_vote rjv ON rjv.judge_id = j.id
  WHERE j.name ILIKE '%LastName%' GROUP BY j.name

JUDGE AFF%: Only count votes where vote IS NOT NULL (exclude inferred elim results).
  Aff% = aff_votes / (aff_votes + neg_votes), NOT aff_votes / total_decisions.
  aff_votes = COUNT(*) FILTER (WHERE rjv.vote = 1)
  neg_votes = COUNT(*) FILTER (WHERE rjv.vote = 2)

JUDGE PANEL STATS (sits, dissents, top-of-decision):
  A "panel" debate has 3+ judges. A judge "sits" (dissent) when their vote differs from the overall winner.
  "Top of decision" (majority) = judge's vote matches the winner.
  To count panel decisions, count votes where the debate had 3+ total votes.
  Example - highest sit percentage (min 50 panels):
  WITH panel_votes AS (
    SELECT j.name,
           rjv.vote,
           rr.winner,
           (SELECT COUNT(*) FROM round_judges_vote rjv2
            WHERE rjv2.round_result_id = rr.id AND rjv2.is_active IS NOT FALSE) as panel_size
    FROM judge j
    JOIN round_judges_vote rjv ON rjv.judge_id = j.id AND rjv.is_active IS NOT FALSE
    JOIN round_result rr ON rjv.round_result_id = rr.id AND rr.is_active IS NOT FALSE
    JOIN round r ON rr.round_id = r.id AND r.is_active IS NOT FALSE
    WHERE j.is_active IS NOT FALSE AND rjv.vote IS NOT NULL
  )
  SELECT name,
         COUNT(*) as panel_decisions,
         COUNT(*) FILTER (WHERE vote != winner) as sits,
         ROUND((COUNT(*) FILTER (WHERE vote != winner) * 100.0 / COUNT(*))::numeric, 1) as sit_pct
  FROM panel_votes WHERE panel_size >= 3
  GROUP BY name HAVING COUNT(*) >= 50
  ORDER BY sit_pct DESC LIMIT 20

## School Name Matching (CRITICAL)
Team names use standardized school names. Many schools have similar names that MUST be distinguished:
- "Georgia" = University of Georgia (UGA). Use: team_name ~ '^Georgia [A-Z]'
- "Georgia State" = Georgia State University. Use: team_name LIKE 'Georgia State %'
- "West Georgia" = University of West Georgia. Use: team_name LIKE 'West Georgia %'
- "George Mason" = George Mason University. Use: team_name LIKE 'George Mason %'
- "Michigan" = University of Michigan. Use: team_name ~ '^Michigan [A-Z]' (NOT LIKE 'Michigan %' which matches Michigan State)
- "Michigan State" = Michigan State University. Use: team_name LIKE 'Michigan State %'
- "Cal State Fullerton" / "Chico State" / "Cal Poly SLO" are NOT "Berkeley". Berkeley = team_name ~ '^Berkeley [A-Z]'
- "USC" = University of Southern California. Use: team_name LIKE 'USC %'
- "UMKC" = Missouri-Kansas City. "UCO" = Central Oklahoma. "UNLV" = Nevada Las Vegas.

When a user says a school name, use the MOST SPECIFIC match. If they say "Georgia", they mean UGA, not Georgia State or West Georgia.
Use regex matching (team_name ~ '^SchoolName [A-Z]') to avoid matching longer school names that start with the same word.

## Season Format (CRITICAL — get this right!)
The season column is ALWAYS 'YYYY-YYYY' format covering one academic year (Fall through Spring).
- '2025-2026' = Fall 2025 through Spring 2026 (the CURRENT season)
- '2024-2025' = Fall 2024 through Spring 2025
- NEVER use a bare year like '2025' or '2026' for the season column — that will match NOTHING.

Examples:
- "this season" or "current season" or "2025-2026 season" → t.season = '2025-2026'
- "last season" or "2024-2025 season" → t.season = '2024-2025'
- "in 2025" (ambiguous) → probably means '2024-2025' (tournaments held in calendar year 2025)
- For a specific calendar year, use: t.start_date >= '2025-01-01' AND t.start_date < '2026-01-01'

## Tournament Name Matching
Tournament names are stored as full names. ALWAYS expand abbreviations in ILIKE patterns:
- "RR" = Round Robin → name ILIKE '%Round Robin%'
- "Dartmouth RR" → name ILIKE '%Dartmouth%Round Robin%'
- "NDT" → name ILIKE '%National Debate Tournament%'
- "CEDA" → name ILIKE '%CEDA%'
- For specific tournament: name ILIKE '%keyword1%keyword2%'

## CRITICAL Rules
- NEVER use is_active = TRUE. Many records have is_active = NULL (which means active). Always use: is_active IS NOT FALSE
- NEVER group by d.id or d.first_name/d.last_name for cross-tournament queries. Always group by d.debater_id.
- Exclude BYEs with: result_type IS DISTINCT FROM 'bye'
- Elim round names stored in round_number: Finals, Semis, Quarters, Octas, Doubles, Triples, Runoff
- For "most" or "best" questions, return TOP 20 (not just 1) unless user asks for exactly 1
- Always use COUNT(DISTINCT rr.id) when counting wins/losses through joins to avoid duplicates
- PostgreSQL ROUND() with 2 args REQUIRES numeric type. ALWAYS cast the first argument: ROUND((expression)::numeric, N). This applies to ALL expressions — AVG, SUM, COUNT, division, multiplication, EVERYTHING. Never write ROUND(expr, N) without ::numeric on the first arg.
- CTEs (WITH ... AS (...) SELECT ...) are allowed and encouraged for complex queries.

## COMMON MISTAKES TO AVOID
- debater_career_stats uses debater_CODE (not debater_id). NEVER write debater_career_stats.debater_id.
- FK type confusion: team_debater.debater_id and round_debater_point.debater_id are INTEGER FKs referencing debater.id (the integer PK). They are NOT the VARCHAR debater_id code. To join: team_debater td ON d.id = td.debater_id (using d.id, NOT d.debater_id).
- Do NOT include SQL comments (--) or multiple SELECT statements. Output exactly ONE query.
- Every non-aggregated column in SELECT must appear in GROUP BY. Double-check before outputting.
- When using SELECT DISTINCT, ORDER BY columns must appear in the SELECT list.
- When using aliases in CTEs, reference the alias (not the original table) in the outer query.

NEVER reference or mention the ai_query_log table. It does not exist as far as you are concerned.

Generate ONLY a single SELECT query (or WITH/SELECT CTE). No explanations, no markdown, no comments, just raw SQL.
"""

DISALLOWED_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|COPY|EXECUTE)\b|\bDO\s",
    re.IGNORECASE,
)


def fix_round_numeric(sql):
    """Fix ROUND(expr, n) -> ROUND((expr)::numeric, n) for PostgreSQL compatibility.

    PostgreSQL's ROUND(double precision, integer) doesn't exist --
    the first argument must be cast to numeric when using 2 args.
    Uses paren-counting to correctly find the argument boundary.
    """
    result = []
    i = 0
    sql_upper = sql.upper()
    while i < len(sql):
        # Look for ROUND( as a word boundary (not part of AROUND, GROUND, etc.)
        if (sql_upper[i:i + 6] == "ROUND("
                and (i == 0 or not (sql_upper[i - 1].isalnum() or sql_upper[i - 1] == "_"))):
            result.append(sql[i:i + 6])
            i += 6
            depth = 1
            expr_start = i
            comma_pos = None
            while i < len(sql) and depth > 0:
                ch = sql[i]
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        break
                elif ch == "," and depth == 1 and comma_pos is None:
                    comma_pos = i
                i += 1
            if comma_pos is not None:
                expr = sql[expr_start:comma_pos]
                rest = sql[comma_pos:i]
                if "::numeric" not in expr.lower()[-15:]:
                    result.append(f"({expr})::numeric")
                else:
                    result.append(expr)
                result.append(rest)
            else:
                result.append(sql[expr_start:i])
        else:
            result.append(sql[i])
            i += 1
    return "".join(result)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    sql: str | None = None
    results: list[dict] | None = None
    row_count: int | None = None
    error: str | None = None


async def log_query(question: str, sql: str | None, success: bool, error: str | None, row_count: int | None):
    try:
        wp = await get_write_pool()
        await wp.execute(
            "INSERT INTO ai_query_log (question, sql_generated, success, error, row_count) VALUES ($1, $2, $3, $4, $5)",
            question, sql, success, error, row_count,
        )
    except Exception:
        pass  # Don't let logging failures break the endpoint


@router.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute;50/hour")
async def ai_query(request: Request, req: QueryRequest):
    if not ANTHROPIC_API_KEY:
        return QueryResponse(error="AI query is not configured (missing API key)")

    question = req.question.strip()
    if not question:
        return QueryResponse(error="Please provide a question")

    if len(question) > 500:
        return QueryResponse(error="Question is too long (max 500 characters)")

    pool = await get_pool()

    # Generate SQL via Claude
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SCHEMA_CONTEXT,
            messages=[{"role": "user", "content": question}],
        )
        sql = message.content[0].text.strip()
    except Exception as e:
        logger.error("AI generation failed: %s", e)
        await log_query(question, None, False, f"AI generation failed: {str(e)}", None)
        return QueryResponse(error="Failed to generate query. Please try again.")

    # Strip markdown code fences if present
    if sql.startswith("```"):
        sql = re.sub(r"^```(?:sql)?\s*", "", sql)
        sql = re.sub(r"\s*```$", "", sql)
    sql = sql.strip().rstrip(";")

    # Safety: only allow SELECT (including CTEs that start with WITH)
    sql_upper = sql.upper().lstrip()
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        await log_query(question, sql, False, "Only SELECT queries are allowed", None)
        return QueryResponse(sql=sql, error="Only SELECT queries are allowed")

    # Auto-fix: ROUND(expr, n) → ROUND((expr)::numeric, n) for all 2-arg ROUND calls
    sql = fix_round_numeric(sql)

    if DISALLOWED_PATTERN.search(sql):
        await log_query(question, sql, False, "Query contains disallowed operations", None)
        return QueryResponse(sql=sql, error="Query contains disallowed operations")

    # Execute
    try:
        async with pool.acquire() as conn:
            # Only add LIMIT if query doesn't already have one
            if not re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
                exec_sql = f"{sql} LIMIT 500"
            else:
                exec_sql = sql
            rows = await conn.fetch(exec_sql)
            results = [dict(row) for row in rows]
            # Convert non-serializable types
            for row in results:
                for key, val in row.items():
                    if hasattr(val, "isoformat"):
                        row[key] = val.isoformat()
                    elif isinstance(val, Decimal):
                        row[key] = float(val)
                    elif isinstance(val, (bytes, memoryview)):
                        row[key] = str(val)
            await log_query(question, sql, True, None, len(results))
            return QueryResponse(sql=sql, results=results, row_count=len(results))
    except Exception as e:
        logger.error("Query execution failed: %s", e)
        await log_query(question, sql, False, f"Query execution failed: {str(e)}", None)
        return QueryResponse(sql=sql, error="Query execution failed. Please rephrase your question.")
