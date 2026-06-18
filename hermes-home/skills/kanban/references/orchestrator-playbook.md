# Kanban Orchestrator — Decomposition Playbook

> This is the full orchestrator reference. The core lifecycle is auto-injected via `KANBAN_GUIDANCE`; this document covers the deeper playbook.

## Profiles are user-configured — not a fixed roster

Before fanning out, discover available profiles:
- `hermes profile list`
- Ask the user: "What profiles do you have set up?"

## When to use the board (vs. just doing the work)

Create Kanban tasks when:
1. Multiple specialists are needed
2. Work should survive a crash or restart
3. User might want to interject
4. Multiple subtasks can run in parallel
5. Review/iteration is expected
6. Audit trail matters

If none apply — use `delegate_task` or answer directly.

## Anti-temptation rules

- Do not execute the work yourself
- For any concrete task, create a Kanban task and assign it
- Split multi-lane requests before creating cards
- Run independent lanes in parallel
- Never create dependent work as independent ready cards
- If no specialist fits the available profiles, ask the user

## Decomposition playbook

### Step 1 — Understand the goal
Ask clarifying questions if the goal is ambiguous.

### Step 2 — Sketch the task graph
1. Extract the lanes from the request
2. Map each lane to a discovered profile
3. Decide independence vs gating
4. Create independent lanes as parallel cards with no parent links
5. Create synthesis/review cards with parent links

### Step 3 — Create tasks and link
```python
t1 = kanban_create(title="research: X", assignee="<profile-A>", ...)["task_id"]
t2 = kanban_create(title="implement: Y", assignee="<profile-B>", ...)["task_id"]
t3 = kanban_create(title="review: Z", assignee="<profile-C>", parents=[t1, t2], ...)["task_id"]
```

### Step 4 — Complete your own task
If spawned as a task yourself, mark it done with a summary.

### Step 5 — Report back
Tell the user what was created in plain prose.

## Common patterns

- **Fan-out + fan-in:** N research cards, one synthesis with all parents
- **Parallel implementation + validation:** implementer + verifier, reviewer gates on both
- **Pipeline:** planner → implementer → reviewer
- **Same-profile queue:** N tasks to same profile, serialized by dispatcher
- **Human-in-the-loop:** `kanban_block()` for input

## Goal-mode cards

For open-ended cards, pass `goal_mode=True`:
```python
kanban_create(title="Translate docs", assignee="translator", goal_mode=True, goal_max_turns=15)
```
Worker keeps going in same session; judge evaluates after each turn; budget exhausted → auto-blocked.

## Recovering stuck workers

- **Reclaim:** `hermes kanban reclaim <task_id>` — abort and reset to ready
- **Reassign:** `hermes kanban reassign <task_id> <new-profile> --reclaim`
- **Change model:** edit profile config, then reclaim

## Orchestrator pitfalls

- Inventing profile names — dispatcher silently fails
- Bundling independent lanes — create separate cards
- Over-linking because of wording — "finally check X" may be parallel
- Forgetting dependency links — parent links gate execution
- Reassignment vs new task — blocked review → NEW task, not re-run
- Argument order for links — `kanban_link(parent_id=..., child_id=...)`
