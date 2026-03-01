SEARCH_DEBATERS = """
    SELECT debater_code, first_name, last_name, total_wins, total_losses,
           win_percentage, avg_speaker_points, tournaments_attended
    FROM debater_career_stats
    WHERE total_wins + total_losses > 0
      AND (LOWER(last_name) LIKE LOWER($1)
           OR LOWER(first_name) LIKE LOWER($1)
           OR LOWER(debater_code) LIKE LOWER($1)
           OR LOWER(first_name || ' ' || last_name) LIKE LOWER($1)
           OR LOWER(last_name || ', ' || first_name) LIKE LOWER($1))
    ORDER BY last_name, first_name
    LIMIT 50
"""

ALL_DEBATERS = """
    SELECT debater_code, first_name, last_name, total_wins, total_losses,
           win_percentage, avg_speaker_points, tournaments_attended
    FROM debater_career_stats
    WHERE total_wins + total_losses > 0
    ORDER BY last_name, first_name
"""

CAREER_STATS = """
    SELECT debater_code, first_name, last_name, total_wins, total_losses,
           win_percentage, avg_speaker_points, tournaments_attended
    FROM debater_career_stats
    WHERE debater_code = $1
"""

SEASON_SUMMARY = """
    SELECT
        t.season,
        REGEXP_REPLACE(tm.team_name, '\s+\S+$', '') as school,
        string_agg(DISTINCT
            CASE WHEN d2.debater_id != $1
                 THEN TRIM(COALESCE(d2.first_name, '') || ' ' || COALESCE(d2.last_name, d2.debater_id))
            END, ', '
        ) as partners,
        COUNT(DISTINCT rr.id) FILTER (WHERE
            (rr.aff_team_id = tm.id AND rr.winner = 1) OR
            (rr.neg_team_id = tm.id AND rr.winner = 2)
        ) as wins,
        COUNT(DISTINCT rr.id) FILTER (WHERE
            (rr.aff_team_id = tm.id AND rr.winner = 2) OR
            (rr.neg_team_id = tm.id AND rr.winner = 1)
        ) as losses,
        ROUND(AVG(rdp.points)::numeric, 1) as avg_sp
    FROM debater d
    JOIN team_debater td ON d.id = td.debater_id
    JOIN team tm ON td.team_id = tm.id
    JOIN round_result rr ON (rr.aff_team_id = tm.id OR rr.neg_team_id = tm.id)
        AND rr.is_active IS NOT FALSE
    JOIN round r ON rr.round_id = r.id AND r.is_active IS NOT FALSE
    JOIN tournament t ON r.tournament_id = t.id AND tm.tournament_id = t.id
    LEFT JOIN team_debater td2 ON td2.team_id = tm.id AND td2.debater_id != d.id
    LEFT JOIN debater d2 ON td2.debater_id = d2.id
    LEFT JOIN round_debater_point rdp ON rdp.round_result_id = rr.id AND rdp.debater_id = d.id
    WHERE d.debater_id = $1 AND d.is_active IS NOT FALSE
    GROUP BY t.season, REGEXP_REPLACE(tm.team_name, '\s+\S+$', '')
    ORDER BY MIN(t.start_date)
"""

PARTNER_HISTORY = """
    SELECT
        d2.debater_id as partner_code,
        TRIM(COALESCE(d2.first_name, '') || ' ' || COALESCE(d2.last_name, d2.debater_id)) as partner_name,
        REGEXP_REPLACE(tm.team_name, '\s+\S+$', '') as school,
        COUNT(*) FILTER (WHERE
            (rr.aff_team_id = tm.id AND rr.winner = 1) OR
            (rr.neg_team_id = tm.id AND rr.winner = 2)
        ) as wins,
        COUNT(*) FILTER (WHERE
            (rr.aff_team_id = tm.id AND rr.winner = 2) OR
            (rr.neg_team_id = tm.id AND rr.winner = 1)
        ) as losses,
        COUNT(DISTINCT t.id) as tournaments
    FROM debater d
    JOIN team_debater td ON d.id = td.debater_id
    JOIN team tm ON td.team_id = tm.id
    JOIN team_debater td2 ON td2.team_id = tm.id AND td2.debater_id != d.id
    JOIN debater d2 ON td2.debater_id = d2.id
    JOIN round_result rr ON (rr.aff_team_id = tm.id OR rr.neg_team_id = tm.id)
        AND rr.is_active IS NOT FALSE
    JOIN round r ON rr.round_id = r.id AND r.is_active IS NOT FALSE
    JOIN tournament t ON r.tournament_id = t.id AND tm.tournament_id = t.id
    WHERE d.debater_id = $1 AND d.is_active IS NOT FALSE
    GROUP BY d2.debater_id, d2.first_name, d2.last_name, REGEXP_REPLACE(tm.team_name, '\s+\S+$', '')
    ORDER BY COUNT(*) DESC
"""

TOURNAMENT_LIST = """
    SELECT
        t.id as tournament_id,
        t.name as tournament_name,
        t.season,
        t.start_date,
        tm.team_name,
        COUNT(DISTINCT rr.id) FILTER (WHERE
            r.round_type = 'prelim' AND (
            (rr.aff_team_id = tm.id AND rr.winner = 1) OR
            (rr.neg_team_id = tm.id AND rr.winner = 2))
        ) as wins,
        COUNT(DISTINCT rr.id) FILTER (WHERE
            r.round_type = 'prelim' AND (
            (rr.aff_team_id = tm.id AND rr.winner = 2) OR
            (rr.neg_team_id = tm.id AND rr.winner = 1))
        ) as losses,
        ROUND(AVG(rdp.points)::numeric, 1) as avg_sp,
        MAX(CASE
            WHEN r.round_type = 'elim' THEN
                CASE
                    WHEN LOWER(r.round_number) LIKE '%final%' AND LOWER(r.round_number) NOT LIKE '%semi%' THEN 'Finals'
                    WHEN LOWER(r.round_number) LIKE '%semi%' THEN 'Semis'
                    WHEN LOWER(r.round_number) LIKE '%quarter%' THEN 'Quarters'
                    WHEN LOWER(r.round_number) LIKE '%octa%' OR LOWER(r.round_number) LIKE '%octo%' THEN 'Octas'
                    WHEN LOWER(r.round_number) LIKE '%double%' THEN 'Doubles'
                    WHEN LOWER(r.round_number) LIKE '%triple%' THEN 'Triples'
                    WHEN LOWER(r.round_number) LIKE '%runoff%' THEN 'Runoff'
                    ELSE r.round_number
                END
            ELSE NULL
        END) as elim_result
    FROM debater d
    JOIN team_debater td ON d.id = td.debater_id
    JOIN team tm ON td.team_id = tm.id
    JOIN round_result rr ON (rr.aff_team_id = tm.id OR rr.neg_team_id = tm.id)
        AND rr.is_active IS NOT FALSE
    JOIN round r ON rr.round_id = r.id AND r.is_active IS NOT FALSE
    JOIN tournament t ON r.tournament_id = t.id AND tm.tournament_id = t.id
    LEFT JOIN round_debater_point rdp ON rdp.round_result_id = rr.id AND rdp.debater_id = d.id
        AND r.round_type = 'prelim'
    WHERE d.debater_id = $1 AND d.is_active IS NOT FALSE
    GROUP BY t.id, t.name, t.season, t.start_date, tm.team_name
    ORDER BY t.start_date ASC
"""

TOURNAMENT_ROUNDS = """
    SELECT
        r.round_number as round,
        r.round_type,
        CASE WHEN rr.aff_team_id = tm.id THEN 'Aff' ELSE 'Neg' END as side,
        CASE WHEN rr.aff_team_id = tm.id THEN neg_tm.team_name ELSE aff_tm.team_name END as opponent,
        (SELECT string_agg(
             CASE WHEN rjv.vote != rr.winner THEN j.name || '*' ELSE j.name END,
             ', ')
         FROM round_judges_vote rjv JOIN judge j ON rjv.judge_id = j.id
         WHERE rjv.round_result_id = rr.id) as judge,
        CASE
            WHEN rr.result_type = 'bye' THEN 'BYE'
            WHEN rr.result_type = 'forfeit' THEN 'FFT'
            WHEN rr.winner = -1 THEN 'BYE'
            WHEN (rr.aff_team_id = tm.id AND rr.winner = 1) OR (rr.neg_team_id = tm.id AND rr.winner = 2) THEN 'W'
            ELSE 'L'
        END as result,
        rr.ballot_count,
        rdp.points as speaker_points
    FROM debater d
    JOIN team_debater td ON d.id = td.debater_id
    JOIN team tm ON td.team_id = tm.id
    JOIN round_result rr ON (rr.aff_team_id = tm.id OR rr.neg_team_id = tm.id)
        AND rr.is_active IS NOT FALSE
    JOIN round r ON rr.round_id = r.id AND r.is_active IS NOT FALSE
        AND r.tournament_id = $2
    LEFT JOIN team aff_tm ON rr.aff_team_id = aff_tm.id
    LEFT JOIN team neg_tm ON rr.neg_team_id = neg_tm.id
    LEFT JOIN (
        SELECT round_result_id, debater_id,
               ROUND(AVG(points)::numeric, 1) as points
        FROM round_debater_point
        GROUP BY round_result_id, debater_id
    ) rdp ON rdp.round_result_id = rr.id AND rdp.debater_id = d.id
    WHERE d.debater_id = $1 AND d.is_active IS NOT FALSE
        AND tm.tournament_id = $2
    ORDER BY CASE WHEN r.round_type = 'prelim' THEN 0 ELSE 1 END,
             CASE
                 WHEN r.round_type = 'prelim' THEN
                     CASE WHEN REGEXP_REPLACE(r.round_number, '[^0-9]', '', 'g') = '' THEN 0
                          ELSE CAST(REGEXP_REPLACE(r.round_number, '[^0-9]', '', 'g') AS INTEGER)
                     END
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
