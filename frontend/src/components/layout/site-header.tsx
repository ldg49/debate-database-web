import Link from "next/link";

export function SiteHeader() {
  return (
    <header style={{ background: "var(--sr-navy)" }}>
      <div className="max-w-[1200px] mx-auto px-4 flex items-center justify-between h-10">
        <Link
          href="/"
          className="text-white font-bold text-sm tracking-wide no-underline"
        >
          College Debate Results
        </Link>
        <nav className="flex gap-6">
          {[
            { href: "/", label: "Home" },
            { href: "/debaters", label: "Debaters" },
            { href: "/tournaments", label: "Tournaments" },
            { href: "/judges", label: "Judges" },
            { href: "/data-gaps", label: "Data Gaps" },
            { href: "/ask", label: "Ask the Database" },
          ].map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-white/80 hover:text-white text-xs font-semibold no-underline uppercase tracking-wider"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
