import type { Metadata } from "next";
import "./globals.css";
import { Analytics } from "@vercel/analytics/next";
import { SiteHeader } from "@/components/layout/site-header";
import { SiteFooter } from "@/components/layout/site-footer";

export const metadata: Metadata = {
  title: "College Policy Debate Database",
  description:
    "Comprehensive statistics for college policy debate tournaments, debaters, and teams. Search debater records, tournament results, and speaker points from 2003 to present.",
  openGraph: {
    title: "College Policy Debate Database",
    description:
      "Search debater records, tournament results, and speaker points from 2003 to present.",
    url: "https://collegedebateresults.vercel.app",
    siteName: "College Policy Debate Database",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary",
    title: "College Policy Debate Database",
    description:
      "Search debater records, tournament results, and speaker points from 2003 to present.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen flex flex-col">
        <SiteHeader />
        <main className="flex-1 max-w-[1200px] w-full mx-auto px-4 py-4">
          {children}
        </main>
        <SiteFooter />
        <Analytics />
      </body>
    </html>
  );
}
