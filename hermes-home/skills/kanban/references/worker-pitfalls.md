# Kanban Worker — Pitfalls and Reference

> The lifecycle (orient → work → heartbeat → block/complete) is auto-injected via `KANBAN_GUIDANCE`. This doc covers deeper detail.

## Workspace handling

| Kind | What it is | How to work |
|---|---|---|
| `scratch` | Fresh tmp dir, yours alone | Read/write freely; GC'd on archive |
| `dir:<path>` | Shared persistent directory | Other runs will read what you write |
| `worktree` | Git worktree | If `.git` missing, run `git worktree add` first, then cd and work |

## Tenant isolation

If `$HERMES_TENANT` is set, prefix memory entries with tenant name.

## Good summary + metadata shapes

**Coding task:**
```python
kanban_complete(
    summary="shipped rate limiter — token bucket, keys on user_id with IP fallback, 14 tests pass",
    metadata={"changed_files": [...], "tests_run": 14, "tests_passed": 14, "decisions": [...]},
)
```

**Review-required (block instead of complete):**
```python
kanban_comment(body="review-required handoff:\n" + json.dumps({...}))
kanban_block(reason="review-required: rate limiter shipped, 14/14 tests pass — needs eyes on...")
```

**Research task:**
```python
kanban_complete(
    summary="3 libraries reviewed; vLLM wins on throughput",
    metadata={"sources_read": 12, "recommendation": "vLLM", "benchmarks": {...}},
)
```

## Claiming cards you created

Only list ids captured from a successful `kanban_create` return value. Never invent ids from prose. The kernel verifies each id exists.

```python
# GOOD
c1 = kanban_create(title="fix X", assignee="worker")
kanban_complete(summary="...", created_cards=[c1["task_id"]])

# BAD — hallucinated ids
kanban_complete(summary="...", created_cards=["t_a1b2c3d4"])  # → gate rejects
```

## Block reasons

Bad: `"stuck"` — no context.
Good: one sentence naming the specific decision needed. Longer context goes in a comment.

## Heartbeats

Good: `"epoch 12/50, loss 0.31"`, `"scanned 1.2M/2.4M rows"`.
Bad: `"still working"`, empty, sub-second intervals. Skip for tasks < 2 min.

## Retry scenarios

Check `runs: [...]` from `kanban_show` for prior outcomes:
- `timed_out` — chunk work or shorten
- `crashed` — reduce memory
- `spawn_failed` — ask human via `kanban_block`
- `reclaimed` — operator archived; check status
- `blocked` — unblock comment should be in thread

## Do NOT

- Call `delegate_task` as substitute for `kanban_create`
- Call `clarify` — headless, will timeout silently
- Modify files outside `$HERMES_KANBAN_WORKSPACE`
- Create follow-up tasks assigned to yourself
- Complete a task you didn't actually finish — block instead

## Pitfalls

- **Task state changing between dispatch and startup** — always `kanban_show` first
- **Stale workspace artifacts** — read comment thread for context
- **Don't rely on CLI when tools are available** — `kanban_*` tools work across all backends
