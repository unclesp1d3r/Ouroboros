# Ouroboros API Documentation

This directory contains comprehensive documentation for all Ouroboros API interfaces.

## Documentation Structure

### Core Documentation Files

- **[overview.md](overview.md)** - High-level API overview and quick start guide
- **[agent.md](agent.md)** - Agent API (v1) documentation with legacy compatibility
- **[web.md](web.md)** - Web UI API documentation for SvelteKit frontend
- **[control.md](control.md)** - Control API documentation for CLI/automation tools
- **[error-responses.md](error-responses.md)** - Comprehensive error handling reference
- **[integration-guides.md](integration-guides.md)** - Step-by-step integration examples
- **[workflow-examples.md](workflow-examples.md)** - Complete workflow scenarios

### Interactive Documentation

- **Swagger UI**: Available at `/docs` when running the application
- **ReDoc**: Available at `/redoc` for alternative documentation view
- **OpenAPI Spec**: Raw specification available at `/openapi.json`

## API Interfaces Overview

### 1. Agent API (`/api/v1/client/*`)

**Purpose**: Legacy-compatible interface for Ouroboros agents
**Authentication**: Bearer tokens (`csa_<agent_id>_<token>`)
**Key Features**:

- Strict OpenAPI 3.0.1 specification compliance
- Agent registration and heartbeat
- Task assignment and progress reporting
- Result submission and error reporting
- Resource access via presigned URLs

### 2. Web UI API (`/api/v1/web/*`)

**Purpose**: Rich interface for SvelteKit frontend application
**Authentication**: JWT tokens in HTTP-only cookies
**Key Features**:

- Campaign and attack management
- Real-time updates via Server-Sent Events
- Agent monitoring and configuration
- Resource management with inline editing
- Hash list operations and analysis

### 3. Control API (`/api/v1/control/*`)

**Purpose**: Programmatic interface for CLI tools and automation
**Authentication**: API keys (`cst_<user_id>_<token>`)
**Key Features**:

- RFC9457-compliant error responses
- Batch operations and bulk management
- Offset-based pagination
- System health monitoring
- Template import/export

## Documentation Standards

### Field-Level Documentation

All Pydantic schemas should include comprehensive field documentation:

```python
class ExampleSchema(BaseModel):
    """Brief description of the schema's purpose."""

    field_name: Annotated[
        str,
        Field(
            description="Detailed description of what this field represents and how it's used.",
            examples=["example1", "example2"],
            min_length=1,
            max_length=255,
        ),
    ]

    model_config = ConfigDict(
        json_schema_extra={"example": {"field_name": "example_value"}}
    )
```

### Endpoint Documentation

API endpoints should include comprehensive documentation:

```python
@router.post(
    "/example",
    summary="Brief endpoint summary",
    description="""
    Detailed description of what the endpoint does.

    Include:
    - Prerequisites and requirements
    - State transitions or side effects
    - Real-time update triggers
    - Business logic explanations
    """,
    responses={
        200: {
            "description": "Success response description",
            "content": {"application/json": {"example": {"key": "value"}}},
        },
        400: {
            "description": "Client error description",
            "content": {
                "application/json": {
                    "examples": {
                        "validation_error": {
                            "summary": "Validation failed",
                            "value": {"detail": "Field is required"},
                        }
                    }
                }
            },
        },
    },
    tags=["Primary Tag", "Secondary Tag"],
)
async def example_endpoint(
    param: Annotated[
        int, Path(description="Parameter description with examples", example=123, gt=0)
    ],
) -> ResponseSchema:
    """Example endpoint implementation."""
    pass
```

### Error Response Documentation

Each API interface uses different error formats:

#### Agent API (Legacy Format)

```json
{
  "error": "Human readable error message"
}
```

#### Web UI API (FastAPI Standard)

```json
{
  "detail": "Human readable error message"
}
```

#### Control API (RFC9457 Problem Details)

```json
{
  "type": "https://example.com/problems/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The request contains invalid data",
  "instance": "/api/v1/control/campaigns/123"
}
```

## Maintaining Documentation

### Adding New Endpoints

1. **Add comprehensive docstrings** to the endpoint function
2. **Include detailed parameter descriptions** using FastAPI annotations
3. **Document all possible responses** with examples
4. **Add appropriate tags** for organization
5. **Update relevant documentation files** in this directory

### Updating Schemas

1. **Enhance field descriptions** with examples and constraints
2. **Add model_config with examples** for better OpenAPI generation
3. **Include validation rules** in field annotations
4. **Document relationships** between schemas

### Testing Documentation

1. **Verify OpenAPI generation** by checking `/docs` and `/redoc`
2. **Test examples** to ensure they work with actual API
3. **Validate error responses** match documented formats
4. **Check integration guides** for accuracy

## Integration Examples

### Python Client Example

```python
import requests


class CipherSwarmClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def list_campaigns(self, page: int = 1, size: int = 20):
        response = requests.get(
            f"{self.base_url}/api/v1/control/campaigns/",
            headers=self.headers,
            params={"page": page, "size": size},
        )
        response.raise_for_status()
        return response.json()


# Usage
client = CipherSwarmClient(base_url="https://api.example.com", api_key="cst_123_abc...")
campaigns = client.list_campaigns()
```

### JavaScript/TypeScript Example

```typescript
interface Campaign {
    id: number;
    name: string;
    state: "draft" | "active" | "paused" | "completed";
    project_id: number;
}

class CipherSwarmAPI {
    constructor(private baseUrl: string) {}

    async listCampaigns(): Promise<Campaign[]> {
        const response = await fetch(`${this.baseUrl}/api/v1/web/campaigns/`, {
            credentials: "include", // For cookie-based auth
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        return data.items;
    }
}

// Usage
const api = new CipherSwarmAPI("https://api.example.com");
const campaigns = await api.listCampaigns();
```

### cURL Examples

```bash
# Control API - List campaigns
curl -H "Authorization: Bearer cst_123_abc..." \
    "https://api.example.com/api/v1/control/campaigns/"

# Web UI API - Start campaign (requires cookie auth)
curl -X POST \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/campaigns/123/start"

# Agent API - Submit heartbeat
curl -X POST \
    -H "Authorization: Bearer csa_789_xyz..." \
    -H "Content-Type: application/json" \
    -d '{"status": "idle", "current_task_id": null}' \
    "https://api.example.com/api/v1/client/agents/789/heartbeat"
```

## Best Practices

### Documentation Writing

1. **Be specific and actionable** - Include concrete examples
2. **Document edge cases** - Cover error scenarios and limitations
3. **Keep examples current** - Regularly test and update examples
4. **Use consistent terminology** - Maintain glossary of terms
5. **Include context** - Explain why, not just what

### API Design

1. **Follow REST conventions** - Use appropriate HTTP methods and status codes
2. **Provide meaningful errors** - Include actionable error messages
3. **Version appropriately** - Maintain backward compatibility
4. **Document breaking changes** - Clearly communicate API changes
5. **Test thoroughly** - Validate all documented behavior

### Integration Support

1. **Provide working examples** - Include complete, runnable code
2. **Document authentication** - Clear setup instructions
3. **Explain rate limits** - Help users avoid hitting limits
4. **Show error handling** - Demonstrate proper error handling
5. **Include troubleshooting** - Common issues and solutions

## Contributing

When contributing to the API documentation:

1. **Follow existing patterns** - Maintain consistency with current docs
2. **Test your examples** - Ensure all code examples work
3. **Update multiple files** - Keep related docs in sync
4. **Review generated docs** - Check OpenAPI output
5. **Get feedback** - Have others review your documentation

For questions or suggestions about the API documentation, please open an issue or submit a pull request.
