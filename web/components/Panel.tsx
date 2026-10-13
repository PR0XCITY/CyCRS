import Link from "next/link";

type Props = { title?: string; learn: { href: string; label: string }[]; children: React.ReactNode; testId?: string };

export default function Panel({ title = "How this was calculated", learn, children, testId }: Props) {
  return (
    <details className="mt-4 panel group" data-testid={testId}>
      <summary className="cursor-pointer select-none px-4 py-3 text-sm font-medium flex items-center justify-between gap-3">
        <span>{title}</span>
        <span aria-hidden="true" className="num text-muted group-open:rotate-45 transition-transform">
          +
        </span>
      </summary>
      <div className="px-4 pb-4 text-sm">
        {children}
        <p className="mt-4 pt-3 border-t border-rule flex flex-wrap gap-x-4 gap-y-1">
          <span className="label">Learn the model</span>
          {learn.map((l) => (
            <Link key={l.href} href={l.href} className="underline">
              {l.label}
            </Link>
          ))}
        </p>
      </div>
    </details>
  );
}
