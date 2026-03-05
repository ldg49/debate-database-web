export function winPct(wins: number, losses: number): string {
  const total = wins + losses;
  if (total === 0) return ".000";
  return (wins / total).toFixed(3).replace(/^0/, "");
}

export function formatRecord(wins: number, losses: number, ties?: number): string {
  if (ties && ties > 0) return `${wins}-${losses}-${ties}`;
  return `${wins}-${losses}`;
}

export function formatSP(sp: number | null): string {
  if (sp === null || sp === undefined) return "-";
  return sp.toFixed(1);
}

export function resultColor(result: string): string {
  if (result.startsWith("W")) return "text-green-700";
  if (result.startsWith("L")) return "text-red-700";
  if (result === "T" || result.startsWith("TIE")) return "text-yellow-700";
  return "";
}
