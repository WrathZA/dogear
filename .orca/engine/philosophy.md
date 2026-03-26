# Orca Philosophy

Design principles that guide how orca skills are built and improved. Principles are added and evolved via `/orca-meditate` only.

## Principles

<!-- Principles are added here via /orca-meditate -->

### Specify outcomes, not procedures

When writing skill instructions, state what the agent must achieve or avoid — not a rigid sequence of implementation steps. Procedure specifications constrain the agent to one path, block adaptability when context changes, and push complexity into the skill that the agent can handle itself. A constraint like "patch the source file only after the issue number is confirmed" is stronger than "call orca-feed, wait for output, then patch the file" — the first specifies the invariant that must hold; the second locks in a particular execution path that may not generalise. The exception is when ordering IS the constraint: "commit before asking for feedback, not after" is a behavioral invariant, not a procedure hint, and belongs in the skill.

**Applies to:** All orca-* SKILL.md files, especially workflow step descriptions and NEVER rules
**Counterexample:** When step order is itself a correctness invariant (not just one way to accomplish the goal), explicit sequencing is appropriate.

### Iterate toward less wrong, not toward correct

A forcing function, in the evolutionary sense, is selective pressure — the environmental constraint that forces adaptation. In orca, forcing functions are the feedback loops (HITL decisions, skill-judge runs, therapy sessions) that create pressure to change. Like evolution, they do not produce correctness; they eliminate wrongness. Each cycle makes something slightly less wrong than it was before, and the system gets better the more you add to it, not worse — each iteration reduces wrongness and each addition builds on the last. Agents and users operating orca should resist the urge to achieve a "correct" outcome in a single pass — the workflow is designed for repeated small improvements driven by feedback pressure. Correctness, if it comes, emerges from accumulated iterations. An agent that halts until it finds the "right" answer is applying the wrong mental model.

**Applies to:** All orca-* skills, especially orca-therapy, orca-lasso, orca-meditate, and any skill that runs a feedback loop
**Counterexample:** Hard correctness constraints (e.g., "never commit to main") are invariants, not iterative targets — these must be correct on every execution, not slightly less wrong over time.
