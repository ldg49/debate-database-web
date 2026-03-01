SEARCH_TOURNAMENTS = """
    SELECT id, name, season, start_date
    FROM tournament
    WHERE is_active IS NOT FALSE
      AND ($1::text IS NULL OR LOWER(name) LIKE LOWER($1))
      AND ($2::text IS NULL OR season = $2)
    ORDER BY start_date DESC NULLS LAST
    LIMIT 200
"""

TOURNAMENT_DETAIL = """
    SELECT id, name, season, start_date, end_date
    FROM tournament
    WHERE id = $1 AND is_active IS NOT FALSE
"""

STANDINGS = """
    SELECT
        t.id as team_id,
        t.team_name,
        (SELECT string_agg(
            TRIM(COALESCE(d.first_name, '') || ' ' || COALESCE(d.last_name, '')),
            ', ' ORDER BY d.last_name)
         FROM team_debater td JOIN debater d ON td.debater_id = d.id
         WHERE td.team_id = t.id) as debaters,
        (SELECT string_agg(d.debater_id, ', ' ORDER BY d.last_name)
         FROM team_debater td JOIN debater d ON td.debater_id = d.id
         WHERE td.team_id = t.id) as debater_codes,
        (SELECT COUNT(*) FROM round_result rr2
         JOIN round r2 ON rr2.round_id = r2.id
         WHERE ((rr2.aff_team_id = t.id AND rr2.winner = 1) OR
                (rr2.neg_team_id = t.id AND rr2.winner = 2))
           AND r2.round_type = 'prelim' AND rr2.is_active IS NOT FALSE) as prelim_wins,
        (SELECT COUNT(*) FROM round_result rr2
         JOIN round r2 ON rr2.round_id = r2.id
         WHERE ((rr2.aff_team_id = t.id AND rr2.winner = 2) OR
                (rr2.neg_team_id = t.id AND rr2.winner = 1))
           AND r2.round_type = 'prelim' AND rr2.is_active IS NOT FALSE) as prelim_losses,
        (SELECT ROUND(AVG(rdp.points)::numeric, 1)
         FROM round_debater_point rdp
         JOIN debater d ON rdp.debater_id = d.id
         JOIN team_debater td ON td.debater_id = d.id AND td.team_id = t.id
         JOIN round_result rr2 ON rdp.round_result_id = rr2.id
         JOIN round r2 ON rr2.round_id = r2.id
         WHERE r2.tournament_id = $1 AND rdp.points IS NOT NULL
           AND rr2.is_active IS NOT FALSE) as avg_sp
    FROM team t
    WHERE t.tournament_id = $1 AND t.is_active IS NOT FALSE
    ORDER BY (SELECT COUNT(*) FROM round_result rr2
         JOIN round r2 ON rr2.round_id = r2.id
         WHERE ((rr2.aff_team_id = t.id AND rr2.winner = 1) OR
                (rr2.neg_team_id = t.id AND rr2.winner = 2))
           AND r2.round_type = 'prelim' AND rr2.is_active IS NOT FALSE) DESC,
         t.team_name ASC
"""

ELIM_RESULTS = """
    SELECT
        r.round_number as round,
        CASE
            WHEN LOWER(r.round_number) LIKE '%double%' THEN 'Doubles'
            WHEN LOWER(r.round_number) LIKE '%triple%' THEN 'Triples'
            WHEN LOWER(r.round_number) LIKE '%octa%' OR LOWER(r.round_number) LIKE '%octo%' THEN 'Octas'
            WHEN LOWER(r.round_number) LIKE '%quarter%' THEN 'Quarters'
            WHEN LOWER(r.round_number) LIKE '%semi%' THEN 'Semis'
            WHEN LOWER(r.round_number) LIKE '%final%' AND LOWER(r.round_number) NOT LIKE '%semi%' THEN 'Finals'
            WHEN LOWER(r.round_number) LIKE '%runoff%' THEN 'Runoff'
            ELSE r.round_number
        END as round_name,
        aff_tm.team_name as aff_team,
        aff_tm.id as aff_team_id,
        COALESCE(neg_tm.team_name, 'BYE') as neg_team,
        neg_tm.id as neg_team_id,
        (SELECT string_agg(
             CASE WHEN rjv.vote != rr.winner THEN j.name || '*' ELSE j.name END,
             ', ')
         FROM round_judges_vote rjv JOIN judge j ON rjv.judge_id = j.id
         WHERE rjv.round_result_id = rr.id) as judges,
        CASE WHEN rr.result_type = 'bye' THEN 'BYE'
             WHEN rr.result_type = 'closeout' THEN 'CLOSEOUT'
             WHEN rr.result_type = 'forfeit' THEN 'FORFEIT'
             WHEN rr.winner = 1 THEN 'AFF ' || COALESCE(rr.ballot_count, '')
             WHEN rr.winner = 2 THEN 'NEG ' || COALESCE(rr.ballot_count, '')
             WHEN rr.winner = -1 THEN COALESCE(rr.ballot_count, '')
        END as decision,
        rr.winner
    FROM round_result rr
    JOIN round r ON rr.round_id = r.id
    JOIN team aff_tm ON rr.aff_team_id = aff_tm.id
    LEFT JOIN team neg_tm ON rr.neg_team_id = neg_tm.id
    WHERE r.tournament_id = $1 AND r.round_type = 'elim' AND rr.is_active IS NOT FALSE
    ORDER BY CASE
        WHEN LOWER(r.round_number) LIKE '%runoff%' THEN 1
        WHEN LOWER(r.round_number) LIKE '%triple%' THEN 2
        WHEN LOWER(r.round_number) LIKE '%double%' THEN 3
        WHEN LOWER(r.round_number) LIKE '%octa%' OR LOWER(r.round_number) LIKE '%octo%' THEN 4
        WHEN LOWER(r.round_number) LIKE '%quarter%' THEN 5
        WHEN LOWER(r.round_number) LIKE '%semi%' THEN 6
        WHEN LOWER(r.round_number) LIKE '%final%' THEN 7
        ELSE 0
    END DESC, aff_tm.team_name
"""

ROUND_LIST = """
    SELECT DISTINCT round_number, round_type,
        CASE WHEN round_type = 'prelim' THEN 0 ELSE 1 END as type_order,
        CASE WHEN REGEXP_REPLACE(round_number, '[^0-9]', '', 'g') = '' THEN 0
             ELSE CAST(REGEXP_REPLACE(round_number, '[^0-9]', '', 'g') AS INTEGER) END as num_order
    FROM round WHERE tournament_id = $1
    ORDER BY type_order, num_order
"""

ROUND_RESULTS = """
    SELECT
        rr.id as result_id,
        aff_tm.team_name as aff_team,
        aff_tm.id as aff_team_id,
        (SELECT string_agg(d.last_name || ' (' || COALESCE(rdp.points::text, '-') || ')', ', ' ORDER BY d.last_name)
         FROM team_debater td
         JOIN debater d ON td.debater_id = d.id
         LEFT JOIN round_debater_point rdp ON rdp.round_result_id = rr.id AND rdp.debater_id = d.id
         WHERE td.team_id = rr.aff_team_id) as aff_debaters,
        neg_tm.team_name as neg_team,
        neg_tm.id as neg_team_id,
        (SELECT string_agg(d.last_name || ' (' || COALESCE(rdp.points::text, '-') || ')', ', ' ORDER BY d.last_name)
         FROM team_debater td
         JOIN debater d ON td.debater_id = d.id
         LEFT JOIN round_debater_point rdp ON rdp.round_result_id = rr.id AND rdp.debater_id = d.id
         WHERE td.team_id = rr.neg_team_id) as neg_debaters,
        (SELECT string_agg(
             CASE WHEN rjv.vote != rr.winner THEN j.name || '*' ELSE j.name END,
             ', ')
         FROM round_judges_vote rjv JOIN judge j ON rjv.judge_id = j.id
         WHERE rjv.round_result_id = rr.id) as judge,
        CASE WHEN rr.winner = 1 THEN 'AFF'
             WHEN rr.winner = 2 THEN 'NEG'
             WHEN rr.winner = -1 THEN 'BYE'
        END as decision
    FROM round_result rr
    JOIN round r ON rr.round_id = r.id
    JOIN team aff_tm ON rr.aff_team_id = aff_tm.id
    LEFT JOIN team neg_tm ON rr.neg_team_id = neg_tm.id
    WHERE r.tournament_id = $1 AND r.round_number = $2 AND rr.is_active IS NOT FALSE
    ORDER BY aff_tm.team_name
"""

TEAM_ROUNDS = """
    SELECT
        r.round_number as round,
        r.round_type,
        CASE WHEN rr.aff_team_id = $1 THEN 'Aff' ELSE 'Neg' END as side,
        CASE WHEN rr.aff_team_id = $1 THEN neg_tm.team_name ELSE aff_tm.team_name END as opponent,
        CASE WHEN rr.aff_team_id = $1 THEN neg_tm.id ELSE aff_tm.id END as opponent_id,
        (SELECT string_agg(
             CASE WHEN rjv.vote != rr.winner THEN j.name || '*' ELSE j.name END,
             ', ')
         FROM round_judges_vote rjv JOIN judge j ON rjv.judge_id = j.id
         WHERE rjv.round_result_id = rr.id) as judge,
        CASE
            WHEN rr.result_type = 'bye' THEN 'BYE'
            WHEN rr.result_type = 'forfeit' THEN 'FFT'
            WHEN rr.winner = -1 THEN 'BYE'
            WHEN (rr.aff_team_id = $1 AND rr.winner = 1) OR (rr.neg_team_id = $1 AND rr.winner = 2) THEN
                CASE WHEN r.round_type = 'elim' AND rr.ballot_count IS NOT NULL AND rr.ballot_count != ''
                     THEN 'W (' || rr.ballot_count || ')'
                     ELSE 'W'
                END
            ELSE
                CASE WHEN r.round_type = 'elim' AND rr.ballot_count IS NOT NULL AND rr.ballot_count != ''
                     THEN 'L (' || rr.ballot_count || ')'
                     ELSE 'L'
                END
        END as result
    FROM round_result rr
    JOIN round r ON rr.round_id = r.id
    LEFT JOIN team aff_tm ON rr.aff_team_id = aff_tm.id
    LEFT JOIN team neg_tm ON rr.neg_team_id = neg_tm.id
    WHERE (rr.aff_team_id = $1 OR rr.neg_team_id = $1)
        AND r.tournament_id = $2
        AND rr.is_active IS NOT FALSE
    ORDER BY CASE WHEN r.round_type = 'prelim' THEN 0 ELSE 1 END,
             CASE WHEN REGEXP_REPLACE(r.round_number, '[^0-9]', '', 'g') = '' THEN 0
                  ELSE CAST(REGEXP_REPLACE(r.round_number, '[^0-9]', '', 'g') AS INTEGER) END
"""

TEAM_SEARCH = """
    SELECT team_name, tournament_name, tournament_year,
           prelim_record, avg_speaker_points, elim_wins, elim_losses
    FROM team_tournament_stats
    WHERE LOWER(team_name) LIKE LOWER($1)
      AND ($2::int IS NULL OR tournament_year = $2)
    ORDER BY tournament_year DESC, prelim_wins DESC
    LIMIT 200
"""
