import { createServer } from "node:http";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { resolve, extname, sep, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const root = fileURLToPath(new URL("../dist/", import.meta.url));
const project = fileURLToPath(new URL("../", import.meta.url));
const localRuns = resolve(project, "nca-runs");
const port = Number(process.env.PORT || 4173);
const host = process.env.HOST || "127.0.0.1";
const mime = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".json": "application/json",
};
let training = {
  phase: "idle",
  name: null,
  step: null,
  loss: null,
  message: "Choose an image to begin.",
};

function json(response, code, value) {
  response.writeHead(code, {
    "Content-Type": "application/json",
    "Cache-Control": "no-store",
  });
  response.end(JSON.stringify(value));
}
function body(request) {
  return new Promise((resolveBody, reject) => {
    const chunks = [];
    let size = 0;
    request.on("data", (chunk) => {
      size += chunk.length;
      if (size > 20_000_000) {
        reject(new Error("Request exceeds 20 MB."));
        request.destroy();
      } else chunks.push(chunk);
    });
    request.on("end", () => {
      try {
        resolveBody(JSON.parse(Buffer.concat(chunks).toString("utf8")));
      } catch {
        reject(new Error("Invalid JSON request."));
      }
    });
    request.on("error", reject);
  });
}
function safeName(value) {
  const name = String(value || "portrait")
    .toLowerCase()
    .replace(/[^a-z0-9_-]/g, "-")
    .replace(/-+/g, "-")
    .slice(0, 48);
  if (!name) throw new Error("Enter a run name.");
  return name;
}
function runPython(args, onLine) {
  return new Promise((resolveRun, reject) => {
    const child = spawn(resolve(project, ".nca-venv/bin/python"), args, {
      cwd: project,
    });
    let pending = "";
    child.stdout.on("data", (data) => {
      pending += data;
      const lines = pending.split("\n");
      pending = lines.pop();
      for (const line of lines) onLine?.(line);
    });
    child.stderr.on("data", (data) => {
      training.message =
        data.toString().trim().split("\n").at(-1) || training.message;
    });
    child.on("error", reject);
    child.on("exit", (code) =>
      code === 0
        ? resolveRun()
        : reject(new Error(`Training process exited with code ${code}.`)),
    );
  });
}

async function api(request, response, path) {
  if (path === "/api/nca/status" && request.method === "GET")
    return json(response, 200, training);
  if (path === "/api/nca/target" && request.method === "GET") {
    if (!training.name)
      return json(response, 404, { error: "No prepared target." });
    const data = await readFile(
      resolve(project, "nca-inputs", `${training.name}.png`),
    );
    response.writeHead(200, {
      "Content-Type": "image/png",
      "Cache-Control": "no-store",
    });
    return response.end(data);
  }
  if (path === "/api/nca/model" && request.method === "GET") {
    if (!training.name)
      return json(response, 404, { error: "No trained model." });
    const data = await readFile(
      resolve(project, "nca-runs", training.name, "model.json"),
    );
    response.writeHead(200, {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
    });
    return response.end(data);
  }
  if (path === "/api/nca/prepare" && request.method === "POST") {
    if (training.phase === "training")
      return json(response, 409, { error: "Training is already running." });
    const input = await body(request),
      name = safeName(input.name),
      bytes = Buffer.from(String(input.imageBase64 || ""), "base64");
    if (!bytes.length || bytes.length > 12_000_000)
      return json(response, 400, { error: "Choose an image under 12 MB." });
    const source = resolve(project, "nca-inputs", `${name}-source`);
    await mkdir(dirname(source), { recursive: true });
    await writeFile(source, bytes);
    training = {
      phase: "preparing",
      name,
      step: null,
      loss: null,
      message: "Preparing the exact 64 × 64 target.",
    };
    await runPython([
      "nca/prepare_target.py",
      "--input",
      source,
      "--name",
      name,
      "--circle-mask",
      "--zoom",
      "2",
      "--center-y",
      ".37",
      "--margin",
      "8",
      "--posterize-bits",
      "3",
      "--contrast",
      "1.6",
      "--sharpness",
      "2",
    ]);
    training = {
      phase: "prepared",
      name,
      step: null,
      loss: null,
      message: "Target ready. Inspect it before training.",
    };
    return json(response, 200, training);
  }
  if (path === "/api/nca/train" && request.method === "POST") {
    if (training.phase === "training")
      return json(response, 409, { error: "Training is already running." });
    const input = await body(request),
      name = safeName(input.name || training.name),
      steps = Math.max(1, Math.min(10000, Number(input.steps) || 4000));
    await readFile(resolve(project, "nca-inputs", `${name}.png`));
    training = {
      phase: "training",
      name,
      step: 0,
      loss: null,
      message: `Training 0 / ${steps}`,
    };
    runPython(
      [
        "nca/train.py",
        "--target",
        `nca-inputs/${name}.png`,
        "--run",
        name,
        "--steps",
        String(steps),
        "--batch",
        "4",
        "--pool",
        "64",
        "--padding",
        "0",
        "--mode",
        "grow",
      ],
      (line) => {
        try {
          const event = JSON.parse(line);
          training = {
            ...training,
            step: event.step,
            loss: event.loss,
            message: `Training ${event.step} / ${steps}`,
          };
        } catch {}
      },
    )
      .then(() => {
        training = {
          ...training,
          phase: "complete",
          message: "Training complete. Load the learned weights.",
        };
      })
      .catch((error) => {
        training = { ...training, phase: "error", message: error.message };
      });
    return json(response, 202, training);
  }
  return false;
}

const server = createServer(async (request, response) => {
  const path = (() => {
    try {
      return decodeURIComponent(
        new URL(request.url, "http://localhost").pathname,
      );
    } catch {
      return null;
    }
  })();
  if (path?.startsWith("/api/nca/")) {
    try {
      const handled = await api(request, response, path);
      if (handled !== false) return;
      json(response, 404, { error: "Not found" });
    } catch (error) {
      json(response, 400, { error: error.message });
    }
    return;
  }
  if (!["GET", "HEAD"].includes(request.method)) {
    response.writeHead(405, { Allow: "GET, HEAD" });
    response.end();
    return;
  }
  try {
    if (path === null) throw new URIError();
    const localMatch =
      /^\/local-runs\/(kefas-sigil|pickle-rick-ca|pickle-rat-ca|falcon-ca)\/([a-z0-9-]+\.png)$/.exec(
        path,
      );
    if (localMatch) {
      const target = resolve(localRuns, localMatch[1], localMatch[2]);
      const content = await readFile(target);
      response.writeHead(200, {
        "Content-Type": "image/png",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
      });
      response.end(request.method === "HEAD" ? undefined : content);
      return;
    }
    const target = resolve(root, `.${path === "/" ? "/index.html" : path}`);
    if (!target.startsWith(root.endsWith(sep) ? root : root + sep)) {
      response.writeHead(403);
      response.end("Forbidden");
      return;
    }
    const content = await readFile(target);
    response.writeHead(200, {
      "Content-Type": mime[extname(target)] || "application/octet-stream",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    });
    response.end(request.method === "HEAD" ? undefined : content);
  } catch (error) {
    response.writeHead(error instanceof URIError ? 400 : 404);
    response.end(error instanceof URIError ? "Bad request" : "Not found");
  }
});
server.listen(port, host, () =>
  console.log(`Automata Studio: http://${host}:${port}\nPress Ctrl+C to stop.`),
);
server.on("error", (error) => {
  console.error(
    error.code === "EADDRINUSE"
      ? `Port ${port} is in use. Set PORT to another number and try again.`
      : error.message,
  );
  process.exitCode = 1;
});
