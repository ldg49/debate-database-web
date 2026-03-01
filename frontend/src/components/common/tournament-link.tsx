import Link from "next/link";

export function TournamentLink({
  id,
  children,
}: {
  id: number;
  children: React.ReactNode;
}) {
  return (
    <Link href={`/tournaments/${id}`} className="sr-link">
      {children}
    </Link>
  );
}
