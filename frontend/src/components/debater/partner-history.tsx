import type { PartnerRecord } from "@/lib/types";
import { winPct } from "@/lib/utils";
import { DebaterLink } from "@/components/common/debater-link";

export function PartnerHistory({ partners }: { partners: PartnerRecord[] }) {
  if (partners.length === 0) return null;

  return (
    <div>
      <div className="section-header">Partner History</div>
      <table className="sr-table mt-1">
        <thead>
          <tr>
            <th>Partner</th>
            <th>School</th>
            <th className="text-right">W</th>
            <th className="text-right">L</th>
            <th className="text-right">T</th>
            <th className="text-right">Pct</th>
            <th className="text-right">Tourns</th>
          </tr>
        </thead>
        <tbody>
          {partners.map((p, i) => (
            <tr key={i}>
              <td>
                <DebaterLink code={p.partner_code}>{p.partner_name}</DebaterLink>
              </td>
              <td>{p.school}</td>
              <td className="num">{p.wins}</td>
              <td className="num">{p.losses}</td>
              <td className="num">{p.ties || 0}</td>
              <td className="num">{winPct(p.wins, p.losses)}</td>
              <td className="num">{p.tournaments}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
