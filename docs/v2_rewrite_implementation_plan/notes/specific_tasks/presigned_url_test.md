# Agent Presigned URL Validation

## 🧪 Task: Validate Agent Presigned URL

**ID:** `agent.presigned_url_test`\
**Endpoint:** `POST /api/v1/web/agents/{id}/test_presigned`\
**Context:** Admin-only agent diagnostics

### 🧭 Purpose

Allows administrators to test whether a specific **presigned S3/MinIO URL** is accessible from the Ouroboros backend (not from the agent itself). This helps confirm that uploaded attack resources are still valid and accessible for agent download.

### 📥 Input

```json
{
  "url": "https://minio.example.com/wordlists/xyz123?X-Amz-Signature=..."
}
```

- `url`: The full presigned URL to test.

### 📤 Output

```json
{
  "valid": true
}
```

- Returns a simple boolean indicating whether the resource was successfully fetched (e.g., HTTP 200 within timeout).

### ✅ Implementation Notes

- Perform a `HEAD` request against the provided URL with a short timeout (e.g., 3 seconds).

- Only return `true` for HTTP 200 responses.

- Handle:

  - 403/404 as invalid
  - Network errors as invalid
  - Invalid input as `422 Unprocessable Entity` with Pydantic validation error

- This endpoint is project-scoped and requires admin-level privileges.

### 🧩 UI Context (Optional)

If you want to link this to the Agent Hardware or Resource debug UI:

- Add a **"Test Download"** button next to the resource link on the Agent detail page.
- Clicking it triggers the endpoint via SvelteKit and returns a green check or red ❌ next to the file.

### 🔒 Security

- Validate `url` format with Pydantic.
- Disallow file:// or non-HTTP(S) schemes.
- Do not follow redirects.

### 🔗 Related

- See [Phase 2b: Resource Management](../../phase-2b-resource-management.md)
- Tied to agent resource download reliability and MinIO integration.
