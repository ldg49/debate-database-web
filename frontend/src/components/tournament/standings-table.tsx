import type { Standing } from "@/lib/types";
import { formatSP } from "@/lib/utils";
import Link from "next/link";

export function StandingsTable({
  standings,
  tournamentId,
}: {
  standings: Standing[];
  tournamentId: number;
}) {
  return (
    <table className="sr-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Team</th>
          <th>Debaters</th>
          <th className="text-right">W</th>
          <th className="text-right">L</th>
          <th className="text-right">T</th>
          <th className="text-right">SP</th>
        </tr>
      </thead>
      <tbody>
        {standings.map((s, i) => (
          <tr key={s.team_id}>
            <td className="num">{i + 1}</td>
            <td>
              <Link
                href={`/tournaments/${tournamentId}?team=${s.team_id}`}
                className="sr-link"
              >
                {s.team_name}
              </Link>
            </td>
            <td>
              {s.debater_codes && s.debaters
                ? s.debaters.split(", ").map((name, j) => {
                    const codes = s.debater_codes!.split(", ");
                    return (
                      <span key={j}>
                        {j > 0 && ", "}
                        <Link
                          href={`/debaters/${codes[j]}`}
                          className="sr-link"
                        >
                          {name}
                        </Link>
                      </span>
                    );
                  })
                : s.debaters || "-"}
            </td>
            <td className="num">{s.prelim_wins}</td>
            <td className="num">{s.prelim_losses}</td>
            <td className="num">{s.prelim_ties || 0}</td>
            <td className="num">{formatSP(s.avg_sp)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
