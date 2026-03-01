import type { ElimResult } from "@/lib/types";
import Link from "next/link";

export function ElimResults({
  results,
  tournamentId,
}: {
  results: ElimResult[];
  tournamentId: number;
}) {
  if (results.length === 0) {
    return <p className="text-sm text-gray-500">No elim results available.</p>;
  }

  // Group by round
  const grouped: Record<string, ElimResult[]> = {};
  for (const r of results) {
    const key = r.round_name;
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(r);
  }

  return (
    <div>
      {Object.entries(grouped).map(([roundName, debates]) => (
        <div key={roundName} className="mb-4">
          <h3
            className="text-sm font-bold py-1 px-2"
            style={{ background: "var(--sr-row-alt)" }}
          >
            {roundName}
          </h3>
          <table className="sr-table">
            <thead>
              <tr>
                <th>Aff</th>
                <th>Neg</th>
                <th>Judges</th>
                <th>Decision</th>
              </tr>
            </thead>
            <tbody>
              {debates.map((d, i) => (
                <tr key={i}>
                  <td>
                    <Link
                      href={`/tournaments/${tournamentId}?team=${d.aff_team_id}`}
                      className="sr-link"
                    >
                      {d.aff_team}
                    </Link>
                  </td>
                  <td>
                    {d.neg_team_id ? (
                      <Link
                        href={`/tournaments/${tournamentId}?team=${d.neg_team_id}`}
                        className="sr-link"
                      >
                        {d.neg_team}
                      </Link>
                    ) : (
                      d.neg_team
                    )}
                  </td>
                  <td>{d.judges || "-"}</td>
                  <td>
                    <span
                      className={
                        d.decision?.includes("AFF")
                          ? "result-w"
                          : d.decision?.includes("NEG")
                          ? "result-l"
                          : ""
                      }
                    >
                      {d.decision}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
