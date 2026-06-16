# Instinct: Library Substitutions

**Confidence**: 100% **Source**: AGENTS.md (documented requirement) **Category**: code-style

## Pattern

The Ouroboros project requires specific library substitutions. Always use the prescribed alternatives.

| Never Use             | Always Use                   |
| --------------------- | ---------------------------- |
| `logging` (stdlib)    | `loguru`                     |
| `functools.lru_cache` | `cashews`                    |
| `datetime.utcnow()`   | `datetime.now(datetime.UTC)` |
| `Optional[T]`         | `T \| None`                  |

## Examples

### Logging

```python
# Wrong
import logging

logger = logging.getLogger(__name__)
logger.info("Message")

# Correct
from loguru import logger

logger.info("Message")
logger.bind(task_id=task.id).info("Task started")
```

### Datetime

```python
# Wrong
from datetime import datetime

now = datetime.utcnow()

# Correct
from datetime import datetime, UTC

now = datetime.now(UTC)
```

### Type Hints

```python
# Wrong
from typing import Optional
def get_user(id: int) -> Optional[User]:

# Correct
def get_user(id: int) -> User | None:
```

## Trigger

Activate when:

- Writing new Python code
- Reviewing code for style issues
- Seeing `import logging`, `lru_cache`, `utcnow()`, or `Optional[`
