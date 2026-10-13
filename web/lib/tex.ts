import katex from "katex";

export function renderTex(tex: string, display = true) {
  if (typeof window !== "undefined" && !process.env.VITEST) throw new Error("KaTeX renders at build time only");
  return katex.renderToString(tex, { displayMode: display, throwOnError: false, output: "html", strict: "ignore", trust: false });
}
