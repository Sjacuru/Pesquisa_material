---
name: Summarize Last Interaction
description: Summarize the latest repository work context and propose the single next logical task.
argument-hint: Paste the latest interaction notes, changed-file context, or active file focus.
agent: agent
---
Analyze the latest interaction context and produce a concise operational handoff.

Return exactly these sections:

1) **What We Were Working On**
- 3-6 bullets
- Focus on concrete tasks, not generic goals
- Mention active modules/files when available
- Separate product/planning work from implementation work

2) **Current State**
- 2-4 bullets
- Include what is done, what is partially done, and known blockers/unknowns
- If confidence is low, explicitly mark assumptions

3) **Next Most Logical Task**
- Exactly one task
- Must be actionable and immediately executable
- Include short rationale (1-2 sentences)
- Include a clear completion condition ("done when ...")

Rules:
- Prefer evidence from current branch/workspace context.
- If context is ambiguous, state the top 2 assumptions before recommending the next task.
- Keep output short and execution-focused.
- Do not invent completed work.
