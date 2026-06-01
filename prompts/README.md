# Agent personas for GSBGEN390

Four role-specific personas for spawning Claude subagents during this project.
Each file is a self-contained system prompt — paste the full contents as the
subagent's instructions when you spawn it.

## When to use which

| Role | When to spawn | Cost / overhead |
|---|---|---|
| **[Reviewer](reviewer.md)** | Major milestone done (e.g., before a paid run, before submitting to advisor) | Always worth it at milestones |
| **[Researcher](researcher.md)** | Concrete factual question that needs a citation (Park v2 details, comparable methodology, OpenRouter behavior) | On demand |
| **[Planner](planner.md)** | "What should we do next" when the path forks | Use sparingly — overlaps with RESEARCH_DESIGN.md |
| **[Builder](builder.md)** | Default mode — most direct work is Builder mode | This is the standard conversation in Claude Code |

## Recommended cadence

- **Small changes** (bug fix, doc update, single self-test): just Builder. No subagent needed.
- **Big milestones** (a complete phase, before paid run, before advisor signoff): spawn Reviewer with full persona. Treat the report as ground truth and triage from there.
- **Open questions** (Park v2 detail, comparable practice): spawn Researcher with a specific question.
- **Forks** (which of N approaches to take): spawn Planner; expect a decision table with tradeoffs.

## Usage notes

- Each persona reads RESEARCH_DESIGN.md + git log first to ground itself. Don't assume the agent already knows project state.
- Builder edits code AND updates RESEARCH_DESIGN.md when design surfaces. Builder is the only writer.
- Reviewer is read-only — it identifies problems but does not fix them. Fixes go through Builder.
- Researcher is read-only on the codebase but may web-search.
- Planner does not edit anything; produces decision tables.
