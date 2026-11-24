# Limitations

Stated plainly, so that the findings are read at the right strength.

1. **Synthetic, simplified maps.** Clean 2-D grids with axis-aligned walls. Real SLAM maps are noisier
   (partial walls, sensor speckle, unknown regions). The results describe spatial reasoning on clean maps,
   which is an upper bound on what to expect from real ones.
2. **Grid world.** The robot moves in 4 directions on cells, with a square footprint and no rotation or
   dynamics. Driving distance is the grid shortest path.
3. **Conventions are given in the prompt.** Colours, the arrow and the unit of distance are explained in
   text. A model that ignores the legend is penalised, which we consider fair for a map-reading task.
4. **One image, one question, zero-shot, temperature 0.** No chain-of-thought prompting, few-shot examples or
   tool use. Models may do better with any of these; we measure the default single-turn behaviour.
5. **Open-weight models only.** No organiser credits were available, so no closed frontier models were
   tested. The pipeline supports the Gemini API (`--model gemini:...`) for anyone with a key.
6. **Sample size.** 100 base tasks per family; the 95% bootstrap intervals in the report show the
   uncertainty. Differences smaller than those intervals should not be read as real.
7. **Not a planner benchmark.** NavProbe does not claim VLMs should replace A*. It measures how far a
   VLM's reading of a map can be trusted when a VLM is the one making the decision.
8. **Answer-format sensitivity.** Replies must contain `{"answer": ...}`. Invalid replies count as wrong,
   and the invalid rate is reported separately so formatting failures are not mistaken for reasoning failures.
