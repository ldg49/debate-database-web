import { fetchApi } from "@/lib/api";
import type {
  DebaterCareer,
  SeasonSummary,
  PartnerRecord,
  TournamentEntry,
} from "@/lib/types";
import { DebaterHeader } from "@/components/debater/debater-header";
import { CareerSummary } from "@/components/debater/career-summary";
import { PartnerHistory } from "@/components/debater/partner-history";
import { TournamentLog } from "@/components/debater/tournament-log";

export default async function DebaterPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = await params;

  const [career, seasons, partners, tournaments] = await Promise.all([
    fetchApi<DebaterCareer>(`/debaters/${code}`),
    fetchApi<SeasonSummary[]>(`/debaters/${code}/season-summary`),
    fetchApi<PartnerRecord[]>(`/debaters/${code}/partners`),
    fetchApi<TournamentEntry[]>(`/debaters/${code}/tournaments`),
  ]);

  if ("error" in career) {
    return (
      <div>
        <div className="breadcrumb">
          <a href="/">Home</a> &gt; <a href="/debaters">Debaters</a> &gt; Not
          Found
        </div>
        <h1 className="text-xl font-bold mt-2">Debater not found</h1>
        <p className="text-sm text-gray-500 mt-1">
          No debater with code &quot;{code}&quot; exists in the database.
        </p>
      </div>
    );
  }

  return (
    <div>
      <DebaterHeader career={career} seasons={seasons} />
      <CareerSummary seasons={seasons} career={career} />
      <PartnerHistory partners={partners} />
      <TournamentLog tournaments={tournaments} code={code} />
    </div>
  );
}
