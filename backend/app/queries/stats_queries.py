OVERVIEW = """
    SELECT
        (SELECT COUNT(*) FROM tournament WHERE is_active IS NOT FALSE) as tournaments,
        (SELECT COUNT(DISTINCT debater_id) FROM debater WHERE is_active IS NOT FALSE) as debaters,
        (SELECT COUNT(*) FROM round_result WHERE is_active IS NOT FALSE) as debates,
        (SELECT COUNT(*) FROM team WHERE is_active IS NOT FALSE) as teams
"""
