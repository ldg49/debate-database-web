import type { SeasonSummary, DebaterCareer } from "@/lib/types";
import { winPct, formatSP } from "@/lib/utils";

export function CareerSummary({
  seasons,
  career,
}: {
  seasons: SeasonSummary[];
  career: DebaterCareer;
}) {
  return (
    <div>
      <div className="section-header">Career Summary</div>
      <table className="sr-table mt-1">
        <thead>
          <tr>
            <th>Season</th>
            <th>School</th>
            <th>Partners</th>
            <th className="text-right">W</th>
            <th className="text-right">L</th>
            <th className="text-right">Pct</th>
            <th className="text-right">SP</th>
          </tr>
        </thead>
        <tbody>
          {seasons.map((s, i) => (
            <tr key={i}>
              <td>{s.season}</td>
              <td>{s.school}</td>
              <td>{s.partners || "-"}</td>
              <td className="num">{s.wins}</td>
              <td className="num">{s.losses}</td>
              <td className="num">{winPct(s.wins, s.losses)}</td>
              <td className="num">{formatSP(s.avg_sp)}</td>
            </tr>
          ))}
          <tr className="total-row">
            <td>Career</td>
            <td></td>
            <td></td>
            <td className="num">{career.total_wins}</td>
            <td className="num">{career.total_losses}</td>
            <td className="num">
              {winPct(career.total_wins, career.total_losses)}
            </td>
            <td className="num">{formatSP(career.avg_speaker_points)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
