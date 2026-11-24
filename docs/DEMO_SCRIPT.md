# Demo video script (about 4 minutes)

Structure: **pain first, then the magic** (show the failure, then the factory that proves it), get to the
"wow" within 30 seconds, and end with a clear next step and ask.

Record the screen with QuickTime (File → New Screen Recording) and talk over it. Before you start, open
the deck, a terminal in `navprobe/`, and `outputs/results/gallery/F5_nearest_by_path.png`.

| Time | Show | Say |
|---|---|---|
| 0:00–0:30 | Slide 2 (the failure map) | "Hospitals are starting to let AI models read a floor map and choose where a delivery robot goes. Here, the robot should go to C. Six of seven models we tested send it to B, which looks closer but is behind closed doors. That is a robot stuck in front of a locked door with someone's medication." |
| 0:30–0:50 | Slide 2 steps | "NavProbe is a factory that tests whether a model can really read a map: it generates the map, computes the exact answer, proves the answer is visible, and tests the models." |
| 0:50–1:20 | Two sample maps (plan + ROS) | "Every map comes from a seed: rooms, open doors, closed doors in red, furniture, the robot and its heading arrow, and goals. Six kinds of question: counting, left or right, reachability, fit, nearest by driving, line of sight." |
| 1:20–1:55 | Terminal: `make verify`, then `pytest -q` | "A separate decoder rebuilds each map from its pixels and recomputes the answer: 1,407 of 1,407 pass. Mutation tests break answer keys, erase doors and move goals, and every corruption is caught." |
| 1:55–2:15 | Slide 6 (minimal pair) | "Minimal pairs: close one door and the answer flips. A model that guesses can't get both right." |
| 2:15–2:55 | Slide 10 (results table) | "A person scores 95%, about 8 seconds a task. The best model, Qwen3-VL 32B, scores 54%. Even a 72-billion-parameter model scores 48%. Small models do about as well with no image at all, and they keep repeating one favourite answer." |
| 2:55–3:30 | Slide 11 (trap chart) | "The key finding: bigger models get better at eyeballing distance, from 70% to 88%, but on traps, where the goal that looks closest isn't, they stay at chance. They don't plan routes." |
| 3:30–3:45 | Terminal / README (`docker run … make all`) | "Everything is one command, seeded, and Docker reproduces it byte-for-byte on Linux." |
| 3:45–4:00 | Slide 13 (What's next) | "Next: real hospital maps, and training a model on these verified tasks. Our ask is mentorship and GPU credits to run that experiment." |
