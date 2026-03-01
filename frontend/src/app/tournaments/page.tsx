"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import type { TournamentSearchResult } from "@/lib/types";
import { fetchApiClient } from "@/lib/api";

export default function TournamentsPage() {
  const [query, setQuery] = useState("");
  const [season, setSeason] = useState("");
  const [results, setResults] = useState<TournamentSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (query.trim()) params.set("q", query);
        if (season) params.set("season", season);
        const data = await fetchApiClient<TournamentSearchResult[]>(
          `/tournaments?${params.toString()}`
        );
        setResults(data);
      } catch {
        setResults([]);
      }
      setLoading(false);
    }, 300);
  }, [query, season]);

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
        <input
          type="text"
          placeholder="Season (e.g., 2025-2026)"
          value={season}
          onChange={(e) => setSeason(e.target.value)}
          className="w-48 border border-gray-300 px-3 py-2 text-sm rounded"
        />
      </div>

      {loading && (
        <p className="text-xs text-gray-400">Searching...</p>
      )}

      {results.length > 0 && (
        <table className="sr-table" style={{ maxWidth: 700 }}>
          <thead>
            <tr>
              <th>Tournament</th>
              <th>Season</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {results.map((t) => (
              <tr
                key={t.id}
                className="cursor-pointer"
                onClick={() => router.push(`/tournaments/${t.id}`)}
              >
                <td>
                  <a className="sr-link">{t.name}</a>
                </td>
                <td>{t.season}</td>
                <td>{t.start_date ? new Date(t.start_date).toLocaleDateString() : "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {!loading && results.length === 0 && (
        <p className="text-sm text-gray-500">No tournaments found.</p>
      )}
    </div>
  );
}
