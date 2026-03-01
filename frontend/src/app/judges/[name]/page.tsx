"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import type {
  JudgeCareer,
  JudgeSeasonSummary,
  JudgeTournamentEntry,
  JudgeRound,
} from "@/lib/types";
import { fetchApiClient } from "@/lib/api";
import { TournamentLink } from "@/components/common/tournament-link";

function affPct(aff: number, total: number): string {
  if (total === 0) return "-";
  return ((aff / total) * 100).toFixed(1) + "%";
}

function TournamentRow({ entry, judgeName }: { entry: JudgeTournamentEntry; judgeName: string }) {
  const [open, setOpen] = useState(false);
  const [rounds, setRounds] = useState<JudgeRound[] | null>(null);
  const [loading, setLoading] = useState(false);

  const toggle = async () => {
    if (!open && rounds === null) {
      setLoading(true);
      try {
        const data = await fetchApiClient<JudgeRound[]>(
          `/judges/${encodeURIComponent(judgeName)}/tournaments/${entry.tournament_id}/rounds`
        );
        setRounds(data);
      } catch {
        setRounds([]);
      }
      setLoading(false);
    }
    setOpen(!open);
  };

  return (
    <div>
      <div className="tourn-header flex items-center gap-2" onClick={toggle}>
        <span className="text-xs w-4 inline-block">
          {open ? "\u25BC" : "\u25B6"}
        </span>
        <TournamentLink id={entry.tournament_id}>
          {entry.tournament_name}
        </TournamentLink>
        <span className="text-gray-500">
          &mdash; {entry.decisions} decisions ({affPct(entry.aff_votes, entry.decisions)} Aff)
          {entry.elim_decisions > 0 && `, ${entry.elim_decisions} elim`}
        </span>
      </div>
      {open && (
        <div className="pl-6 pb-2">
          {loading ? (
            <div className="text-xs text-gray-400 py-2">Loading...</div>
          ) : rounds && rounds.length > 0 ? (
            <table className="sr-table" style={{ maxWidth: 700 }}>
              <thead>
                <tr>
                  <th>Rd</th>
                  <th>Aff</th>
                  <th>Neg</th>
                  <th>Vote</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {rounds.map((r, i) => (
                  <tr key={i}>
                    <td>{r.round}</td>
                    <td>{r.aff_team}</td>
                    <td>{r.neg_team || "BYE"}</td>
                    <td>
                      <span className={r.judge_vote === 1 ? "result-w" : "result-l"}>
                        {r.judge_vote === 1 ? "Aff" : "Neg"}
                      </span>
                    </td>
                    <td>
                      {r.decision}
                      {r.dissent && (
                        <span className="text-red-600 ml-1 text-xs font-bold" title="Dissent">
                          *
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="text-xs text-gray-400 py-2">No round data</div>
          )}
        </div>
      )}
    </div>
  );
}

export default function JudgePage() {
  const params = useParams();
  const judgeName = decodeURIComponent(params.name as string);

  const [career, setCareer] = useState<JudgeCareer | null>(null);
  const [seasons, setSeasons] = useState<JudgeSeasonSummary[]>([]);
  const [tournaments, setTournaments] = useState<JudgeTournamentEntry[]>([]);

  useEffect(() => {
    const encoded = encodeURIComponent(judgeName);
    fetchApiClient<JudgeCareer>(`/judges/${encoded}`).then(setCareer);
    fetchApiClient<JudgeSeasonSummary[]>(`/judges/${encoded}/season-summary`).then(setSeasons);
    fetchApiClient<JudgeTournamentEntry[]>(`/judges/${encoded}/tournaments`).then(setTournaments);
  }, [judgeName]);

  if (!career) {
    return <p className="text-xs text-gray-400">Loading...</p>;
  }

  if ("error" in career) {
    return (
      <div>
        <div className="breadcrumb">
          <a href="/">Home</a> &gt; <a href="/judges">Judges</a> &gt; Not Found
        </div>
        <h1 className="text-xl font-bold mt-2">Judge not found</h1>
      </div>
    );
  }

  const firstYear = career.first_seen ? new Date(career.first_seen).getFullYear() : "";
  const lastYear = career.last_seen ? new Date(career.last_seen).getFullYear() : "";
  const yearRange = firstYear === lastYear ? `${firstYear}` : `${firstYear}-${lastYear}`;

  return (
    <div>
      <div className="breadcrumb">
        <a href="/">Home</a> &gt; <a href="/judges">Judges</a> &gt; {career.name}
      </div>

      {/* Header */}
      <h1 className="text-2xl font-bold mt-1" style={{ color: "var(--sr-navy)" }}>
        {career.name}
      </h1>
      <div className="text-sm text-gray-600 mt-1">{yearRange}</div>
      <div className="text-sm mt-1 font-semibold">
        {career.total_decisions} decisions | {affPct(career.aff_votes, career.total_decisions)} Aff |{" "}
        {career.tournaments} tournaments
      </div>

      {/* Season Summary */}
      <div className="section-header mt-4">Season Summary</div>
      <table className="sr-table mt-1">
        <thead>
          <tr>
            <th>Season</th>
            <th className="text-right">Tourns</th>
            <th className="text-right">Decisions</th>
            <th className="text-right">Aff</th>
            <th className="text-right">Neg</th>
            <th className="text-right">Aff%</th>
            <th className="text-right">Elims</th>
          </tr>
        </thead>
        <tbody>
          {seasons.map((s, i) => (
            <tr key={i}>
              <td>{s.season}</td>
              <td className="num">{s.tournaments}</td>
              <td className="num">{s.decisions}</td>
              <td className="num">{s.aff_votes}</td>
              <td className="num">{s.neg_votes}</td>
              <td className="num">{affPct(s.aff_votes, s.decisions)}</td>
              <td className="num">{s.elim_decisions}</td>
            </tr>
          ))}
          {/* Career total */}
          <tr className="total-row">
            <td>Career</td>
            <td className="num">{career.tournaments}</td>
            <td className="num">{career.total_decisions}</td>
            <td className="num">{career.aff_votes}</td>
            <td className="num">{career.neg_votes}</td>
            <td className="num">{affPct(career.aff_votes, career.total_decisions)}</td>
            <td className="num">{seasons.reduce((sum, s) => sum + s.elim_decisions, 0)}</td>
          </tr>
        </tbody>
      </table>

      {/* Tournament Log */}
      <div className="section-header">Tournament Log</div>
      <div className="border border-gray-200 mt-1">
        {tournaments.map((t, i) => (
          <TournamentRow key={i} entry={t} judgeName={judgeName} />
        ))}
      </div>
    </div>
  );
}
