"use client";

import { useState, useEffect } from "react";
import type { RoundInfo, RoundResult } from "@/lib/types";
import { fetchApiClient } from "@/lib/api";

export function RoundResults({ tournamentId }: { tournamentId: number }) {
  const [rounds, setRounds] = useState<RoundInfo[]>([]);
  const [selectedRound, setSelectedRound] = useState<string>("");
  const [results, setResults] = useState<RoundResult[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchApiClient<RoundInfo[]>(`/tournaments/${tournamentId}/rounds`).then(
      (data) => {
        setRounds(data);
        if (data.length > 0) setSelectedRound(data[0].round_number);
      }
    );
  }, [tournamentId]);

  useEffect(() => {
    if (!selectedRound) return;
    setLoading(true);
    fetchApiClient<RoundResult[]>(
      `/tournaments/${tournamentId}/rounds/${encodeURIComponent(selectedRound)}`
    ).then((data) => {
      setResults(data);
      setLoading(false);
    });
  }, [tournamentId, selectedRound]);

  return (
    <div>
      <div className="mb-2">
        <select
          value={selectedRound}
          onChange={(e) => setSelectedRound(e.target.value)}
          className="border border-gray-300 px-2 py-1 text-xs rounded"
        >
          {rounds.map((r) => (
            <option key={r.round_number} value={r.round_number}>
              {r.round_number}
            </option>
          ))}
        </select>
      </div>
      {loading ? (
        <p className="text-xs text-gray-400">Loading...</p>
      ) : results.length > 0 ? (
        <table className="sr-table">
          <thead>
            <tr>
              <th>Aff</th>
              <th>Aff Debaters</th>
              <th>Neg</th>
              <th>Neg Debaters</th>
              <th>Judge</th>
              <th>Dec</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr key={r.result_id}>
                <td>{r.aff_team}</td>
                <td>{r.aff_debaters || "-"}</td>
                <td>{r.neg_team || "BYE"}</td>
                <td>{r.neg_debaters || "-"}</td>
                <td>{r.judge || "-"}</td>
                <td>
                  <span
                    className={
                      r.decision === "AFF"
                        ? "result-w"
                        : r.decision === "NEG"
                        ? "result-l"
                        : ""
                    }
                  >
                    {r.decision}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="text-xs text-gray-400">No results for this round.</p>
      )}
    </div>
  );
}
