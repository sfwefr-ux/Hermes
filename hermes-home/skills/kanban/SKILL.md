---
name: kanban
description: "Hermes Kanban multi-agent workflow: orchestrator decomposition playbook, worker lifecycle and pitfalls."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, collaboration, workflow]
---

# Kanban — Multi-Agent Work Queue

Hermes Kanban is a durable SQLite-backed multi-agent task board. Users drive it via `hermes kanban <verb>`, the dispatcher spawns worker profiles, and orchestrator profiles route work.

## Quick Reference

- **Board init:** `hermes kanban init`
- **Create task:** `hermes kanban create "title" --assignee <profile>`
- **List tasks:** `hermes kanban list` (alias `ls`)
- **Show task:** `hermes kanban show <id>`
- **Complete:** `hermes kanban complete <id> --summary "..." --metadata '{...}'`
- **Block:** `hermes kanban block <id> "reason"`
- **CLI fallback:** Every tool has a CLI equivalent for scripting; from an agent, prefer the `kanban_*` tools.

## When to use the board vs. `delegate_task`

| | Kanban | delegate_task |
|-|--------|--------------|
| Durability | Survives crashes/restarts | Lost if parent interrupted |
| Duration | Hours/days | Minutes (bounded by parent loop) |
| Multi-profile | Multiple specialist profiles | Single subagent |
| Audit trail | SQLite forever | None |

Create Kanban tasks when: multiple specialists needed, work must survive restarts, user may interject, subtasks run in parallel, review/iteration expected, audit trail matters.

## Orchestrator Role

Orchestrators route work — they decompose, create tasks, and link dependencies. They do NOT execute implementation themselves.

**Core rules:**
- Discover profiles first (`hermes profile list`). Never invent profile names.
- Split multi-lane requests into separate cards.
- Run independent lanes in parallel (no parent links).
- Gate dependent work with `parents=[...]`.
- Report the task graph back to the user.

**Full playbook:** [`references/orchestrator-playbook.md`](references/orchestrator-playbook.md) — decomposition, task-graph sketching, anti-temptation rules, common patterns (fan-out/fan-in, pipeline, human-in-the-loop), goal-mode cards, recovering stuck workers.

## Worker Role

Workers are spawned by the dispatcher to execute individual tasks. The basic lifecycle (orient → work → heartbeat → block/complete) is auto-injected into every worker's system prompt.

**Key rules:**
- Always `kanban_show` first — task state may have changed between dispatch and startup.
- Use `kanban_complete` with structured metadata (changed files, tests, decisions).
- For code changes needing human review, block with `reason="review-required: ..."` instead of completing.
- Claim only cards you actually created via `created_cards=[...]`.
- Do NOT call `clarify` — workers run headless. Use `kanban_comment` + `kanban_block`.
- Do NOT modify files outside `$HERMES_KANBAN_WORKSPACE`.

**Full reference:** [`references/worker-pitfalls.md`](references/worker-pitfalls.md) — workspace handling, tenant isolation, handoff shapes, retry diagnostics, block reasons, heartbeats, created_cards verification.

## Core Lifecycle (auto-injected)

Every worker gets this in `KANBAN_GUIDANCE`:
1. **Orient** — `kanban_show` to read task + thread
2. **Work** — do the assigned work
3. **Heartbeat** — optional progress pings (name concrete progress, skip for tasks < 2 min)
4. **Complete** or **Block** — terminal state with summary + metadata

## Pitfalls

- **Inventing profile names** — dispatcher silently fails. Always `hermes profile list` first.
- **Bundling independent lanes** — create separate cards. "fix X and check Y" → two cards.
- **Forgetting parent links** — children without `parents=[]` run before inputs exist.
- **Calling clarify in a worker** — times out silently with no signal to the operator.
- **Task state changing between dispatch and startup** — always `kanban_show` first.
- **Notification routing** — configure `notification_sources` in `config.yaml` to receive cross-profile task notifications.
