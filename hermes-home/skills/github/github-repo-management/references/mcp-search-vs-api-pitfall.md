# MCP Search vs Direct API: Repo Discovery Pitfall

**Date:** 2026-06-11
**Session:** sfwefr-ux repo discovery

## Problem

`mcp_github_search_repositories` with `user:sfwefr-ux` returned **1 repository** (test), while the direct GitHub REST API (`GET /users/sfwefr-ux/repos`) returned **2 repositories** (Hermes + test).

## MCP Search Result

```
Query: user:sfwefr-ux
Total count: 1
  - test (created 2026-05-17)
```

## Direct API Result

```
URL: https://api.github.com/users/sfwefr-ux/repos?per_page=100&sort=updated
Total count: 2
  - Hermes (updated 2026-06-11)
  - test (updated 2026-05-17)
```

## Root Cause

The MCP GitHub search index may lag behind the REST API. The `Hermes` repo was created/updated on the same day (June 11) and hadn't been indexed by search yet. Direct API access always reflects the current state.

## Recommendation

- **For complete inventory**: use `GET /users/{username}/repos` (direct API via execute_code or terminal curl)
- **For targeted search**: MCP search is fine for finding repos by topic, language, or keyword
- **For verifying a specific repo exists**: direct API or `mcp_github_get_file_contents` on the repo root
