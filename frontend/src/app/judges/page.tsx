"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import type { JudgeCareer } from "@/lib/types";
import { fetchApiClient } from "@/lib/api";

export default function JudgesPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<JudgeCareer[]>([]);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
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
        const data = await fetchApiClient<JudgeCareer[]>(
          `/judges?q=${encodeURIComponent(query)}`
        );
        setResults(data);
      } catch {
        setResults([]);
      }
      setLoading(false);
    }, 300);
  }, [query]);

  function affPct(aff: number, total: number): string {
    if (total === 0) return "-";
    return ((aff / total) * 100).toFixed(1) + "%";
  }

  return (
    <div>
      <div className="breadcrumb">
        <a href="/">Home</a> &gt; Judges
      </div>
      <h1
        className="text-xl font-bold mb-3"
        style={{ color: "var(--sr-navy)" }}
      >
        Judge Search
      </h1>
      <input
        type="text"
        placeholder="Search by name (e.g., Harris, Scott Harris)..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="w-full max-w-md border border-gray-300 px-3 py-2 text-sm rounded mb-3"
        autoFocus
      />

      {loading && <p className="text-xs text-gray-400">Searching...</p>}

      {results.length > 0 && (
        <table className="sr-table" style={{ maxWidth: 800 }}>
          <thead>
            <tr>
              <th>Name</th>
              <th className="text-right">Decisions</th>
              <th className="text-right">Aff%</th>
              <th className="text-right">Tourns</th>
              <th>Active</th>
            </tr>
          </thead>
          <tbody>
            {results.map((j) => {
              const firstYear = j.first_seen
                ? new Date(j.first_seen).getFullYear()
                : "";
              const lastYear = j.last_seen
                ? new Date(j.last_seen).getFullYear()
                : "";
              const years =
                firstYear === lastYear
                  ? `${firstYear}`
                  : `${firstYear}-${lastYear}`;
              return (
                <tr
                  key={j.name}
                  className="cursor-pointer"
                  onClick={() =>
                    router.push(`/judges/${encodeURIComponent(j.name)}`)
                  }
                >
                  <td>
                    <a className="sr-link">{j.name}</a>
                  </td>
                  <td className="num">{j.total_decisions}</td>
                  <td className="num">
                    {affPct(j.aff_votes, j.total_decisions)}
                  </td>
                  <td className="num">{j.tournaments}</td>
                  <td>{years}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      {!loading && query.trim() && results.length === 0 && (
        <p className="text-sm text-gray-500">No judges found.</p>
      )}
    </div>
  );
}
