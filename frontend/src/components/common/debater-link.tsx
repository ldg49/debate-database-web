import Link from "next/link";

export function DebaterLink({
  code,
  children,
}: {
  code: string;
  children: React.ReactNode;
}) {
  return (
    <Link href={`/debaters/${code}`} className="sr-link">
      {children}
    </Link>
  );
}
