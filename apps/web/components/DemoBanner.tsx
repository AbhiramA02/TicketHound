export function DemoBanner({ warning }: { warning?: string | null }) {
  return (
    <div
      role="status"
      className="demo-banner"
      aria-live="polite"
    >
      <span className="demo-banner__tag">DEMO DATA</span>
      <span>
        {warning ??
          "Synthetic demonstration listings — not live marketplace prices and not purchasable."}
      </span>
    </div>
  );
}
