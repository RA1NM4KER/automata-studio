# Sources and reading status

## Supplied by the user

- Michael Sipser, *Introduction to the Theory of Computation*, second-edition scan, 453 PDF pages. Original filename: `Introduction_to_the_theory_of_computation_by_Michael_Sipser.pdf`.
- MIT OpenCourseWare `18.404j-fall-2020.zip`: course pages, lecture notes, transcripts, problem sets and exams. There are 25 lecture PDFs; the session numbering skips 13 because of the midterm.
- [JFLAP](https://jflap.org/).
- [Automatarium](https://automatarium.tdib.xyz/).
- [Stellenbosch CS345](https://www.cs.sun.ac.za/courses/cs345/).

The original files are deliberately not redistributed inside this code project. A separate `automata-reference-pack.zip` was prepared during the conversation with OCR text and a more detailed source map.

## What was reviewed

The uploaded book was OCR-processed in full, and selected passages were read. MIT's course pages and lecture coverage were inspected, with closer review of selected notes, including decidability, reductions, computation histories, recursion, Cook-Levin and space complexity. Not every proof or transcript was reviewed and no complete exercise solution pass was performed.

The 2020 MIT reading list uses the third edition of Sipser while the supplied book is the second. Older problem sets in the archive refer to second-edition exercises. Match topics and statements, not just section numbers.

The supplied Stellenbosch and JFLAP URLs could not be fully retrieved during the source pass. Automatarium returned a JavaScript-required page. Do not treat their full contents as known.

## Additional context

- [Growing Neural Cellular Automata](https://distill.pub/2020/growing-ca/): the architecture and training baseline reproduced by the separate neural experiment.
- [Google Research self-organising-systems](https://github.com/google-research/self-organising-systems): reference implementation inspected before implementation. The repository is Apache-2.0 licensed. Automata Studio's PyTorch code was independently written and retains this attribution; no TensorFlow source was copied.
- [Lenia, by Bert Wang-Chak Chan](https://chakazul.github.io/lenia.html): continuous cellular automata and related artificial-life work. This project's binary rules are not Lenia.

The application source was written for this project. PyTorch, NumPy and Pillow are optional local training dependencies for the neural experiment. No remote fonts or image assets are required. Scientific novelty is not claimed. The original source materials retain their own rights and licensing terms.
