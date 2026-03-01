import re
import anthropic
from fastapi import APIRouter
from pydantic import BaseModel

from ..config import ANTHROPIC_API_KEY
from ..database import get_pool

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
  - winner: 1=Aff won, 2=Neg won, -1=Closeout (same school)
  - result_type: NULL=normal, 'bye', 'forfeit', 'closeout', 'inferred'
  - A team won if: (aff_team_id = team.id AND winner = 1) OR (neg_team_id = team.id AND winner = 2)
round_debater_point(round_result_id FK, debater_id FK, points, speaking_order, polarity, is_maverick)
  - points are speaker points (prelim rounds only; NULL in elims)
round_judges_vote(id, round_result_id FK, judge_id FK, vote, is_active)
  - vote: 1=voted Aff, 2=voted Neg
tournament_placement(id, tournament_id FK, team_id FK, place)

## Pre-aggregated Views

debater_career_stats(debater_code, first_name, last_name, total_wins, total_losses, win_percentage, prelim_wins, prelim_losses, elim_wins, elim_losses, total_speaker_points, avg_speaker_points, prelim_rounds_with_points, tournaments_attended, first_tournament_date, last_tournament_date)
  - Use for: career records, top debaters overall, speaker point rankings
  - Does NOT have school info; to filter by school, join through debater/team tables

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

TEAM RECORDS at tournaments: Use team_tournament_stats view.
  SELECT * FROM team_tournament_stats WHERE team_name LIKE 'Kansas %' ORDER BY tournament_year DESC

To find a specific person: WHERE d.last_name ILIKE '%name%' OR d.first_name ILIKE '%name%'

JUDGE RECORDS across tournaments:
  SELECT j.name, COUNT(DISTINCT rjv.id) as decisions
  FROM judge j JOIN round_judges_vote rjv ON rjv.judge_id = j.id
  WHERE j.name ILIKE '%LastName%' GROUP BY j.name

## School Name Matching (CRITICAL)
Team names use standardized school names. Many schools have similar names that MUST be distinguished:
- "Georgia" = University of Georgia (UGA). Use: team_name LIKE 'Georgia __' (2-char initials) OR use regex: team_name ~ '^Georgia [A-Z]{2,4}$'
- "Georgia State" = Georgia State University. Use: team_name LIKE 'Georgia State %'
- "West Georgia" = University of West Georgia. Use: team_name LIKE 'West Georgia %'
- "George Mason" = George Mason University. Use: team_name LIKE 'George Mason %'
- "Michigan" = University of Michigan. Use: team_name LIKE 'Michigan __' OR regex: team_name ~ '^Michigan [A-Z]{2,4}$'
- "Michigan State" = Michigan State University. Use: team_name LIKE 'Michigan State %'
- "Cal State Fullerton" / "Chico State" / "Cal Poly SLO" are NOT "Berkeley". Berkeley = team_name ~ '^Berkeley [A-Z]{2,4}$'
- "USC" = University of Southern California. Use: team_name LIKE 'USC %'
- "UMKC" = Missouri-Kansas City. "UCO" = Central Oklahoma. "UNLV" = Nevada Las Vegas.

When a user says a school name, use the MOST SPECIFIC match. If they say "Georgia", they mean UGA, not Georgia State or West Georgia.
Use regex matching (team_name ~ '^SchoolName [A-Z]{2,4}$') to avoid matching longer school names that start with the same word.

## CRITICAL Rules
- NEVER use is_active = TRUE. Many records have is_active = NULL (which means active). Always use: is_active IS NOT FALSE
- NEVER group by d.id or d.first_name/d.last_name for cross-tournament queries. Always group by d.debater_id.
- Exclude BYEs with: result_type IS DISTINCT FROM 'bye'
- Elim round names stored in round_number: Finals, Semis, Quarters, Octas, Doubles, Triples, Runoff
- Seasons span two academic years (season '2024' = Fall 2024 + Spring 2025)
- For "most" or "best" questions, return TOP 20 (not just 1) unless user asks for exactly 1
- Always use COUNT(DISTINCT rr.id) when counting wins/losses through joins to avoid duplicates
- PostgreSQL ROUND() requires numeric type: use ROUND(AVG(rdp.points)::numeric, 2), NOT ROUND(AVG(rdp.points), 2)
- Tournament name matching: "Dartmouth RR" = name ILIKE '%Dartmouth%Round Robin%', "NDT" = name ILIKE '%National Debate Tournament%'

NEVER reference or mention the ai_query_log table. It does not exist as far as you are concerned.

Generate ONLY a single SELECT query. No explanations, no markdown, just raw SQL.
"""

DISALLOWED_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|COPY|EXECUTE|DO\s)\b",
    re.IGNORECASE,
)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    sql: str | None = None
    results: list[dict] | None = None
    row_count: int | None = None
    error: str | None = None


async def log_query(pool, question: str, sql: str | None, success: bool, error: str | None, row_count: int | None):
    try:
        await pool.execute(
            "INSERT INTO ai_query_log (question, sql_generated, success, error, row_count) VALUES ($1, $2, $3, $4, $5)",
            question, sql, success, error, row_count,
        )
    except Exception:
        pass  # Don't let logging failures break the endpoint


@router.post("/query", response_model=QueryResponse)
async def ai_query(req: QueryRequest):
    if not ANTHROPIC_API_KEY:
        return QueryResponse(error="AI query is not configured (missing API key)")

    question = req.question.strip()
    if not question:
        return QueryResponse(error="Please provide a question")

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
        await log_query(pool, question, None, False, f"AI generation failed: {str(e)}", None)
        return QueryResponse(error=f"AI generation failed: {str(e)}")

    # Strip markdown code fences if present
    if sql.startswith("```"):
        sql = re.sub(r"^```(?:sql)?\s*", "", sql)
        sql = re.sub(r"\s*```$", "", sql)
    sql = sql.strip().rstrip(";")

    # Safety: only allow SELECT
    if not sql.upper().startswith("SELECT"):
        await log_query(pool, question, sql, False, "Only SELECT queries are allowed", None)
        return QueryResponse(sql=sql, error="Only SELECT queries are allowed")

    if DISALLOWED_PATTERN.search(sql):
        await log_query(pool, question, sql, False, "Query contains disallowed operations", None)
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
                    elif isinstance(val, (bytes, memoryview)):
                        row[key] = str(val)
            await log_query(pool, question, sql, True, None, len(results))
            return QueryResponse(sql=sql, results=results, row_count=len(results))
    except Exception as e:
        await log_query(pool, question, sql, False, f"Query execution failed: {str(e)}", None)
        return QueryResponse(sql=sql, error=f"Query execution failed: {str(e)}")
