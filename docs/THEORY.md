# The implemented model

Each cell has binary state, dead or alive. The grid has 151 rows and 151 columns. Let `s_t(i)` be a cell's state and `n_t(i)` the number of its living neighbours at time `t`.

- If `s_t(i) = 0`, its next state is 1 exactly when `n_t(i)` belongs to the birth set.
- If `s_t(i) = 1`, its next state is 1 exactly when `n_t(i)` belongs to the survival set.

All other next states are 0. A separate output buffer ensures the update is simultaneous. Updating cells in place would define a different process.

## Geometry

The square lattice uses the Moore neighbourhood: the eight surrounding positions, excluding the cell itself.

The hexagonal lattice is stored using odd-row offset coordinates. Every interior cell has left and right neighbours, two neighbours above and two below. On even rows the diagonal neighbours are shifted left; on odd rows they are shifted right. Rendering uses matching hexagonal centres, so visual adjacency agrees with the engine.

Outside-domain positions are permanently empty. Boundary cells have fewer represented neighbours. There is no wrapping.

## Seed and display

Single-cell, ring and discovered-witness seeds are fixed. A witness stores its exact centre-relative coordinates. Disk and scatter seeds draw from a deterministic pseudorandom generator keyed by a string. This generator is for repeatable art, not cryptography. Identical configuration and engine version produce identical evolution.

Each live cell also has a birth-generation value used by the renderer. It resets when a cell dies and records the new generation if it is born again. These values do not participate in the CA transition rule. The renderer interpolates palette colours over a 72-generation cycle. It never paints dead cells as alive.

The camera centres the lattice and scales to the greater of the pattern's extent and a minimum initial viewport. This keeps the initial seed small while framing mature specimens. Cell geometry is rendered into the requested PNG size, rather than enlarging a screenshot of the interface.

## Snapshot semantics

Format version 2 stores topology, rule, seed kind, optional witness coordinates, seed key, generation, all cell states, each cell's colour history, palette and framing. Full state is saved so restoration does not depend on replaying thousands of generations. Version-1 snapshots migrate explicitly by assigning no witness coordinates. Generation is capped at 4096 by the application.

## Limits

For a fixed finite binary grid of N cells, there are only 2^N automaton configurations. A deterministic autonomous trajectory eventually repeats. The app's fixed-point detection detects period one only. It does not identify all oscillators or establish open-ended novelty.

The textbook's DFA, PDA and Turing-machine models are related through computation theory, but they are not interchangeable labels for this app. This implementation is a finite-domain binary cellular automaton. It does not prove that its selected rules support universal computation or regeneration.
