import Link from "next/link";
import ThemeToggle from "@/components/ThemeToggle";

export const NAV = [
  { href: "/", label: "Home" },
  { href: "/assess/", label: "Assess" },
  { href: "/models/", label: "How it works" },
  { href: "/data/", label: "Data" },
  { href: "/cases/", label: "Cases" },
] as const;

export default function Header() {
  return (
    <header className="border-b border-rule">
      <div className="wrap flex flex-wrap items-center justify-between gap-3 py-4">
        <Link href="/" className="display text-xl no-underline" aria-label="CyCRS home">
          CyCRS
        </Link>
        <nav aria-label="Main" className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
          {NAV.map((n) => (
            <Link key={n.href} href={n.href} className="no-underline hover:underline">
              {n.label}
            </Link>
          ))}
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
