SEARCH_JUDGES = """
    SELECT
        j.name,
        COUNT(DISTINCT t.id) as tournaments,
        COUNT(rjv.id) as total_decisions,
        COUNT(rjv.id) FILTER (WHERE rjv.vote = 1) as aff_votes,
        COUNT(rjv.id) FILTER (WHERE rjv.vote = 2) as neg_votes,
        MIN(t.start_date) as first_seen,
        MAX(t.start_date) as last_seen
    FROM judge j
    JOIN round_judges_vote rjv ON rjv.judge_id = j.id AND rjv.is_active IS NOT FALSE
    JOIN round_result rr ON rjv.round_result_id = rr.id AND rr.is_active IS NOT FALSE
    JOIN round r ON rr.round_id = r.id AND r.is_active IS NOT FALSE
    JOIN tournament t ON r.tournament_id = t.id
    WHERE j.is_active IS NOT FALSE
      AND LOWER(j.name) LIKE LOWER($1)
    GROUP BY j.name
    ORDER BY COUNT(rjv.id) DESC
    LIMIT 50
"""

JUDGE_CAREER = """
    SELECT
        j.name,
        COUNT(DISTINCT t.id) as tournaments,
        COUNT(rjv.id) as total_decisions,
        COUNT(rjv.id) FILTER (WHERE rjv.vote = 1) as aff_votes,
        COUNT(rjv.id) FILTER (WHERE rjv.vote = 2) as neg_votes,
        MIN(t.start_date) as first_seen,
        MAX(t.start_date) as last_seen
    FROM judge j
    JOIN round_judges_vote rjv ON rjv.judge_id = j.id AND rjv.is_active IS NOT FALSE
    JOIN round_result rr ON rjv.round_result_id = rr.id AND rr.is_active IS NOT FALSE
    JOIN round r ON rr.round_id = r.id AND r.is_active IS NOT FALSE
    JOIN tournament t ON r.tournament_id = t.id
    WHERE j.is_active IS NOT FALSE
      AND j.name = $1
    GROUP BY j.name
"""

JUDGE_SEASON_SUMMARY = """
    SELECT
        t.season,
        COUNT(DISTINCT t.id) as tournaments,
        COUNT(rjv.id) as decisions,
        COUNT(rjv.id) FILTER (WHERE rjv.vote = 1) as aff_votes,
        COUNT(rjv.id) FILTER (WHERE rjv.vote = 2) as neg_votes,
        COUNT(rjv.id) FILTER (WHERE r.round_type = 'elim') as elim_decisions
    FROM judge j
    JOIN round_judges_vote rjv ON rjv.judge_id = j.id AND rjv.is_active IS NOT FALSE
    JOIN round_result rr ON rjv.round_result_id = rr.id AND rr.is_active IS NOT FALSE
    JOIN round r ON rr.round_id = r.id AND r.is_active IS NOT FALSE
    JOIN tournament t ON r.tournament_id = t.id
    WHERE j.is_active IS NOT FALSE
      AND j.name = $1
    GROUP BY t.season
    ORDER BY MIN(t.start_date)
"""

JUDGE_TOURNAMENT_LIST = """
    SELECT
        t.id as tournament_id,
        t.name as tournament_name,
        t.season,
        t.start_date,
        COUNT(rjv.id) as decisions,
        COUNT(rjv.id) FILTER (WHERE rjv.vote = 1) as aff_votes,
        COUNT(rjv.id) FILTER (WHERE rjv.vote = 2) as neg_votes,
        COUNT(rjv.id) FILTER (WHERE r.round_type = 'elim') as elim_decisions
    FROM judge j
    JOIN round_judges_vote rjv ON rjv.judge_id = j.id AND rjv.is_active IS NOT FALSE
    JOIN round_result rr ON rjv.round_result_id = rr.id AND rr.is_active IS NOT FALSE
    JOIN round r ON rr.round_id = r.id AND r.is_active IS NOT FALSE
    JOIN tournament t ON r.tournament_id = t.id
    WHERE j.is_active IS NOT FALSE
      AND j.name = $1
    GROUP BY t.id, t.name, t.season, t.start_date
    ORDER BY t.start_date DESC
"""

JUDGE_TOURNAMENT_ROUNDS = """
    SELECT
        r.round_number as round,
        r.round_type,
        aff_tm.team_name as aff_team,
        neg_tm.team_name as neg_team,
        rjv.vote as judge_vote,
        rr.winner,
        CASE
            WHEN rr.result_type = 'bye' THEN 'BYE'
            WHEN rr.result_type = 'forfeit' THEN 'FFT'
            WHEN rr.winner = -1 THEN 'CLOSEOUT'
            WHEN rr.winner = 1 THEN 'AFF'
            WHEN rr.winner = 2 THEN 'NEG'
            ELSE ''
        END as decision,
        rr.ballot_count,
        CASE WHEN rjv.vote != rr.winner AND rr.winner > 0 THEN true ELSE false END as dissent
    FROM judge j
    JOIN round_judges_vote rjv ON rjv.judge_id = j.id AND rjv.is_active IS NOT FALSE
    JOIN round_result rr ON rjv.round_result_id = rr.id AND rr.is_active IS NOT FALSE
    JOIN round r ON rr.round_id = r.id AND r.is_active IS NOT FALSE
    LEFT JOIN team aff_tm ON rr.aff_team_id = aff_tm.id
    LEFT JOIN team neg_tm ON rr.neg_team_id = neg_tm.id
    WHERE j.is_active IS NOT FALSE
      AND j.name = $1
      AND r.tournament_id = $2
    ORDER BY CASE WHEN r.round_type = 'prelim' THEN 0 ELSE 1 END,
             CASE WHEN REGEXP_REPLACE(r.round_number, '[^0-9]', '', 'g') = '' THEN 0
                  ELSE CAST(REGEXP_REPLACE(r.round_number, '[^0-9]', '', 'g') AS INTEGER) END,
             CASE
                 WHEN LOWER(r.round_number) LIKE '%runoff%' THEN 1
                 WHEN LOWER(r.round_number) LIKE '%triple%' THEN 2
                 WHEN LOWER(r.round_number) LIKE '%double%' THEN 3
                 WHEN LOWER(r.round_number) LIKE '%octa%' OR LOWER(r.round_number) LIKE '%octo%' THEN 4
                 WHEN LOWER(r.round_number) LIKE '%quarter%' THEN 5
                 WHEN LOWER(r.round_number) LIKE '%semi%' THEN 6
                 WHEN LOWER(r.round_number) LIKE '%final%' THEN 7
                 ELSE 0
             END
"""
