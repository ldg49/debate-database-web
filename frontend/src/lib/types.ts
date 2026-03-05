export interface DebaterCareer {
  debater_code: string;
  first_name: string;
  last_name: string;
  total_wins: number;
  total_losses: number;
  total_ties: number;
  win_percentage: number;
  avg_speaker_points: number | null;
  tournaments_attended: number;
}

export interface SeasonSummary {
  season: string;
  school: string;
  partners: string | null;
  wins: number;
  losses: number;
  ties: number;
  avg_sp: number | null;
}

export interface PartnerRecord {
  partner_code: string;
  partner_name: string;
  school: string;
  wins: number;
  losses: number;
  ties: number;
  tournaments: number;
}

export interface TournamentEntry {
  tournament_id: number;
  tournament_name: string;
  season: string;
  start_date: string;
  team_name: string;
  wins: number;
  losses: number;
  ties: number;
  avg_sp: number | null;
  elim_result: string | null;
}

export interface TournamentRound {
  round: string;
  round_type: string;
  side: string;
  opponent: string | null;
  judge: string | null;
  result: string;
  ballot_count: string | null;
  speaker_points: number | null;
}

export interface Tournament {
  id: number;
  name: string;
  display_name: string | null;
  host_school: string | null;
  tournament_type: string | null;
  season: string;
  start_date: string;
  end_date: string | null;
}

export interface TournamentSearchResult {
  id: number;
  name: string;
  display_name: string | null;
  host_school: string | null;
  tournament_type: string | null;
  season: string;
  start_date: string;
}

export interface Standing {
  team_id: number;
  team_name: string;
  debaters: string | null;
  debater_codes: string | null;
  prelim_wins: number;
  prelim_losses: number;
  prelim_ties: number;
  avg_sp: number | null;
}

export interface ElimResult {
  round: string;
  round_name: string;
  aff_team: string;
  aff_team_id: number;
  neg_team: string;
  neg_team_id: number | null;
  judges: string | null;
  decision: string;
  winner: number;
}

export interface RoundInfo {
  round_number: string;
  round_type: string;
}

export interface RoundResult {
  result_id: number;
  aff_team: string;
  aff_team_id: number;
  aff_debaters: string | null;
  neg_team: string | null;
  neg_team_id: number | null;
  neg_debaters: string | null;
  judge: string | null;
  decision: string;
}

export interface TeamRound {
  round: string;
  round_type: string;
  side: string;
  opponent: string | null;
  opponent_id: number | null;
  judge: string | null;
  result: string;
}

export interface OverviewStats {
  tournaments: number;
  debaters: number;
  debates: number;
  teams: number;
}

export interface JudgeCareer {
  name: string;
  tournaments: number;
  total_decisions: number;
  aff_votes: number;
  neg_votes: number;
  first_seen: string;
  last_seen: string;
}

export interface JudgeSeasonSummary {
  season: string;
  tournaments: number;
  decisions: number;
  aff_votes: number;
  neg_votes: number;
  elim_decisions: number;
}

export interface JudgeTournamentEntry {
  tournament_id: number;
  tournament_name: string;
  season: string;
  start_date: string;
  decisions: number;
  aff_votes: number;
  neg_votes: number;
  elim_decisions: number;
}

export interface JudgePanelStats {
  career: { panel_decisions: number; majority: number; minority: number };
  seasons: { season: string; panel_decisions: number; majority: number; minority: number }[];
}

export interface JudgeRound {
  round: string;
  round_type: string;
  aff_team: string;
  neg_team: string | null;
  judge_vote: number;
  winner: number;
  decision: string;
  ballot_count: string | null;
  dissent: boolean;
}

export interface DataGapTournament {
  id: number;
  name: string;
  season: string;
  start_date: string | null;
  total_debates: number;
  prelim_debates: number;
  elim_debates: number;
  sp_coverage_pct: number | null;
  missing_names: number;
  total_debaters: number;
  name_coverage_pct: number | null;
  known_issues: number;
  issue_notes: string[];
  gaps: string[];
}

export interface DataGapSummary {
  no_results: number;
  missing_elims: number;
  missing_prelims: number;
  missing_speaker_points: number;
  missing_names: number;
  known_issues: number;
}

export interface DataGapsResponse {
  tournaments: DataGapTournament[];
  summary: DataGapSummary;
}
