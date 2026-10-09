# Working on Automata Studio

## User and intent

Kefas is a software developer who enjoyed university automata theory and wants to make ambitious, beautiful things with it. The immediate goal is a genuinely automata-generated **static GitHub avatar**. The wider interest is cellular automata, artificial life and discovering simple rules with interesting behaviour.

Do not infer a request to deploy, upload personal images or connect accounts. Read `README.md` before substantial work. When available, also read the local-only `docs/CONTEXT.md` and `docs/HANDOFF.md` for experiment history.

## Non-negotiable implementation facts

- All generated artwork must actually come from the implemented automaton. Do not substitute generated imagery, prerecorded animation, a static illustration or an unrelated visual effect while describing it as CA output.
- The engine in `dist/src/engine.js` has no DOM dependency. Keep simulation, rendering and application controls separate.
- Updates are synchronous and double-buffered. Each cell reads only the previous generation.
- The domain is a 151 × 151 grid with a fixed empty exterior. Hexagonal geometry uses odd-row offset coordinates. Preserve the documented neighbourhood.
- Seeded disk and scatter patterns use the deterministic generator in the engine. Changes to it affect replay compatibility.
- Snapshots preserve the full live-cell state and birth-generation colour history. A restoration must reproduce the image and subsequent evolution, not merely approximate it by rerunning a seed.
- Validate imported snapshots before replacing the visible state. Keep a version tag; provide an explicit migration if the format changes.
- Palette and camera changes must not change the automaton.
- The avatar export is a square PNG of the artwork. Circle cropping is only a preview.
- `dist/` contains authored source. It is not disposable output.

## Scope and stack

Native browser ES modules, HTML, CSS and Canvas 2D; a small Node static server. No runtime or development package dependencies. `npm start` must work without an install step. Do not introduce a framework, bundler, database, API or ML runtime just because one is familiar. If a later requested feature justifies it, discuss the tradeoff and preserve the pure engine.

Do not bundle the user's textbook or MIT archive into the repository. See `docs/SOURCES.md`; those materials remain separate. Do not claim a full book read or proof audit was completed.

## Workflow

Use `npm run check` for syntax. For behavioural changes, verify a known pattern or a concrete invariant affected by the change. Avoid a large test suite that mirrors the implementation. The next useful step is a browser pass over the existing UI, not a rewrite.

Preserve accessibility labels, keyboard shortcuts that do not steal input focus, responsive layout and reduced-motion preferences. Playback is opt-in and pauses in the background. Use the same underlying actions for optional agent tools and UI controls. Browser-only API support must remain optional.

No subagents are required. Do not add deployment credentials or private source material to Git.

## Communication

Be concise and specific. Explain what changed and what was actually verified. Never use an em dash. Avoid inline code comments unless they are necessary for a non-obvious invariant. Do not invent scientific novelty, biological claims or regeneration guarantees. Autonomous numerical growth is not proof of intelligence.

## Neural CA experiment

The separate `nca/` experiment is now authorized. It follows Mordvintsev et al., *Growing Neural Cellular Automata* (Distill, 2020): Sobel perception, shared residual 1×1 rule, stochastic per-cell fire mask, alpha-based living mask and a single central seed. Keep its PyTorch training process separate from the dependency-free classical studio. Browser playback accepts only exported learned weights and must not load a target, a coordinate map, an animation or a reveal mask.

Targets, checkpoints, progress logs, contact sheets, virtual environments and personal photos are local-only and ignored by Git. `nca-runs/*/model.json` is the portable inference artifact. The checkpoint needs the original target only for further training or evaluation, never playback. Do not claim recognisability from loss alone: inspect fresh seed rollouts and longer-than-training rollouts.

## Possible later work, not current requirements

An editable finite-state coordinate image generator; bounded rule search with replayable witnesses; a gallery of saved specimens; damage-recovery training for the NCA. Keep future ideas labelled as proposals.
