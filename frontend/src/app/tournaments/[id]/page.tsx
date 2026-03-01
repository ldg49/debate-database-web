"use client";

import { useState, useEffect } from "react";
import { useParams, useSearchParams } from "next/navigation";
import type { Tournament, Standing, ElimResult, TeamRound } from "@/lib/types";
import { fetchApiClient } from "@/lib/api";
import { StandingsTable } from "@/components/tournament/standings-table";
import { ElimResults } from "@/components/tournament/elim-results";
import { RoundResults } from "@/components/tournament/round-results";

function TeamDetail({
  tournamentId,
  teamId,
  teamName,
  onClose,
}: {
  tournamentId: number;
  teamId: number;
  teamName: string;
  onClose: () => void;
}) {
  const [rounds, setRounds] = useState<TeamRound[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApiClient<TeamRound[]>(
      `/tournaments/${tournamentId}/teams/${teamId}`
    ).then((data) => {
      setRounds(data);
      setLoading(false);
    });
  }, [tournamentId, teamId]);

  const wins = rounds.filter(
    (r) => r.result.startsWith("W") || r.result === "BYE"
  ).length;
  const losses = rounds.filter((r) => r.result.startsWith("L")).length;

  return (
    <div className="mb-4 p-3 border border-gray-200 rounded bg-gray-50">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-bold" style={{ color: "var(--sr-navy)" }}>
          {teamName} ({wins}-{losses})
        </h3>
        <button
          onClick={onClose}
          className="text-xs text-gray-500 hover:text-gray-700 cursor-pointer"
        >
          Close
        </button>
      </div>
      {loading ? (
        <p className="text-xs text-gray-400">Loading...</p>
      ) : (
        <table className="sr-table">
          <thead>
            <tr>
              <th>Rd</th>
              <th>Side</th>
              <th>Opponent</th>
              <th>Judge</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {rounds.map((r, i) => (
              <tr key={i}>
                <td>{r.round}</td>
                <td>{r.side}</td>
                <td>{r.opponent || "BYE"}</td>
                <td>{r.judge || "-"}</td>
                <td>
                  <span
                    className={
                      r.result.startsWith("W")
                        ? "result-w"
                        : r.result.startsWith("L")
                        ? "result-l"
                        : "result-bye"
                    }
                  >
                    {r.result}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default function TournamentPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const tournamentId = Number(params.id);

  const [tournament, setTournament] = useState<Tournament | null>(null);
  const [standings, setStandings] = useState<Standing[]>([]);
  const [elims, setElims] = useState<ElimResult[]>([]);
  const [activeTab, setActiveTab] = useState("standings");
  const [selectedTeam, setSelectedTeam] = useState<{
    id: number;
    name: string;
  } | null>(null);

  useEffect(() => {
    fetchApiClient<Tournament>(`/tournaments/${tournamentId}`).then(
      setTournament
    );
    fetchApiClient<Standing[]>(`/tournaments/${tournamentId}/standings`).then(
      setStandings
    );
    fetchApiClient<ElimResult[]>(`/tournaments/${tournamentId}/elims`).then(
      setElims
    );
  }, [tournamentId]);

  // Handle team query param
  useEffect(() => {
    const teamId = searchParams.get("team");
    if (teamId && standings.length > 0) {
      const team = standings.find((s) => s.team_id === Number(teamId));
      if (team) {
        setSelectedTeam({ id: team.team_id, name: team.team_name });
      }
    }
  }, [searchParams, standings]);

  if (!tournament) {
    return <p className="text-xs text-gray-400">Loading...</p>;
  }

  const tabs = [
    { key: "standings", label: "Standings" },
    { key: "elims", label: "Elim Results" },
    { key: "rounds", label: "By Round" },
  ];

  return (
    <div>
      <div className="breadcrumb">
        <a href="/">Home</a> &gt; <a href="/tournaments">Tournaments</a> &gt;{" "}
        {tournament.name}
      </div>
      <h1
        className="text-xl font-bold mt-1 mb-1"
        style={{ color: "var(--sr-navy)" }}
      >
        {tournament.name}
      </h1>
      <div className="text-xs text-gray-500 mb-3">
        {tournament.season} |{" "}
        {tournament.start_date
          ? new Date(tournament.start_date).toLocaleDateString()
          : ""}
      </div>

      {selectedTeam && (
        <TeamDetail
          tournamentId={tournamentId}
          teamId={selectedTeam.id}
          teamName={selectedTeam.name}
          onClose={() => setSelectedTeam(null)}
        />
      )}

      <div className="tab-nav">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={`tab-btn ${activeTab === tab.key ? "active" : ""}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "standings" && (
        <StandingsTable
          standings={standings}
          tournamentId={tournamentId}
        />
      )}
      {activeTab === "elims" && (
        <ElimResults results={elims} tournamentId={tournamentId} />
      )}
      {activeTab === "rounds" && (
        <RoundResults tournamentId={tournamentId} />
      )}
    </div>
  );
}
