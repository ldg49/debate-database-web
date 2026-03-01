"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import type { TournamentSearchResult } from "@/lib/types";
import { fetchApiClient } from "@/lib/api";

export default function TournamentsPage() {
  const [query, setQuery] = useState("");
  const [season, setSeason] = useState("");
  const [seasons, setSeasons] = useState<string[]>([]);
  const [results, setResults] = useState<TournamentSearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
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

  // Fetch tournaments when filters change
  useEffect(() => {
    if (!season && seasons.length === 0) return; // wait for seasons to load
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
  }, [query, season, seasons]);

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
