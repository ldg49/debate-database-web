import type { DebaterCareer, SeasonSummary } from "@/lib/types";
import { formatRecord, winPct, formatSP } from "@/lib/utils";

export function DebaterHeader({
  career,
  seasons,
}: {
  career: DebaterCareer;
  seasons: SeasonSummary[];
}) {
  const schools = [...new Set(seasons.map((s) => s.school))];
  const seasonYears = seasons.map((s) => s.season);
  const firstYear = seasonYears.length > 0 ? seasonYears[0] : "";
  const lastYear =
    seasonYears.length > 0 ? seasonYears[seasonYears.length - 1] : "";
  const yearRange = firstYear === lastYear ? firstYear : `${firstYear}-${lastYear}`;

  return (
    <div className="mb-4">
      <div className="breadcrumb">
        <a href="/">Home</a> &gt; <a href="/debaters">Debaters</a> &gt;{" "}
        {career.first_name} {career.last_name}
      </div>
      <h1 className="text-2xl font-bold mt-1" style={{ color: "var(--sr-navy)" }}>
        {career.first_name} {career.last_name}
      </h1>
      <div className="text-sm text-gray-600 mt-1">
        {schools.join(", ")} | {yearRange}
      </div>
      <div className="text-sm mt-1 font-semibold">
        {formatRecord(career.total_wins, career.total_losses)} (
        {winPct(career.total_wins, career.total_losses)}) |{" "}
        {formatSP(career.avg_speaker_points)} avg SP |{" "}
        {career.tournaments_attended} tournaments
      </div>
    </div>
  );
}
