"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import type { TournamentSearchResult } from "@/lib/types";
import { fetchApiClient } from "@/lib/api";

interface PaginatedResponse {
  results: TournamentSearchResult[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export default function TournamentsPage() {
  const [query, setQuery] = useState("");
  const [season, setSeason] = useState("");
  const [seasons, setSeasons] = useState<string[]>([]);
  const [results, setResults] = useState<TournamentSearchResult[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Load seasons on mount, default to most recent
  useEffect(() => {
    (async () => {
      try {
        const data = await fetchApiClient<string[]>("/tournaments/seasons");
        setSeasons(data);
        if (data.length > 0) setSeason(data[0]);
      } catch {
        // fallback
      }
    })();
  }, []);

  // Reset to page 1 when filters change
  useEffect(() => {
    setPage(1);
  }, [query, season]);

  // Fetch tournaments when filters or page change
  useEffect(() => {
    if (!season && seasons.length === 0) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const delay = page === 1 ? 300 : 0; // no debounce on page change
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (query.trim()) params.set("q", query);
        if (season) params.set("season", season);
        params.set("page", String(page));
        const data = await fetchApiClient<PaginatedResponse>(
          `/tournaments?${params.toString()}`
        );
        setResults(data.results);
        setTotalPages(data.total_pages);
        setTotal(data.total);
      } catch {
        setResults([]);
      }
      setLoading(false);
    }, delay);
  }, [query, season, seasons, page]);

  return (
    <div>
      <div className="breadcrumb">
        <a href="/">Home</a> &gt; Tournaments
      </div>
      <h1
        className="text-xl font-bold mb-3"
        style={{ color: "var(--sr-navy)" }}
      >
        Tournament Search
      </h1>
      <div className="flex gap-2 mb-3">
        <input
          type="text"
          placeholder="Search tournaments..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 max-w-sm border border-gray-300 px-3 py-2 text-sm rounded"
          autoFocus
        />
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

      {loading && (
        <p className="text-xs text-gray-400">Loading...</p>
      )}

      {!loading && results.length > 0 && (
        <>
          <p className="text-xs text-gray-500 mb-2">
            {total} tournament{total !== 1 ? "s" : ""}
          </p>
          <table className="sr-table" style={{ maxWidth: 800 }}>
            <thead>
              <tr>
                <th>Tournament</th>
                <th>Host</th>
                <th>Season</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {results.map((t) => (
                <tr key={t.id}>
                  <td>
                    <Link href={`/tournaments/${t.id}`} className="sr-link">{t.display_name || t.name}</Link>
                  </td>
                  <td className="text-gray-500">{t.host_school || "-"}</td>
                  <td>{t.season}</td>
                  <td>{t.start_date ? new Date(t.start_date).toLocaleDateString() : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="flex items-center gap-3 mt-3">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 text-xs border border-gray-300 rounded disabled:opacity-30"
              >
                Previous
              </button>
              <span className="text-xs text-gray-600">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 text-xs border border-gray-300 rounded disabled:opacity-30"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {!loading && results.length === 0 && (
        <p className="text-sm text-gray-500">No tournaments found.</p>
      )}
    </div>
  );
}
