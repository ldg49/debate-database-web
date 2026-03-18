import { fetchApi } from "@/lib/api";
import { StatCard } from "@/components/common/stat-card";
import type { OverviewStats } from "@/lib/types";
import Link from "next/link";

export default async function Home() {
  let stats: OverviewStats | null = null;
  try {
    stats = await fetchApi<OverviewStats>("/stats/overview");
  } catch {
    // API may not be available during build
  }

  return (
    <div>
      <h1
        className="text-xl font-bold mb-2"
        style={{ color: "var(--sr-navy)" }}
      >
        College Policy Debate Database
      </h1>
      <p className="text-sm text-gray-600 mb-4">
        Comprehensive statistics for varsity policy debate tournaments across the
        country. Look up any debater&apos;s career record, browse tournament results,
        and explore team performance.
      </p>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <StatCard label="Tournaments" value={stats.tournaments} />
          <StatCard label="Debaters" value={stats.debaters} />
          <StatCard label="Debates" value={stats.debates} />
          <StatCard label="Team Entries" value={stats.teams} />
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-4">
        <Link
          href="/debaters"
          className="block p-4 border border-gray-200 rounded hover:border-blue-300 no-underline"
        >
          <h2
            className="text-sm font-bold mb-1"
            style={{ color: "var(--sr-navy)" }}
          >
            Debater Lookup
          </h2>
          <p className="text-xs text-gray-600">
            Search for any debater and view their career record with
            season-by-season and round-by-round detail.
          </p>
        </Link>
        <Link
          href="/tournaments"
          className="block p-4 border border-gray-200 rounded hover:border-blue-300 no-underline"
        >
          <h2
            className="text-sm font-bold mb-1"
            style={{ color: "var(--sr-navy)" }}
          >
            Tournament Lookup
          </h2>
          <p className="text-xs text-gray-600">
            Browse results from specific tournaments including standings, elim
            brackets, and round-by-round pairings.
          </p>
        </Link>
        <Link
          href="/ask"
          className="block p-4 border border-gray-200 rounded hover:border-blue-300 no-underline"
        >
          <h2
            className="text-sm font-bold mb-1"
            style={{ color: "var(--sr-navy)" }}
          >
            Ask the Database
          </h2>
          <p className="text-xs text-gray-600">
            Ask questions in plain English and get answers powered by AI.
          </p>
        </Link>
        <Link
          href="/data-gaps"
          className="block p-4 border border-gray-200 rounded hover:border-blue-300 no-underline"
        >
          <h2
            className="text-sm font-bold mb-1"
            style={{ color: "var(--sr-navy)" }}
          >
            Data Gaps
          </h2>
          <p className="text-xs text-gray-600">
            See which tournaments have missing or incomplete data and help
            fill in the gaps.
          </p>
        </Link>
      </div>
    </div>
  );
}
