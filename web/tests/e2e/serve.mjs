import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { createGzip } from "node:zlib";
import { basename, dirname, extname, join, normalize } from "node:path";

const root = join(process.cwd(), "out");
const types = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml", ".woff2": "font/woff2", ".png": "image/png", ".txt": "text/plain", ".ico": "image/x-icon" };

function windowsSegmentPath(f) {
  const d = dirname(f);
  const b = basename(f);
  if (!b.startsWith("__next.") || !b.endsWith(".txt")) return null;
  const parts = b.slice("__next.".length, -".txt".length).split(".");
  if (parts.length < 2) return null;
  return join(d, `__next.${parts[0]}`, ...parts.slice(1, -1), `${parts[parts.length - 1]}.txt`);
}

function resolvePath(url) {
  const p = normalize(decodeURIComponent(url.split("?")[0])).replace(/^(\.\.[/\\])+/, "");
  let f = join(root, p);
  if (existsSync(f) && statSync(f).isDirectory()) f = join(f, "index.html");
  if (existsSync(f)) return f;
  const w = windowsSegmentPath(f);
  return w && existsSync(w) ? w : null;
}

function handle(req, res) {
  const f = resolvePath(req.url);
  if (!f) {
    res.writeHead(404, { "content-type": "text/html" });
    createReadStream(join(root, "404.html")).pipe(res);
    return;
  }
  const t = types[extname(f)] || "application/octet-stream";
  if (/gzip/.test(req.headers["accept-encoding"] || "") && /text|javascript|json|svg/.test(t)) {
    res.writeHead(200, { "content-type": t, "content-encoding": "gzip" });
    createReadStream(f).pipe(createGzip()).pipe(res);
    return;
  }
  res.writeHead(200, { "content-type": t });
  createReadStream(f).pipe(res);
}

createServer(handle).listen(4173, "127.0.0.1");
