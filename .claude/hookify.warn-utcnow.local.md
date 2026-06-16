---
name: warn-utcnow
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
  - field: new_text
    operator: regex_match
    pattern: datetime\.utcnow\(\)
---

⚠️ **Deprecated datetime.utcnow() detected!**

`datetime.utcnow()` is deprecated and returns a naive datetime.

**Replace with:**

```python
from datetime import UTC, datetime

now = datetime.now(UTC)
```

This returns a timezone-aware datetime, which is the correct approach.

See AGENTS.md "Required Library Substitutions" for details.
