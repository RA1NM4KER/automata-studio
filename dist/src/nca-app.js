import { NeuralCA } from "./nca-engine.js";
const $ = (id) => document.getElementById(id);
let ca,
  running = false,
  last = 0,
  carry = 0,
  pollTimer;
const canvas = $("nca-art"),
  ctx = canvas.getContext("2d");
function message(text, error = false) {
  $("nca-status").textContent = text;
  $("nca-status").style.color = error ? "#ffd7c3" : "";
}
function draw() {
  if (!ca) return;
  const tile = document.createElement("canvas");
  tile.width = tile.height = ca.size;
  tile
    .getContext("2d")
    .putImageData(new ImageData(ca.rgba(), ca.size, ca.size), 0, 0);
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(tile, 0, 0, canvas.width, canvas.height);
  $("nca-generation").textContent = String(ca.generation).padStart(4, "0");
}
function play(value) {
  running = value;
  last = 0;
  carry = 0;
  $("nca-play").textContent = value ? "Pause" : "Play";
  $("nca-play").setAttribute("aria-pressed", String(value));
}
function loadModel(model) {
  if (model.format !== "automata-studio-nca-v1")
    throw Error("Not an Automata Studio NCA model.");
  ca = new NeuralCA(model);
  for (const id of ["nca-play", "nca-step", "nca-reset", "nca-export"])
    $(id).disabled = false;
  $("nca-title").textContent = (model.name || "LOADED MODEL").toUpperCase();
  message(`${model.channels} channels · target not loaded`);
  play(false);
  draw();
}
async function api(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw Error(data.error || "Local service request failed.");
  return data;
}
function base64(bytes) {
  let result = "";
  for (let i = 0; i < bytes.length; i += 32768)
    result += String.fromCharCode(...bytes.subarray(i, i + 32768));
  return btoa(result);
}
async function prepare() {
  const file = $("train-image").files[0];
  if (!file) throw Error("Choose a portrait image first.");
  if (file.size > 12_000_000) throw Error("Choose an image under 12 MB.");
  $("prepare-target").disabled = true;
  message("Preparing target locally…");
  const data = await api("/api/nca/prepare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: $("train-name").value,
      imageBase64: base64(new Uint8Array(await file.arrayBuffer())),
    }),
  });
  $("train-name").value = data.name;
  $("target-image").src = `/api/nca/target?v=${Date.now()}`;
  $("target-preview").hidden = false;
  $("start-training").disabled = false;
  $("train-message").textContent = data.message;
  $("prepare-target").disabled = false;
}
async function startTraining() {
  const steps = Math.max(
    1,
    Math.min(10000, Number($("train-steps").value) || 4000),
  );
  $("train-progress").max = steps;
  $("start-training").disabled = true;
  $("prepare-target").disabled = true;
  $("load-trained").disabled = true;
  await api("/api/nca/train", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: $("train-name").value, steps }),
  });
  poll();
}
async function poll() {
  clearTimeout(pollTimer);
  try {
    const status = await api("/api/nca/status");
    $("train-message").textContent =
      status.loss == null
        ? status.message
        : `${status.message} · loss ${status.loss.toFixed(5)}`;
    $("train-progress").value = status.step || 0;
    if (status.name && status.phase !== "idle") {
      $("train-name").value = status.name;
      $("target-image").src = `/api/nca/target?v=${Date.now()}`;
      $("target-preview").hidden = false;
    }
    if (status.phase === "training") {
      pollTimer = setTimeout(poll, 1500);
      return;
    }
    const ready = status.phase === "complete";
    $("load-trained").disabled = !ready;
    $("prepare-target").disabled = false;
    $("start-training").disabled = status.phase !== "prepared";
    if (status.phase === "error") message(status.message, true);
  } catch (error) {
    message(error.message, true);
  }
}
$("prepare-target").onclick = () =>
  prepare().catch((error) => {
    $("prepare-target").disabled = false;
    message(error.message, true);
  });
$("start-training").onclick = () =>
  startTraining().catch((error) => {
    $("start-training").disabled = false;
    $("prepare-target").disabled = false;
    message(error.message, true);
  });
$("load-trained").onclick = async () => {
  try {
    loadModel(await api("/api/nca/model"));
  } catch (error) {
    message(error.message, true);
  }
};
$("nca-file").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    loadModel(JSON.parse(await file.text()));
  } catch (error) {
    message(error.message, true);
  }
  event.target.value = "";
});
$("nca-play").onclick = () => play(!running);
$("nca-step").onclick = () => {
  play(false);
  ca.step();
  draw();
};
$("nca-reset").onclick = () => {
  play(false);
  ca.reset();
  draw();
};
$("nca-export").onclick = () => {
  const link = document.createElement("a");
  link.download = `nca-growth-g${ca.generation}.png`;
  canvas.toBlob((blob) => {
    link.href = URL.createObjectURL(blob);
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 10000);
  });
};
document.addEventListener("visibilitychange", () => {
  if (document.hidden) play(false);
});
document.addEventListener("keydown", (event) => {
  if (
    !ca ||
    event.ctrlKey ||
    event.metaKey ||
    event.altKey ||
    event.repeat ||
    event.target.closest("input,select,textarea,button,[contenteditable]")
  )
    return;
  if (event.code === "Space") {
    event.preventDefault();
    play(!running);
  }
  if (event.key.toLowerCase() === "n") {
    play(false);
    ca.step();
    draw();
  }
});
function loop(time) {
  if (running && ca) {
    if (!last) last = time;
    carry += Math.min(time - last, 150);
    last = time;
    const interval = 1000 / Number($("nca-speed").value);
    let count = Math.min(4, Math.floor(carry / interval));
    while (count--) {
      ca.step();
      carry -= interval;
    }
    draw();
  }
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
poll();
