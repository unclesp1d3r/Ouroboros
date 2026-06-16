---
name: warn-stdlib-logging
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
  - field: new_text
    operator: regex_match
    pattern: ^import logging$|^from logging import
---

⚠️ **stdlib logging detected!**

This project uses **loguru** instead of the stdlib `logging` module.

**Replace with:**

```python
from app.core.logging import logger

logger.info("Your message")
logger.bind(key=value).info("Structured logging")
```

See AGENTS.md "Required Library Substitutions" for details.
