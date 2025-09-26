---
inclusion: fileMatch
fileMatchPattern: "app/schemas/**/*.py"
---

# Pydantic Schema Patterns for Ouroboros

## Schema Organization and Structure

### File Organization

- Store schemas in `app/schemas/{resource}.py` (e.g., `hash_list.py`, `campaign.py`)
- One schema file per domain/resource
- Import shared schemas from `app/schemas/shared.py`
- Group related schemas in the same file

### Schema Naming Conventions

- Input schemas: `{Resource}Create`, `{Resource}Update`
- Output schemas: `{Resource}Out`, `{Resource}Response`
- Internal schemas: `{Resource}UpdateData` (for service layer)
- List responses: Use `PaginatedResponse[{Resource}Out]` from [app/schemas/shared.py](mdc:app/schemas/shared.py)

## Input Schema Patterns

### Create Schemas

- Include all required fields for resource creation
- Use validation constraints with `Field()`
- Exclude auto-generated fields (id, timestamps)

```python
class HashListCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Hash list name")
    description: str | None = Field(
        None, max_length=1000, description="Optional description"
    )
    project_id: int = Field(..., gt=0, description="Project ID")
    hash_type_id: int = Field(..., ge=0, description="Hash type ID")
    is_unavailable: bool = Field(
        False, description="Whether the hash list is unavailable"
    )
```

### Update Schemas

- Make all fields optional for PATCH operations
- Use same validation constraints as create schemas
- Consider separate schemas for different update scenarios

```python
class HashListUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    is_unavailable: bool | None = None
```

### Service Layer Update Schemas

- Use for internal service operations
- May have different validation rules than API schemas
- Often used for partial updates

```python
class HashListUpdateData(BaseModel):
    name: str | None = None
    description: str | None = None
    is_unavailable: bool | None = None

    class Config:
        extra = "forbid"  # Prevent unexpected fields
```

## Output Schema Patterns

### Response Schemas

- Include all fields that should be exposed to clients
- Use `from_attributes = True` for SQLAlchemy model conversion
- Include computed fields when needed

```python
class HashListOut(BaseModel):
    id: int
    name: str
    description: str | None
    project_id: int
    hash_type_id: int
    is_unavailable: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### Pagination Responses

- Always use `PaginatedResponse[T]` for list endpoints
- Don't create custom pagination schemas

```python
# Correct - use shared pagination
from app.schemas.shared import PaginatedResponse


@router.get("/")
async def list_hash_lists() -> PaginatedResponse[HashListOut]:
    return PaginatedResponse[HashListOut](
        items=hash_lists,
        total=total,
        page=page,
        page_size=size,
        search=search_term,
    )
```

## Validation Patterns

### Field Validation

- Use `Field()` for constraints and documentation
- Prefer built-in validators over custom ones when possible
- Use descriptive error messages

```python
class CampaignCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Campaign name",
        examples=["Password Audit 2024"],
    )
    priority: int = Field(
        1, ge=1, le=10, description="Campaign priority (1-10, higher is more important)"
    )
```

### Custom Validators

- Use `@field_validator` for complex validation
- Use `@model_validator` for cross-field validation
- Keep validation logic simple and focused

```python
class AttackCreate(BaseModel):
    attack_mode: AttackMode
    mask: str | None = None
    wordlist_id: int | None = None

    @field_validator("mask")
    @classmethod
    def validate_mask_syntax(cls, v: str | None, info: ValidationInfo) -> str | None:
        if v is None:
            return v

        # Validate hashcat mask syntax
        if not re.match(r"^[\?a-zA-Z0-9\[\]]+$", v):
            raise ValueError("Invalid mask syntax")
        return v

    @model_validator(mode="after")
    def validate_attack_requirements(self) -> "AttackCreate":
        if self.attack_mode == AttackMode.MASK and not self.mask:
            raise ValueError("Mask is required for mask attacks")
        if self.attack_mode == AttackMode.DICTIONARY and not self.wordlist_id:
            raise ValueError("Wordlist is required for dictionary attacks")
        return self
```

## Type Hints and Annotations

### Modern Python Syntax

- Use `str | None` instead of `Optional[str]` (Python 3.10+)
- Use `list[T]` instead of `List[T]`
- Use `dict[K, V]` instead of `Dict[K, V]`

### Annotated Types

- Use `Annotated` for dependency injection
- Combine with `Field()` for validation and documentation

```python
from typing import Annotated
from pydantic import Field


class ResourceCreate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    tags: Annotated[list[str], Field(default_factory=list, max_items=10)]
```

## Configuration and Settings

### Model Configuration

- Use `from_attributes = True` for SQLAlchemy integration
- Set `extra = "forbid"` to prevent unexpected fields
- Use `str_strip_whitespace = True` for string fields

```python
class HashListCreate(BaseModel):
    name: str
    description: str | None = None

    class Config:
        from_attributes = True
        extra = "forbid"
        str_strip_whitespace = True
```

### Pydantic v2 Configuration

- Use `model_config` for Pydantic v2 style
- Prefer explicit configuration over defaults

```python
class HashListOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: int
    name: str
    # ... other fields
```

## Enum Integration

### Using Enums in Schemas

- Define enums in separate files or model files
- Use string enums for API compatibility
- Provide clear enum values

```python
from enum import Enum


class AttackMode(str, Enum):
    DICTIONARY = "dictionary"
    MASK = "mask"
    HYBRID_DICT = "hybrid_dict"
    HYBRID_MASK = "hybrid_mask"


class AttackCreate(BaseModel):
    attack_mode: AttackMode
    # ... other fields
```

## Error Handling and Validation

### Validation Error Responses

- Let FastAPI handle Pydantic validation errors automatically
- Use structured error responses for complex validation
- Provide helpful error messages

### Custom Error Models

- Define error schemas for consistent error responses
- Use for business logic validation errors

```python
class ValidationErrorDetail(BaseModel):
    field: str
    message: str
    invalid_value: Any | None = None


class ValidationErrorResponse(BaseModel):
    detail: str
    errors: list[ValidationErrorDetail]
```

## Documentation and Examples

### Field Documentation

- Always provide `description` for public API fields
- Include `examples` for complex fields
- Use clear, concise descriptions

```python
class CampaignCreate(BaseModel):
    name: str = Field(
        ...,
        description="Human-readable campaign name",
        examples=["Q1 2024 Password Audit"],
    )
    hash_list_id: int = Field(..., description="ID of the hash list to target", gt=0)
```

### Schema Examples

- Provide complete examples in docstrings
- Include both valid and invalid examples
- Document expected behavior

```python
class AttackEstimateRequest(BaseModel):
    """Request schema for attack keyspace estimation.

    Example:
        {
            "attack_mode": "mask",
            "mask": "?u?l?l?l?d?d",
            "hash_type_id": 0
        }
    """

    attack_mode: AttackMode
    mask: str | None = None
    hash_type_id: int
```

## Performance Considerations

### Lazy Loading

- Use `Field(exclude=True)` for expensive computed fields
- Consider separate schemas for different use cases
- Avoid deep nesting in response schemas

### Serialization Optimization

- Use `alias` for field name mapping
- Consider `by_alias=True` for consistent output
- Use `exclude_none=True` to reduce response size

```python
class HashListOut(BaseModel):
    id: int
    name: str
    item_count: int | None = Field(None, exclude=True)  # Expensive to compute

    class Config:
        from_attributes = True
        exclude_none = True
```

## Testing Schema Validation

### Unit Testing Schemas

- Test validation rules with valid and invalid data
- Test edge cases and boundary conditions
- Verify error messages are helpful

```python
def test_hash_list_create_validation():
    # Valid data
    valid_data = {"name": "Test Hash List", "project_id": 1, "hash_type_id": 0}
    schema = HashListCreate(**valid_data)
    assert schema.name == "Test Hash List"

    # Invalid data
    with pytest.raises(ValidationError) as exc_info:
        HashListCreate(name="", project_id=1, hash_type_id=0)

    errors = exc_info.value.errors()
    assert any(error["type"] == "string_too_short" for error in errors)
```
