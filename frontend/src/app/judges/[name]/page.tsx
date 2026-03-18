"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import type {
  JudgeCareer,
  JudgeSeasonSummary,
  JudgeTournamentEntry,
  JudgeRound,
  JudgePanelStats,
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
          &mdash; {entry.decisions} decisions ({affPct(entry.aff_votes, entry.aff_votes + entry.neg_votes)} Aff)
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
  const [panelStats, setPanelStats] = useState<JudgePanelStats | null>(null);

  useEffect(() => {
    const encoded = encodeURIComponent(judgeName);
    fetchApiClient<JudgeCareer>(`/judges/${encoded}`).then(setCareer);
    fetchApiClient<JudgeSeasonSummary[]>(`/judges/${encoded}/season-summary`).then(setSeasons);
    fetchApiClient<JudgeTournamentEntry[]>(`/judges/${encoded}/tournaments`).then(setTournaments);
    fetchApiClient<JudgePanelStats>(`/judges/${encoded}/panel-stats`).then(setPanelStats);
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
        {career.total_decisions} decisions | {affPct(career.aff_votes, career.aff_votes + career.neg_votes)} Aff |{" "}
        {career.tournaments} tournaments
      </div>

      {/* Visual Stats */}
      <div className="flex gap-4 mt-4" style={{ maxWidth: 600 }}>
        {/* Aff/Neg Tendency */}
        <div className="stat-card flex-1">
          <div className="stat-label" style={{ marginBottom: 8 }}>Aff/Neg Tendency</div>
          {(() => {
            const affNegTotal = career.aff_votes + career.neg_votes;
            return affNegTotal > 0 ? (
              <>
                <div style={{
                  display: "flex", height: 24, borderRadius: 4, overflow: "hidden",
                  border: "1px solid #ccc"
                }}>
                  <div style={{
                    width: `${(career.aff_votes / affNegTotal) * 100}%`,
                    background: "#2d6a2e", minWidth: career.aff_votes > 0 ? 2 : 0
                  }} />
                  <div style={{
                    width: `${(career.neg_votes / affNegTotal) * 100}%`,
                    background: "#a31515", minWidth: career.neg_votes > 0 ? 2 : 0
                  }} />
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, fontSize: 12 }}>
                  <span style={{ color: "#2d6a2e", fontWeight: 600 }}>
                    {affPct(career.aff_votes, affNegTotal)} Aff ({career.aff_votes})
                  </span>
                  <span style={{ color: "#a31515", fontWeight: 600 }}>
                    {affPct(career.neg_votes, affNegTotal)} Neg ({career.neg_votes})
                  </span>
                </div>
              </>
            ) : (
              <div className="text-xs text-gray-400">No decisions</div>
            );
          })()}
        </div>

        {/* Panel Record */}
        <div className="stat-card flex-1">
          <div className="stat-label" style={{ marginBottom: 8 }}>Panel Record</div>
          {panelStats && panelStats.career.panel_decisions > 0 ? (
            <>
              <div className="stat-value">
                {((panelStats.career.majority / panelStats.career.panel_decisions) * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: 12, color: "#666", marginTop: 2 }}>
                Top of Decision {panelStats.career.majority} of {panelStats.career.panel_decisions}
              </div>
              <div style={{ fontSize: 12, color: "#a31515", marginTop: 2 }}>
                Sit {panelStats.career.panel_decisions - panelStats.career.majority} of {panelStats.career.panel_decisions}
              </div>
            </>
          ) : (
            <div className="text-xs text-gray-400">
              {panelStats ? "No panel decisions" : "Loading..."}
            </div>
          )}
        </div>
      </div>

      {/* Season Summary */}
      <div style={{ width: "fit-content" }}>
      <div className="section-header mt-4">Season Summary</div>
      {(() => {
        const panelBySeason: Record<string, { panel_decisions: number; majority: number }> = {};
        if (panelStats) {
          for (const ps of panelStats.seasons) {
            panelBySeason[ps.season] = { panel_decisions: ps.panel_decisions, majority: ps.majority };
          }
        }
        return (
          <table className="sr-table mt-1" style={{ width: "auto" }}>
            <thead>
              <tr>
                <th>Season</th>
                <th className="text-right">Tourns</th>
                <th className="text-right">Decisions</th>
                <th className="text-right">Aff</th>
                <th className="text-right">Neg</th>
                <th className="text-right">Aff%</th>
                <th className="text-right">Elims</th>
                <th className="text-right">Panel</th>
                <th className="text-right" style={{ whiteSpace: "normal", minWidth: 40 }}>Top of Decision</th>
                <th className="text-right">Sit%</th>
              </tr>
            </thead>
            <tbody>
              {seasons.map((s, i) => {
                const ps = panelBySeason[s.season];
                return (
                  <tr key={i}>
                    <td>{s.season}</td>
                    <td className="num">{s.tournaments}</td>
                    <td className="num">{s.decisions}</td>
                    <td className="num">{s.aff_votes}</td>
                    <td className="num">{s.neg_votes}</td>
                    <td className="num">{affPct(s.aff_votes, s.aff_votes + s.neg_votes)}</td>
                    <td className="num">{s.elim_decisions}</td>
                    <td className="num">{ps ? ps.panel_decisions : "-"}</td>
                    <td className="num">{ps ? ps.majority : "-"}</td>
                    <td className="num">
                      {ps && ps.panel_decisions > 0
                        ? (((ps.panel_decisions - ps.majority) / ps.panel_decisions) * 100).toFixed(1) + "%"
                        : "-"}
                    </td>
                  </tr>
                );
              })}
              {/* Career total */}
              <tr className="total-row">
                <td>Career</td>
                <td className="num">{career.tournaments}</td>
                <td className="num">{career.total_decisions}</td>
                <td className="num">{career.aff_votes}</td>
                <td className="num">{career.neg_votes}</td>
                <td className="num">{affPct(career.aff_votes, career.aff_votes + career.neg_votes)}</td>
                <td className="num">{seasons.reduce((sum, s) => sum + s.elim_decisions, 0)}</td>
                <td className="num">{panelStats ? panelStats.career.panel_decisions : "-"}</td>
                <td className="num">{panelStats ? panelStats.career.majority : "-"}</td>
                <td className="num">
                  {panelStats && panelStats.career.panel_decisions > 0
                    ? (((panelStats.career.panel_decisions - panelStats.career.majority) / panelStats.career.panel_decisions) * 100).toFixed(1) + "%"
                    : "-"}
                </td>
              </tr>
            </tbody>
          </table>
        );
      })()}
      </div>

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
