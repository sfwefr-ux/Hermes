# .env Token Format for Each Provider

| Provider | .env variable | Token prefix | Masked example |
|----------|--------------|--------------|----------------|
| Perplexity | `PERPLEXITY_API_KEY` | `pplx-` | — |
| Apify | `APIFY_API_TOKEN` | `apify_api_` | `apify_api_4BL...dW1g` |
| OpenRouter | `OPENROUTER_API_KEY` | `sk-or-v1-` | `sk-or-v1-...73 chars` |
| Firecrawl | `FIRECRAWL_API_KEY` | `fc-` | — |

All stored in `C:\Users\1\AppData\Local\hermes\.env`.

## Test commands (via execute_code)

### Perplexity
```python
# POST https://api.perplexity.ai/chat/completions
# Body: {"model":"sonar","messages":[{"role":"user","content":"ping"}],"max_tokens":50}
```

### Apify
```python
# GET https://api.apify.com/v2/users/me
# Header: Authorization: Bearer <token>
# Returns: user ID, username, email, plan
```

### OpenRouter
```python
# GET https://openrouter.ai/api/v1/models
# Header: Authorization: Bearer <key>
```

### Firecrawl
```python
# GET https://api.firecrawl.com/v1/account
# Header: Authorization: Bearer <key>
```
