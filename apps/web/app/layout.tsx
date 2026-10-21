import type { Metadata } from "next";
import { Barlow_Condensed, Manrope } from "next/font/google";

import { SiteHeader } from "@/components/SiteHeader";

import "./globals.css";

const display = Barlow_Condensed({
  subsets: ["latin"],
  weight: ["600", "700", "800"],
  variable: "--font-display",
});

const body = Manrope({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "TicketHound — NBA ticket discovery",
  description:
    "Find affordable NBA tickets across supported marketplaces. Phase 0 ships labeled DEMO data only.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${body.variable} antialiased`}>
        <div className="site-shell">
          <SiteHeader />
          {children}
          <p className="footer-note">
            TicketHound Phase 0 foundation — DEMO provider only. Live Ticketmaster discovery is
            Phase 1. Prices never claim to be live unless provenance says LIVE.
          </p>
        </div>
      </body>
    </html>
  );
}
