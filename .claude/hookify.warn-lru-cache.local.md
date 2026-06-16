---
name: warn-lru-cache
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
  - field: new_text
    operator: regex_match
    pattern: from functools import.*lru_cache|@lru_cache
---

⚠️ **functools.lru_cache detected!**

This project uses **cashews** for caching instead of `functools.lru_cache`.

**Replace with:**

```python
from cashews import cache


@cache(ttl="1h")
async def your_function(): ...
```

See AGENTS.md "Required Library Substitutions" for details.
