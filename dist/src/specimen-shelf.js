const players = [];

for (const card of document.querySelectorAll("[data-specimen]")) {
  const image = card.querySelector("[data-specimen-image]");
  const open = card.querySelector("[data-specimen-open]");
  const play = card.querySelector("[data-specimen-play]");
  const readout = card.querySelector("[data-specimen-generation]");
  const buttons = [...card.querySelectorAll(".generation-picker button")];
  const first = Number(card.dataset.firstGeneration);
  const last = Number(card.dataset.lastGeneration);
  let current = Number(
    buttons.find((button) => button.getAttribute("aria-pressed") === "true")
      ?.dataset.generation ?? first,
  );
  let timer = null;

  function source(generation) {
    return `${card.dataset.framePrefix}${String(generation).padStart(2, "0")}.png`;
  }

  function show(generation) {
    current = generation;
    image.src = source(generation);
    image.alt = image.alt.replace(/generation \d+/, `generation ${generation}`);
    open.href = image.src;
    readout.textContent = `Generation ${generation}`;
    buttons.forEach((button) =>
      button.setAttribute(
        "aria-pressed",
        String(Number(button.dataset.generation) === generation),
      ),
    );
  }

  function stop(label = "Watch growth") {
    clearInterval(timer);
    timer = null;
    play.textContent = label;
    play.setAttribute("aria-pressed", "false");
  }

  function start() {
    show(first);
    play.textContent = "Pause growth";
    play.setAttribute("aria-pressed", "true");
    timer = setInterval(() => {
      const next = current + 1;
      show(next);
      if (next >= last) {
        stop("Watch again");
      }
    }, 900);
  }

  buttons.forEach((button) => {
    button.setAttribute(
      "aria-pressed",
      String(button.getAttribute("aria-pressed") === "true"),
    );
    button.addEventListener("click", () => {
      stop();
      show(Number(button.dataset.generation));
    });
  });

  play.setAttribute("aria-pressed", "false");
  play.addEventListener("click", () => (timer ? stop() : start()));
  image.addEventListener("error", () => {
    stop();
    card.classList.add("missing");
    image.alt = "This local specimen has not been generated yet.";
  });
  image.addEventListener("load", () => card.classList.remove("missing"));
  players.push(() => stop());
}

document.addEventListener("visibilitychange", () => {
  if (document.hidden) players.forEach((pause) => pause());
});
