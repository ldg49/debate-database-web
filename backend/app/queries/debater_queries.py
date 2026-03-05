SEARCH_DEBATERS = """
    SELECT dcs.debater_code, dcs.first_name, dcs.last_name, dcs.total_wins, dcs.total_losses,
           COALESCE(dcs.total_ties, 0) as total_ties, dcs.win_percentage,
           (SELECT ROUND(AVG(rdp.points)::numeric, 1)
            FROM round_debater_point rdp
            JOIN debater d2 ON rdp.debater_id = d2.id
            JOIN round_result rr ON rdp.round_result_id = rr.id AND rr.is_active IS NOT FALSE
            JOIN round r ON rr.round_id = r.id AND r.is_active IS NOT FALSE
            JOIN tournament t ON r.tournament_id = t.id AND t.scoring_scale = '30'
            WHERE d2.debater_id = dcs.debater_code AND rdp.points IS NOT NULL
           ) as avg_speaker_points,
           dcs.tournaments_attended
    FROM debater_career_stats dcs
    WHERE dcs.total_wins + dcs.total_losses > 0
      AND (LOWER(dcs.last_name) LIKE LOWER($1)
           OR LOWER(dcs.first_name) LIKE LOWER($1)
           OR LOWER(dcs.debater_code) LIKE LOWER($1)
           OR LOWER(dcs.first_name || ' ' || dcs.last_name) LIKE LOWER($1)
           OR LOWER(dcs.last_name || ', ' || dcs.first_name) LIKE LOWER($1))
    ORDER BY dcs.last_name, dcs.first_name
    LIMIT 50
"""

ALL_DEBATERS = """
    SELECT debater_code, first_name, last_name, total_wins, total_losses,
           COALESCE(total_ties, 0) as total_ties,
           win_percentage, avg_speaker_points, tournaments_attended
    FROM debater_career_stats
    WHERE total_wins + total_losses > 0
    ORDER BY last_name, first_name
"""

CAREER_STATS = """
    SELECT dcs.debater_code, dcs.first_name, dcs.last_name, dcs.total_wins, dcs.total_losses,
           COALESCE(dcs.total_ties, 0) as total_ties, dcs.win_percentage,
           (SELECT ROUND(AVG(rdp.points)::numeric, 1)
            FROM round_debater_point rdp
            JOIN debater d2 ON rdp.debater_id = d2.id
            JOIN round_result rr ON rdp.round_result_id = rr.id AND rr.is_active IS NOT FALSE
            JOIN round r ON rr.round_id = r.id AND r.is_active IS NOT FALSE
            JOIN tournament t ON r.tournament_id = t.id AND t.scoring_scale = '30'
            WHERE d2.debater_id = dcs.debater_code AND rdp.points IS NOT NULL
           ) as avg_speaker_points,
           dcs.tournaments_attended
    FROM debater_career_stats dcs
    WHERE dcs.debater_code = $1
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
        COUNT(DISTINCT rr.id) FILTER (WHERE
            (rr.aff_team_id = tm.id OR rr.neg_team_id = tm.id) AND rr.winner = 0
        ) as ties,
        ROUND(AVG(rdp.points) FILTER (WHERE t.scoring_scale = '30')::numeric, 1) as avg_sp
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
        COUNT(*) FILTER (WHERE rr.winner = 0) as ties,
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
        COALESCE(t.display_name, t.name) as tournament_name,
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
        COUNT(DISTINCT rr.id) FILTER (WHERE
            r.round_type = 'prelim' AND rr.winner = 0 AND
            (rr.aff_team_id = tm.id OR rr.neg_team_id = tm.id)
        ) as ties,
        ROUND(AVG(rdp.points)::numeric, 1) as avg_sp,
        (SELECT CASE
            WHEN sub_r.round_number = 'Finals' AND (
                (sub_rr.aff_team_id = tm.id AND sub_rr.winner = 1) OR
                (sub_rr.neg_team_id = tm.id AND sub_rr.winner = 2) OR
                sub_rr.winner = -1
            ) THEN 'Champion'
            WHEN sub_r.round_number = 'Finals' THEN 'Finalist'
            ELSE sub_r.round_number
        END
        FROM round sub_r
        JOIN round_result sub_rr ON sub_rr.round_id = sub_r.id
        WHERE sub_r.tournament_id = t.id
            AND sub_r.round_type = 'elim'
            AND sub_r.is_active IS NOT FALSE
            AND sub_rr.is_active IS NOT FALSE
            AND (sub_rr.aff_team_id = tm.id OR sub_rr.neg_team_id = tm.id)
        ORDER BY CASE sub_r.round_number
            WHEN 'Runoff' THEN 1
            WHEN 'Triples' THEN 2
            WHEN 'Doubles' THEN 3
            WHEN 'Octas' THEN 4
            WHEN 'Quarters' THEN 5
            WHEN 'Semis' THEN 6
            WHEN 'Finals' THEN 7
            ELSE 0
        END DESC
        LIMIT 1) as elim_result
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
    GROUP BY t.id, t.name, t.season, t.start_date, tm.id, tm.team_name
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
            WHEN rr.winner = 0 THEN 'T'
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
