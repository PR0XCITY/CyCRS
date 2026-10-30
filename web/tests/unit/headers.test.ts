import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

type Header = { key: string; value: string };
type Rule = { source: string; headers: Header[] };

const root = join(__dirname, "..", "..");
const vercel = JSON.parse(readFileSync(join(root, "vercel.json"), "utf8")) as { headers: Rule[] };
const CSP = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'";

function headersFor(source: string) {
  const r = vercel.headers.find((h) => h.source === source);
  return new Map((r?.headers ?? []).map((h) => [h.key.toLowerCase(), h.value]));
}

function directives(csp: string) {
  return csp
    .split(";")
    .map((d) => d.trim())
    .filter(Boolean)
    .sort();
}

describe("vercel.json security headers match the security policy", () => {
  const h = headersFor("/(.*)");

  it("applies to every path", () => {
    expect(h.size).toBeGreaterThan(0);
  });

  it("uses exactly the required CSP", () => {
    expect(directives(h.get("content-security-policy") ?? "")).toEqual(directives(CSP));
  });

  it("forbids framing, inline objects and foreign connections", () => {
    const csp = h.get("content-security-policy") ?? "";
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("connect-src 'self'");
    expect(csp).not.toMatch(/https?:\/\//);
    expect(csp).not.toContain("unsafe-eval");
  });

  it("sends HSTS for at least a year", () => {
    const v = h.get("strict-transport-security") ?? "";
    const age = Number(v.match(/max-age=(\d+)/)?.[1] ?? 0);
    expect(age).toBeGreaterThanOrEqual(31536000);
  });

  it("sends nosniff, the referrer policy and the permissions policy", () => {
    expect(h.get("x-content-type-options")).toBe("nosniff");
    expect(h.get("referrer-policy")).toBe("strict-origin-when-cross-origin");
    const p = h.get("permissions-policy") ?? "";
    for (const f of ["camera=()", "microphone=()", "geolocation=()"]) expect(p).toContain(f);
  });
});
