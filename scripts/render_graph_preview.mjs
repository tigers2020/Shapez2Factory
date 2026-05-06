import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");
const staticRoot = path.join(repoRoot, "django_apps", "web", "static", "web");
const htmlPath = path.join(staticRoot, "graph-preview-render.html");

function parseArgs(argv) {
  const out = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) continue;
    out[token.slice(2)] = argv[index + 1];
    index += 1;
  }
  return out;
}

function contentTypeFor(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".html") return "text/html; charset=utf-8";
  if (ext === ".js" || ext === ".mjs") return "application/javascript; charset=utf-8";
  if (ext === ".json") return "application/json; charset=utf-8";
  if (ext === ".css") return "text/css; charset=utf-8";
  if (ext === ".bin") return "application/octet-stream";
  if (ext === ".gltf") return "model/gltf+json; charset=utf-8";
  if (ext === ".png") return "image/png";
  return "application/octet-stream";
}

function isWithin(basePath, candidatePath) {
  const relative = path.relative(basePath, candidatePath);
  return relative && !relative.startsWith("..") && !path.isAbsolute(relative);
}

async function startServer(sceneJson) {
  const html = await readFile(htmlPath);
  const scenePayload = JSON.stringify(sceneJson);
  const server = createServer(async (req, res) => {
    try {
      if (!req.url) {
        res.writeHead(404).end();
        return;
      }
      const requestUrl = new URL(req.url, "http://127.0.0.1");
      if (requestUrl.pathname === "/") {
        res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
        res.end(html);
        return;
      }
      if (requestUrl.pathname === "/scene.json") {
        res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
        res.end(scenePayload);
        return;
      }

      const relativePath = requestUrl.pathname.replace(/^\/+/, "");
      const targetPath = path.normalize(path.join(staticRoot, relativePath));
      if (!isWithin(staticRoot, targetPath) || targetPath.endsWith("scene.json")) {
        res.writeHead(404).end();
        return;
      }

      const body = await readFile(targetPath);
      res.writeHead(200, { "Content-Type": contentTypeFor(targetPath) });
      res.end(body);
    } catch (error) {
      res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      res.end(String(error));
    }
  });

  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  if (!address || typeof address === "string") {
    throw new Error("Could not resolve prerender server address.");
  }
  return {
    close: () => new Promise((resolve, reject) => server.close((err) => (err ? reject(err) : resolve()))),
    origin: `http://127.0.0.1:${address.port}`,
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args["scene-file"] || !args.out) {
    throw new Error("Expected --scene-file <path> and --out <path>.");
  }

  const sceneJson = JSON.parse(await readFile(path.resolve(args["scene-file"]), "utf-8"));
  const outputPath = path.resolve(args.out);
  const server = await startServer(sceneJson);
  const browser = await chromium.launch({ headless: true });

  try {
    // Viewport fits graph-preview-render.html; 512×512 CSS preview → 512px PNG (deviceScaleFactor 1).
    const page = await browser.newPage({ viewport: { width: 800, height: 800 }, deviceScaleFactor: 1 });
    await page.goto(`${server.origin}/`, { waitUntil: "networkidle" });
    await page.waitForSelector('[data-prerender-ready="true"]', { timeout: 20000 });
    await page.waitForTimeout(250);
    const preview = page.locator("[data-prerender-viewport]");
    await preview.screenshot({ path: outputPath });
  } finally {
    await browser.close();
    await server.close();
  }
}

await main();
