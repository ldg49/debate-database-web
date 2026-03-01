from fastapi import APIRouter, Query
from ..database import get_pool
from ..queries import data_gaps_queries as q

router = APIRouter(tags=["data-gaps"])


@router.get("/data-gaps")
async def get_data_gaps(season: str = Query(None)):
    pool = await get_pool()
    if season:
        rows = await pool.fetch(q.TOURNAMENT_GAPS_BY_SEASON, season)
    else:
        rows = await pool.fetch(q.TOURNAMENT_GAPS)

    # Build lookup of issue notes per tournament
    issue_rows = await pool.fetch(q.KNOWN_ISSUE_NOTES)
    issue_notes: dict[int, list[str]] = {}
    for ir in issue_rows:
        tid = ir["tournament_id"]
        issue_notes.setdefault(tid, []).append(ir["notes"])

    tournaments = []
    summary = {
        "no_results": 0,
        "missing_elims": 0,
        "missing_prelims": 0,
        "missing_speaker_points": 0,
        "missing_names": 0,
        "known_issues": 0,
    }

    # Tournament types that legitimately have no elim rounds
    ELIMS_NOT_EXPECTED_TYPES = ("qualifier", "round_robin", "prelims_only")
    ELIMS_NOT_EXPECTED_NAMES = ("qualifier", "round robin")

    for row in rows:
        total = row["total_debates"]
        prelim = row["prelim_debates"]
        elim = row["elim_debates"]
        prelim_with_sp = row["prelim_with_sp"]
        missing_names = row["missing_names"]
        total_debaters = row["total_debaters"]
        known_issues = row["known_issues"]
        name_lower = row["name"].lower()
        t_type = (row["tournament_type"] or "").lower()

        gaps = []

        if total == 0:
            gaps.append("no_results")
            summary["no_results"] += 1
        else:
            elims_not_expected = (
                t_type in ELIMS_NOT_EXPECTED_TYPES
                or any(kw in name_lower for kw in ELIMS_NOT_EXPECTED_NAMES)
            )
            if prelim > 0 and elim == 0 and not elims_not_expected:
                gaps.append("missing_elims")
                summary["missing_elims"] += 1
            if elim > 0 and prelim == 0:
                gaps.append("missing_prelims")
                summary["missing_prelims"] += 1
            if prelim > 0 and prelim_with_sp < prelim:
                sp_ratio = prelim_with_sp / prelim
                if sp_ratio < 0.5:
                    gaps.append("missing_speaker_points")
                    summary["missing_speaker_points"] += 1

        if missing_names > 0:
            gaps.append("missing_names")
            summary["missing_names"] += 1

        if known_issues > 0:
            gaps.append("known_issues")
            summary["known_issues"] += 1

        if not gaps:
            continue

        sp_pct = round(prelim_with_sp / prelim * 100, 1) if prelim > 0 else None
        name_pct = (
            round((total_debaters - missing_names) / total_debaters * 100, 1)
            if total_debaters > 0
            else None
        )

        tournaments.append(
            {
                "id": row["id"],
                "name": row["name"],
                "season": row["season"],
                "start_date": str(row["start_date"]) if row["start_date"] else None,
                "total_debates": total,
                "prelim_debates": prelim,
                "elim_debates": elim,
                "sp_coverage_pct": sp_pct,
                "missing_names": missing_names,
                "total_debaters": total_debaters,
                "name_coverage_pct": name_pct,
                "known_issues": known_issues,
                "issue_notes": issue_notes.get(row["id"], []),
                "gaps": gaps,
            }
        )

    return {"tournaments": tournaments, "summary": summary}
