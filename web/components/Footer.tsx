import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-rule mt-16 no-print">
      <div className="wrap flex flex-wrap items-center justify-between gap-3 py-6 text-sm text-muted">
        <span>
          <span className="display text-ink">CyCRS</span> · Cyber Security Control Recommendation System
        </span>
        <Link href="/data/">Data sources</Link>
      </div>
    </footer>
  );
}
