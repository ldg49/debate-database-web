"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import type { DebaterCareer } from "@/lib/types";
import { fetchApiClient } from "@/lib/api";
import { winPct, formatSP } from "@/lib/utils";

export default function DebatersPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<DebaterCareer[]>([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query.trim()) {
      setResults([]);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await fetchApiClient<DebaterCareer[]>(
          `/debaters?q=${encodeURIComponent(query)}`
        );
        setResults(data);
      } catch {
        setResults([]);
      }
      setLoading(false);
    }, 300);
  }, [query]);

  return (
    <div>
      <div className="breadcrumb">
        <a href="/">Home</a> &gt; Debaters
      </div>
      <h1
        className="text-xl font-bold mb-3"
        style={{ color: "var(--sr-navy)" }}
      >
        Debater Search
      </h1>
      <input
        type="text"
        placeholder="Search by name (e.g., King, Brooklyn, BKING)..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="w-full max-w-md border border-gray-300 px-3 py-2 text-sm rounded mb-3"
        autoFocus
      />

      {loading && (
        <p className="text-xs text-gray-400">Searching...</p>
      )}

      {results.length > 0 && (
        <table className="sr-table" style={{ maxWidth: 800 }}>
          <thead>
            <tr>
              <th>Name</th>
              <th className="text-right">W</th>
              <th className="text-right">L</th>
              <th className="text-right">Pct</th>
              <th className="text-right">SP</th>
              <th className="text-right">Tourns</th>
            </tr>
          </thead>
          <tbody>
            {results.map((d) => (
              <tr key={d.debater_code}>
                <td>
                  <Link href={`/debaters/${d.debater_code}`} className="sr-link">
                    {d.last_name}, {d.first_name}
                  </Link>
                </td>
                <td className="num">{d.total_wins}</td>
                <td className="num">{d.total_losses}</td>
                <td className="num">{winPct(d.total_wins, d.total_losses)}</td>
                <td className="num">{formatSP(d.avg_speaker_points)}</td>
                <td className="num">{d.tournaments_attended}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {!loading && query.trim() && results.length === 0 && (
        <p className="text-sm text-gray-500">No debaters found.</p>
      )}
    </div>
  );
}
