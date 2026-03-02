TOURNAMENT_GAPS = """
WITH debate_counts AS (
    SELECT
        r.tournament_id,
        COUNT(rr.id) AS total_debates,
        COUNT(rr.id) FILTER (WHERE r.round_type = 'prelim') AS prelim_debates,
        COUNT(rr.id) FILTER (WHERE r.round_type = 'elim') AS elim_debates
    FROM round r
    JOIN round_result rr ON rr.round_id = r.id
    WHERE rr.result_type IS DISTINCT FROM 'bye'
      AND rr.result_type IS DISTINCT FROM 'forfeit'
    GROUP BY r.tournament_id
),
sp_coverage AS (
    SELECT
        r.tournament_id,
        COUNT(DISTINCT rr.id) AS prelim_with_sp
    FROM round r
    JOIN round_result rr ON rr.round_id = r.id
    JOIN round_debater_point rdp ON rdp.round_result_id = rr.id
    WHERE r.round_type = 'prelim'
      AND rdp.points IS NOT NULL
      AND rr.result_type IS DISTINCT FROM 'bye'
      AND rr.result_type IS DISTINCT FROM 'forfeit'
    GROUP BY r.tournament_id
),
debater_names AS (
    SELECT
        d.tournament_id,
        COUNT(*) AS total_debaters,
        COUNT(*) FILTER (
            WHERE d.first_name IS NULL OR d.first_name = ''
               OR d.last_name IS NULL OR d.last_name = ''
        ) AS missing_names
    FROM debater d
    GROUP BY d.tournament_id
),
known_issues AS (
    SELECT
        r.tournament_id,
        COUNT(ki.id) AS issue_count
    FROM known_data_issues ki
    JOIN round_result rr ON rr.id = ki.round_result_id
    JOIN round r ON r.id = rr.round_id
    GROUP BY r.tournament_id
)
SELECT
    t.id,
    t.name,
    t.season,
    t.start_date,
    COALESCE(dc.total_debates, 0) AS total_debates,
    COALESCE(dc.prelim_debates, 0) AS prelim_debates,
    COALESCE(dc.elim_debates, 0) AS elim_debates,
    COALESCE(sp.prelim_with_sp, 0) AS prelim_with_sp,
    COALESCE(dn.total_debaters, 0) AS total_debaters,
    COALESCE(dn.missing_names, 0) AS missing_names,
    COALESCE(ki.issue_count, 0) AS known_issues,
    t.tournament_type
FROM tournament t
LEFT JOIN debate_counts dc ON dc.tournament_id = t.id
LEFT JOIN sp_coverage sp ON sp.tournament_id = t.id
LEFT JOIN debater_names dn ON dn.tournament_id = t.id
LEFT JOIN known_issues ki ON ki.tournament_id = t.id
WHERE t.is_active IS NOT FALSE
  AND (t.data_gaps_reviewed IS NOT TRUE)
ORDER BY t.start_date DESC, t.name
"""

KNOWN_ISSUE_NOTES = """
SELECT
    r.tournament_id,
    ki.issue_type,
    ki.notes
FROM known_data_issues ki
JOIN round_result rr ON rr.id = ki.round_result_id
JOIN round r ON r.id = rr.round_id
ORDER BY r.tournament_id, ki.id
"""

TOURNAMENT_GAPS_BY_SEASON = """
WITH debate_counts AS (
    SELECT
        r.tournament_id,
        COUNT(rr.id) AS total_debates,
        COUNT(rr.id) FILTER (WHERE r.round_type = 'prelim') AS prelim_debates,
        COUNT(rr.id) FILTER (WHERE r.round_type = 'elim') AS elim_debates
    FROM round r
    JOIN round_result rr ON rr.round_id = r.id
    WHERE rr.result_type IS DISTINCT FROM 'bye'
      AND rr.result_type IS DISTINCT FROM 'forfeit'
    GROUP BY r.tournament_id
),
sp_coverage AS (
    SELECT
        r.tournament_id,
        COUNT(DISTINCT rr.id) AS prelim_with_sp
    FROM round r
    JOIN round_result rr ON rr.round_id = r.id
    JOIN round_debater_point rdp ON rdp.round_result_id = rr.id
    WHERE r.round_type = 'prelim'
      AND rdp.points IS NOT NULL
      AND rr.result_type IS DISTINCT FROM 'bye'
      AND rr.result_type IS DISTINCT FROM 'forfeit'
    GROUP BY r.tournament_id
),
debater_names AS (
    SELECT
        d.tournament_id,
        COUNT(*) AS total_debaters,
        COUNT(*) FILTER (
            WHERE d.first_name IS NULL OR d.first_name = ''
               OR d.last_name IS NULL OR d.last_name = ''
        ) AS missing_names
    FROM debater d
    GROUP BY d.tournament_id
),
known_issues AS (
    SELECT
        r.tournament_id,
        COUNT(ki.id) AS issue_count
    FROM known_data_issues ki
    JOIN round_result rr ON rr.id = ki.round_result_id
    JOIN round r ON r.id = rr.round_id
    GROUP BY r.tournament_id
)
SELECT
    t.id,
    t.name,
    t.season,
    t.start_date,
    COALESCE(dc.total_debates, 0) AS total_debates,
    COALESCE(dc.prelim_debates, 0) AS prelim_debates,
    COALESCE(dc.elim_debates, 0) AS elim_debates,
    COALESCE(sp.prelim_with_sp, 0) AS prelim_with_sp,
    COALESCE(dn.total_debaters, 0) AS total_debaters,
    COALESCE(dn.missing_names, 0) AS missing_names,
    COALESCE(ki.issue_count, 0) AS known_issues,
    t.tournament_type
FROM tournament t
LEFT JOIN debate_counts dc ON dc.tournament_id = t.id
LEFT JOIN sp_coverage sp ON sp.tournament_id = t.id
LEFT JOIN debater_names dn ON dn.tournament_id = t.id
LEFT JOIN known_issues ki ON ki.tournament_id = t.id
WHERE t.is_active IS NOT FALSE
  AND (t.data_gaps_reviewed IS NOT TRUE)
  AND t.season = $1
ORDER BY t.start_date DESC, t.name
"""
