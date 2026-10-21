import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link href="/" className="brand">
        Ticket<span>Hound</span>
      </Link>
      <nav className="site-nav" aria-label="Primary">
        <Link href="/games">Games</Link>
        <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
          API docs
        </a>
      </nav>
    </header>
  );
}
