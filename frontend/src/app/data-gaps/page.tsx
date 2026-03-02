"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import type { DataGapsResponse, DataGapTournament } from "@/lib/types";
import { fetchApiClient } from "@/lib/api";

const GAP_LABELS: Record<string, string> = {
  no_results: "No Results",
  missing_elims: "Missing Elims",
  missing_prelims: "Missing Prelims",
  missing_speaker_points: "Missing Speaker Points",
  missing_names: "Missing Names",
  known_issues: "Known Issues",
};

const GAP_SEVERITY: Record<string, string> = {
  no_results: "severity-high",
  missing_elims: "severity-medium",
  missing_prelims: "severity-medium",
  missing_speaker_points: "severity-medium",
  missing_names: "severity-low",
  known_issues: "severity-low",
};

type GapCategory = keyof typeof GAP_LABELS | "all";

export default function DataGapsPage() {
  const [season, setSeason] = useState("");
  const [seasons, setSeasons] = useState<string[]>([]);
  const [data, setData] = useState<DataGapsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<GapCategory>("all");

  useEffect(() => {
    (async () => {
      try {
        const s = await fetchApiClient<string[]>("/tournaments/seasons");
        setSeasons(s);
      } catch {
        // fallback
      }
    })();
  }, []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const params = season ? `?season=${encodeURIComponent(season)}` : "";
        const resp = await fetchApiClient<DataGapsResponse>(
          `/data-gaps${params}`
        );
        setData(resp);
      } catch {
        setData(null);
      }
      setLoading(false);
    })();
  }, [season]);

  const filtered: DataGapTournament[] = data
    ? filter === "all"
      ? data.tournaments
      : data.tournaments.filter((t) => t.gaps.includes(filter))
    : [];

  const summaryCards: { key: GapCategory; label: string; count: number }[] =
    data
      ? [
          { key: "all", label: "All Gaps", count: data.tournaments.length },
          { key: "no_results", label: "No Results", count: data.summary.no_results },
          { key: "missing_elims", label: "Missing Elims", count: data.summary.missing_elims },
          { key: "missing_prelims", label: "Missing Prelims", count: data.summary.missing_prelims },
          { key: "missing_speaker_points", label: "Missing SP", count: data.summary.missing_speaker_points },
          { key: "missing_names", label: "Missing Names", count: data.summary.missing_names },
          { key: "known_issues", label: "Known Issues", count: data.summary.known_issues },
        ]
      : [];

  return (
    <div>
      <div className="breadcrumb">
        <a href="/">Home</a> &gt; Data Gaps
      </div>
      <h1
        className="text-xl font-bold mb-1"
        style={{ color: "var(--sr-navy)" }}
      >
        Data Gaps
      </h1>
      <p className="text-xs text-gray-600 mb-3">
        Tournaments with missing or incomplete data. Help us fill in the gaps!
      </p>

      <div className="flex gap-2 mb-4">
        <select
          value={season}
          onChange={(e) => setSeason(e.target.value)}
          className="w-48 border border-gray-300 px-3 py-2 text-sm rounded bg-white"
        >
          <option value="">All seasons</option>
          {seasons.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {loading && <p className="text-xs text-gray-400">Loading...</p>}

      {!loading && data && (
        <>
          <div className="flex flex-wrap gap-2 mb-4">
            {summaryCards.map((c) => (
              <button
                key={c.key}
                onClick={() => setFilter(c.key)}
                className={`gap-filter-btn ${filter === c.key ? "active" : ""}`}
              >
                {c.label} ({c.count})
              </button>
            ))}
          </div>

          <p className="text-xs text-gray-500 mb-2">
            {filtered.length} tournament{filtered.length !== 1 ? "s" : ""}
          </p>

          {filtered.length > 0 ? (
            <table className="sr-table">
              <thead>
                <tr>
                  <th>Tournament</th>
                  <th>Season</th>
                  <th>Date</th>
                  <th className="text-right">Debates</th>
                  <th>Gaps</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((t) => (
                  <tr key={t.id}>
                    <td>
                      <Link
                        href={`/tournaments/${t.id}`}
                        className="sr-link"
                      >
                        {t.name}
                      </Link>
                    </td>
                    <td>{t.season}</td>
                    <td>
                      {t.start_date
                        ? new Date(t.start_date + "T00:00:00").toLocaleDateString()
                        : "-"}
                    </td>
                    <td className="num">{t.total_debates}</td>
                    <td>
                      {t.gaps.map((g) => (
                        <span
                          key={g}
                          className={`gap-badge ${GAP_SEVERITY[g] || "severity-low"}`}
                        >
                          {GAP_LABELS[g] || g}
                        </span>
                      ))}
                    </td>
                    <td className="text-xs text-gray-500">
                      {gapDetails(t)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-sm text-gray-500">
              No tournaments with gaps in this category.
            </p>
          )}
        </>
      )}
    </div>
  );
}

function gapDetails(t: DataGapTournament): string {
  const parts: string[] = [];
  if (t.gaps.includes("no_results")) {
    parts.push("0 debates");
  } else {
    if (t.gaps.includes("missing_speaker_points") && t.sp_coverage_pct !== null) {
      parts.push(`SP: ${t.sp_coverage_pct}%`);
    }
    if (t.gaps.includes("missing_elims")) {
      parts.push(`${t.prelim_debates} prelims, 0 elims`);
    }
    if (t.gaps.includes("missing_prelims")) {
      parts.push(`0 prelims, ${t.elim_debates} elims`);
    }
  }
  if (t.gaps.includes("missing_names")) {
    parts.push(`${t.missing_names} unnamed`);
  }
  if (t.gaps.includes("known_issues")) {
    if (t.issue_notes && t.issue_notes.length > 0) {
      parts.push(t.issue_notes.join("; "));
    } else {
      parts.push(`${t.known_issues} issue${t.known_issues !== 1 ? "s" : ""}`);
    }
  }
  return parts.join(" | ");
}
