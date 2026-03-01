import re
import anthropic
from fastapi import APIRouter
from pydantic import BaseModel

from ..config import ANTHROPIC_API_KEY
from ..database import get_pool

router = APIRouter(prefix="/ai", tags=["ai"])

SCHEMA_CONTEXT = """
You are a SQL query generator for a college policy debate database (PostgreSQL).

## Tables

tournament(id, name, season, start_date, end_date, is_active, year)
round(id, tournament_id FK, round_number, round_type ['prelim'/'elim'], source, is_active)
team(id, tournament_id FK, team_name, is_active)
debater(id, debater_id, first_name, last_name, tournament_id FK, is_active)
  - debater_id is a code like 'JSMITH' (first initial + last name)
  - Same person across tournaments shares debater_id + first_name + last_name
judge(id, name, tournament_id FK, is_active)
team_debater(team_id FK, debater_id FK)
round_result(id, round_id FK, aff_team_id FK, neg_team_id FK, winner, ballot_count, result_type, is_active)
  - winner: 1=Aff won, 2=Neg won, -1=Closeout
  - result_type: NULL=normal, 'bye', 'forfeit', 'closeout', 'inferred'
round_debater_point(round_result_id FK, debater_id FK, points, speaking_order, polarity, is_maverick)
  - polarity: 1=Aff, 2=Neg
  - points are speaker points (prelim rounds only; NULL in elims)
round_judges_vote(id, round_result_id FK, judge_id FK, vote, is_active)
  - vote: 1=Aff, 2=Neg
known_data_issues(id, round_result_id, issue_type, notes, year, created_at)
tournament_placement(id, tournament_id FK, team_id FK, place)

## Useful Views (prefer these for aggregate queries)

debater_career_stats - pre-aggregated career stats per debater
team_tournament_stats - team stats per tournament

## Elim round names (round_number values for elims)
Finals, Semis, Quarters, Octas, Doubles, Triples, Runoff

## Rules
- Team names: "School XY" where XY are alphabetically sorted initials
- Seasons span two academic years (e.g., season '2024' = Fall 2024 + Spring 2025)
- Filter is_active = TRUE for current/valid records
- Use ILIKE for case-insensitive text search

Generate ONLY a single SELECT query. No explanations, no markdown, just the raw SQL.
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


@router.post("/query", response_model=QueryResponse)
async def ai_query(req: QueryRequest):
    if not ANTHROPIC_API_KEY:
        return QueryResponse(error="AI query is not configured (missing API key)")

    question = req.question.strip()
    if not question:
        return QueryResponse(error="Please provide a question")

    # Generate SQL via Claude Haiku
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SCHEMA_CONTEXT,
            messages=[{"role": "user", "content": question}],
        )
        sql = message.content[0].text.strip()
    except Exception as e:
        return QueryResponse(error=f"AI generation failed: {str(e)}")

    # Strip markdown code fences if present
    if sql.startswith("```"):
        sql = re.sub(r"^```(?:sql)?\s*", "", sql)
        sql = re.sub(r"\s*```$", "", sql)
    sql = sql.strip().rstrip(";")

    # Safety: only allow SELECT
    if not sql.upper().startswith("SELECT"):
        return QueryResponse(sql=sql, error="Only SELECT queries are allowed")

    if DISALLOWED_PATTERN.search(sql):
        return QueryResponse(sql=sql, error="Query contains disallowed operations")

    # Execute
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Only add LIMIT if query doesn't already have one
            if not re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
                exec_sql = f"{sql} LIMIT 100"
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
            return QueryResponse(sql=sql, results=results, row_count=len(results))
    except Exception as e:
        return QueryResponse(sql=sql, error=f"Query execution failed: {str(e)}")
