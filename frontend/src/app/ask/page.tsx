"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/api";

interface QueryResult {
  sql: string | null;
  results: Record<string, unknown>[] | null;
  row_count: number | null;
  error: string | null;
}

export default function AskPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [showSql, setShowSql] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || loading) return;

    setLoading(true);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/ai/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question.trim() }),
      });
      const data: QueryResult = await res.json();
      setResult(data);
    } catch {
      setResult({ sql: null, results: null, row_count: null, error: "Failed to reach the API" });
    }

    setLoading(false);
  }

  const columns = result?.results?.length
    ? Object.keys(result.results[0])
    : [];

  return (
    <div>
      <div className="breadcrumb">
        <a href="/">Home</a> &gt; Ask AI
      </div>
      <h1
        className="text-xl font-bold mb-1"
        style={{ color: "var(--sr-navy)" }}
      >
        Ask the Database
      </h1>
      <p className="text-xs text-gray-500 mb-3">
        Ask a question in plain English and get results from the debate database.
      </p>

      <form onSubmit={handleSubmit} className="flex gap-2 mb-4 max-w-2xl">
        <input
          type="text"
          placeholder="e.g., Who has the most career wins?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className="flex-1 border border-gray-300 px-3 py-2 text-sm rounded"
          autoFocus
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="px-4 py-2 text-sm font-semibold text-white rounded disabled:opacity-50"
          style={{ background: "var(--sr-navy)" }}
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>

      {result?.error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2 rounded mb-3 max-w-2xl">
          {result.error}
        </div>
      )}

      {result?.sql && (
        <div className="mb-3 max-w-2xl">
          <button
            onClick={() => setShowSql(!showSql)}
            className="text-xs text-gray-500 hover:text-gray-700 underline"
          >
            {showSql ? "Hide SQL" : "Show SQL"}
          </button>
          {showSql && (
            <pre className="mt-1 bg-gray-50 border border-gray-200 text-xs p-2 rounded overflow-x-auto">
              {result.sql}
            </pre>
          )}
        </div>
      )}

      {result?.results && result.results.length > 0 && (
        <>
          <p className="text-xs text-gray-500 mb-2">
            {result.row_count} result{result.row_count !== 1 ? "s" : ""}
          </p>
          <div className="overflow-x-auto">
            <table className="sr-table" style={{ maxWidth: 1000 }}>
              <thead>
                <tr>
                  {columns.map((col) => (
                    <th key={col}>{col.replace(/_/g, " ")}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.results.map((row, i) => (
                  <tr key={i}>
                    {columns.map((col) => (
                      <td key={col} className={typeof row[col] === "number" ? "num" : ""}>
                        {row[col] == null ? "—" : String(row[col])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {result?.results && result.results.length === 0 && !result.error && (
        <p className="text-sm text-gray-500">No results found.</p>
      )}
    </div>
  );
}
