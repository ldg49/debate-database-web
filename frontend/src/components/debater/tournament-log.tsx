"use client";

import { useState } from "react";
import type { TournamentEntry, TournamentRound } from "@/lib/types";
import { formatRecord, formatSP } from "@/lib/utils";
import { TournamentLink } from "@/components/common/tournament-link";
import { fetchApiClient } from "@/lib/api";

function resultClass(result: string) {
  if (result === "W") return "result-w";
  if (result === "L") return "result-l";
  if (result === "T") return "result-tie";
  if (result === "BYE" || result === "FFT") return "result-bye";
  return "";
}

function TournamentRow({
  entry,
  code,
}: {
  entry: TournamentEntry;
  code: string;
}) {
  const [open, setOpen] = useState(false);
  const [rounds, setRounds] = useState<TournamentRound[] | null>(null);
  const [loading, setLoading] = useState(false);

  const toggle = async () => {
    if (!open && rounds === null) {
      setLoading(true);
      try {
        const data = await fetchApiClient<TournamentRound[]>(
          `/debaters/${code}/tournaments/${entry.tournament_id}/rounds`
        );
        setRounds(data);
      } catch {
        setRounds([]);
      }
      setLoading(false);
    }
    setOpen(!open);
  };

  const record = formatRecord(entry.wins, entry.losses, entry.ties);
  const elimTag = entry.elim_result ? `, ${entry.elim_result}` : "";
  const sp = entry.avg_sp ? ` ${formatSP(entry.avg_sp)}` : "";

  return (
    <div>
      <div className="tourn-header flex items-center gap-2" onClick={toggle}>
        <span className="text-xs w-4 inline-block">{open ? "\u25BC" : "\u25B6"}</span>
        <TournamentLink id={entry.tournament_id}>
          {entry.tournament_name}
        </TournamentLink>
        <span className="text-gray-500">
          &mdash; {entry.team_name} ({record}{elimTag}){sp}
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
                  <th>Side</th>
                  <th>Opponent</th>
                  <th>Judge</th>
                  <th>Result</th>
                  <th className="text-right">SP</th>
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
                      <span className={resultClass(r.result)}>
                        {r.result}
                        {r.ballot_count &&
                        r.round_type === "elim" &&
                        r.result !== "BYE" &&
                        r.result !== "FFT"
                          ? ` (${r.ballot_count})`
                          : ""}
                      </span>
                    </td>
                    <td className="num">{formatSP(r.speaker_points)}</td>
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

export function TournamentLog({
  tournaments,
  code,
}: {
  tournaments: TournamentEntry[];
  code: string;
}) {
  return (
    <div>
      <div className="section-header">Tournament Log</div>
      <div className="border border-gray-200 mt-1">
        {tournaments.map((t, i) => (
          <TournamentRow key={i} entry={t} code={code} />
        ))}
      </div>
    </div>
  );
}
