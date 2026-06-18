---
name: github
description: "Complete GitHub workflow — auth setup, PR lifecycle, code review, issues, and repo management via gh CLI or git+curl."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Pull-Requests, Issues, Code-Review, Authentication, Repositories, Git, CI/CD]
---

# GitHub Workflow

Complete GitHub operations: authentication, pull requests, code review, issues, and repository management. Every section works with `gh` CLI (preferred) and falls back to `git` + `curl` when `gh` isn't installed.

## Authentication Setup

Before any GitHub operation, detect and configure auth:

```bash
# Check what's available
gh auth status 2>/dev/null && echo "AUTH=gh" || echo "AUTH=git"
git config --global credential.helper 2>/dev/null
```

**Decision tree:**
1. `gh auth status` → authenticated: use `gh` for everything
2. `gh` installed but not authenticated → `gh auth login` (browser) or `echo "<token>" | gh auth login --with-token`
3. No `gh` → set up HTTPS token or SSH key via `git`

**HTTPS token (most portable):**
- Create at https://github.com/settings/tokens (scopes: `repo`, `workflow`)
- `git config --global credential.helper store`
- First `git ls-remote https://github.com/<user>/<repo>.git` → enter username + token as password
- `git config --global user.name "Name" && git config --global user.email "email"`

**Token extraction fallback (for curl API calls):**
```bash
if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
  export GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
  export GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
fi
export GH_OWNER=$(git remote get-url origin | sed -E 's|.*github\.com[:/]||; s|\.git$||' | cut -d/ -f1)
export GH_REPO=$(git remote get-url origin | sed -E 's|.*github\.com[:/]||; s|\.git$||' | cut -d/ -f2)
```

Full auth details: [`references/github-auth.md`](references/github-auth.md). Helper script: [`scripts/gh-env.sh`](scripts/gh-env.sh).

---

## Pull Request Workflow

### Branch → Commit → Push → PR → CI → Merge

```bash
# 1. Start clean
git checkout main && git pull origin main

# 2. Branch (feat/, fix/, refactor/, docs/, ci/)
git checkout -b feat/description

# 3. Commit (Conventional Commits: type(scope): summary)
git add <files> && git commit -m "feat: add feature X"

# 4. Push
git push -u origin HEAD

# 5. Create PR (gh)
gh pr create --title "feat: ..." --body "## Summary\n..." [--draft] [--reviewer user]
# OR (curl)
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GH_OWNER/$GH_REPO/pulls \
  -d '{"title":"...","body":"...","head":"<branch>","base":"main"}'

# 6. Monitor CI
gh pr checks [--watch]
# OR curl: GET /repos/$GH_OWNER/$GH_REPO/commits/$(git rev-parse HEAD)/status

# 7. Merge (when green)
gh pr merge --squash --delete-branch
```

**Full PR workflow:** [`references/github-pr-workflow.md`](references/github-pr-workflow.md) — CI monitoring, auto-fix loop, merge methods, auto-merge.
**PR templates:** [`templates/pr-body-feature.md`](templates/pr-body-feature.md), [`templates/pr-body-bugfix.md`](templates/pr-body-bugfix.md).
**CI troubleshooting:** [`references/ci-troubleshooting.md`](references/ci-troubleshooting.md).
**Conventional commits:** [`references/conventional-commits.md`](references/conventional-commits.md).

---

## Code Review

### Pre-Push Review (pure git — works everywhere)

```bash
git diff main...HEAD --stat          # Scope
git diff main...HEAD                 # Full diff
# Check for: debug statements, secrets, large files, merge conflicts
git diff main...HEAD | grep -n "print(\|console\.log\|TODO\|FIXME"
git diff main...HEAD | grep -in "password\|secret\|api_key\|token.*=\|private_key"
git diff main...HEAD | grep -n "<<<<<<\|>>>>>>\|======="
```

### PR Review on GitHub

```bash
# View PR
gh pr view 123
gh pr diff 123

# Check out locally for full review
git fetch origin pull/123/head:pr-123 && git checkout pr-123

# Submit review
gh pr review 123 --approve --body "LGTM!"
gh pr review 123 --request-changes --body "See inline comments."
```

### Review Checklist
- **Correctness:** Edge cases, error paths
- **Security:** No secrets, input validation, SQL injection, XSS
- **Quality:** Clear naming, no duplication, single responsibility
- **Testing:** New paths tested, happy + error cases
- **Performance:** No N+1 queries, no blocking in async
- **Documentation:** Public APIs documented

**Full review workflow:** [`references/github-code-review.md`](references/github-code-review.md) — inline comments via curl, formal reviews, review output template.

---

## Issues Management

### Quick Reference

| Action | gh | curl endpoint |
|--------|-----|--------------|
| List | `gh issue list` | `GET /repos/{o}/{r}/issues` |
| View | `gh issue view N` | `GET /repos/{o}/{r}/issues/N` |
| Create | `gh issue create ...` | `POST /repos/{o}/{r}/issues` |
| Add labels | `gh issue edit N --add-label ...` | `POST /repos/{o}/{r}/issues/N/labels` |
| Assign | `gh issue edit N --add-assignee ...` | `POST /repos/{o}/{r}/issues/N/assignees` |
| Comment | `gh issue comment N --body ...` | `POST /repos/{o}/{r}/issues/N/comments` |
| Close | `gh issue close N` | `PATCH /repos/{o}/{r}/issues/N` |
| Search | `gh issue list --search "..."` | `GET /search/issues?q=...` |

**Bug report template:** [`templates/bug-report.md`](templates/bug-report.md).
**Feature request template:** [`templates/feature-request.md`](templates/feature-request.md).
**Full reference:** [`references/github-issues.md`](references/github-issues.md).

---

## Repository Management

### Clone, Create, Fork

```bash
git clone https://github.com/owner/repo.git
gh repo create name --public --clone     # Create + clone
gh repo fork owner/repo --clone          # Fork + clone
```

### Releases

```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release list
```

### CI/Workflows

```bash
gh workflow list
gh run list --limit 10
gh run view <ID> --log-failed
gh run rerun <ID>
```

### Branch Protection & Secrets

```bash
gh secret set API_KEY --body "value"
gh secret list
# Branch protection: curl PUT /repos/{o}/{r}/branches/main/protection
```

**⚠️ MCP search pitfall:** `mcp_github_search_repositories` may return fewer results than direct REST API. Prefer `GET /users/{username}/repos` for complete inventory. See [`references/mcp-search-vs-api-pitfall.md`](references/mcp-search-vs-api-pitfall.md).

**Full reference:** [`references/github-repo-management.md`](references/github-repo-management.md).
**API cheatsheet:** [`references/github-api-cheatsheet.md`](references/github-api-cheatsheet.md).

---

## Quick Reference Table

| Action | gh | git + curl |
|--------|-----|-----------|
| Create PR | `gh pr create ...` | `curl POST /repos/{o}/{r}/pulls` |
| List PRs | `gh pr list` | `curl GET /repos/{o}/{r}/pulls` |
| View PR diff | `gh pr diff` | `git diff main...HEAD` |
| CI status | `gh pr checks --watch` | `curl GET .../commits/{sha}/status` |
| Merge | `gh pr merge --squash` | `curl PUT .../pulls/{n}/merge` |
| Review | `gh pr review N --approve` | `curl POST .../pulls/{n}/reviews` |
| Create issue | `gh issue create ...` | `curl POST /repos/{o}/{r}/issues` |
| Clone repo | `gh repo clone o/r` | `git clone https://...` |
| Create repo | `gh repo create name` | `curl POST /user/repos` |
| Fork | `gh repo fork o/r --clone` | `curl POST .../forks` + `git clone` |
| Create release | `gh release create v1.0` | `curl POST .../releases` |
| List workflows | `gh workflow list` | `curl GET .../actions/workflows` |
| Set secret | `gh secret set KEY` | `curl PUT .../actions/secrets/KEY` |
