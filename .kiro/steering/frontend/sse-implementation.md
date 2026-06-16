---
inclusion: manual
---

# SSE (Server-Sent Events) Implementation Patterns

## Overview

This rule documents patterns for implementing Server-Sent Events in Ouroboros for real-time dashboard updates, based on successful SSE implementation and debugging.

## Backend SSE Implementation

### Correct Media Type Configuration

```python
# [x] CORRECT - Use proper SSE media type
@router.get("/live/campaigns")
async def get_campaign_events():
    return StreamingResponse(
        event_service.get_campaign_events(),
        media_type="text/event-stream",  # Critical: Must be text/event-stream
    )


# [FAIL] WRONG - Using text/plain breaks SSE
@router.get("/live/campaigns")
async def get_campaign_events():
    return StreamingResponse(
        event_service.get_campaign_events(),
        media_type="text/plain",  # This breaks EventSource connections
    )
```

### SSE Event Format

```python
# [x] CORRECT - Proper SSE event format
async def get_campaign_events():
    try:
        async for event in event_listener.get_events():
            yield f"data: {json.dumps(event)}\n\n"
    except TimeoutError:
        # Send keepalive ping every 30 seconds
        yield 'data: {"trigger": "ping"}\n\n'
```

### Authentication with SSE

```python
# [x] CORRECT - SSE endpoints must handle authentication
@router.get("/live/campaigns")
async def get_campaign_events(current_user: User = Depends(get_current_user)):
    return StreamingResponse(
        event_service.get_campaign_events(user_id=current_user.id),
        media_type="text/event-stream",
    )
```

## Frontend SSE Implementation

### SSE Service Pattern

```typescript
// [x] CORRECT - Robust SSE service with connection tracking
export class SSEService {
    private connections = new Map<string, EventSource>();
    private connectionStatus = $state({
        connected: false,
        connectedEndpoints: new Set<string>(),
        reconnectAttempts: 0
    });

    connect(endpoint: string, onMessage: (event: SSEEvent) => void): void {
        const eventSource = new EventSource(endpoint, {
            withCredentials: true  // Include cookies for authentication
        });

        eventSource.onopen = () => {
            this.updateConnectionStatus(endpoint, true);
        };

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.trigger !== 'ping') {  // Filter out keepalive pings
                onMessage(data);
            }
        };

        eventSource.onerror = () => {
            // Only mark as disconnected if connection is actually closed
            if (eventSource.readyState === EventSource.CLOSED) {
                this.updateConnectionStatus(endpoint, false);
                this.scheduleReconnect(endpoint, onMessage);
            }
        };

        this.connections.set(endpoint, eventSource);
    }

    private updateConnectionStatus(endpoint: string, connected: boolean) {
        if (connected) {
            this.connectionStatus.connectedEndpoints.add(endpoint);
        } else {
            this.connectionStatus.connectedEndpoints.delete(endpoint);
        }

        // Overall connection status based on any active connections
        this.connectionStatus.connected = this.connectionStatus.connectedEndpoints.size > 0;
    }
}
```

### Component Integration

```svelte
<!-- [x] CORRECT - SSE integration in dashboard components -->
<script lang="ts">
    import { sseService } from '$lib/services/sse';
    import { onMount } from 'svelte';

    let campaigns = $state([]);
    let connectionStatus = $derived(sseService.connected);

    onMount(() => {
        // Connect to SSE for real-time updates
        sseService.connect('/api/v1/web/live/campaigns', (event) => {
            if (event.trigger === 'campaign_updated') {
                // Handle campaign updates
                updateCampaignData(event);
            }
        });

        return () => {
            sseService.disconnect('/api/v1/web/live/campaigns');
        };
    });
</script>

<div class="dashboard">
    {#if connectionStatus}
        <div class="status-indicator connected">Real-time updates active</div>
    {:else}
        <div class="status-indicator disconnected">Real-time updates disconnected</div>
    {/if}

    <!-- Dashboard content -->
</div>
```

## Common SSE Issues and Solutions

### Media Type Mismatch

**Problem**: SSE connections fail immediately after establishment **Solution**: Ensure backend uses `media_type="text/event-stream"`

### Authentication Failures

**Problem**: SSE connections receive 401 errors **Solution**: Use `withCredentials: true` in EventSource constructor

### Connection Status Tracking

**Problem**: Frontend shows "disconnected" despite working connections **Solution**: Only treat `EventSource.CLOSED` state as actual disconnection

### Keep-Alive Handling

**Problem**: Connections timeout after 30 seconds **Solution**: Backend should send periodic ping messages, frontend should filter them

## Testing SSE Implementation

### Backend Tests

```python
def test_sse_media_type():
    response = client.get("/api/v1/web/live/campaigns")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
```

### Frontend Tests

```typescript
test('SSE service connects and receives events', async () => {
    const mockEventSource = vi.fn();
    global.EventSource = mockEventSource;

    const service = new SSEService();
    const onMessage = vi.fn();

    service.connect('/test-endpoint', onMessage);

    expect(mockEventSource).toHaveBeenCalledWith('/test-endpoint', {
        withCredentials: true
    });
});
```

## Development and Debugging

### Vite Proxy Configuration

```typescript
// [x] CORRECT - Vite proxy for SSE endpoints
export default defineConfig({
    server: {
        proxy: {
            '/api/v1/web/live': {
                target: 'http://backend:8000',
                changeOrigin: true,
                headers: {
                    'Accept': 'text/event-stream',
                    'Cache-Control': 'no-cache'
                }
            }
        }
    }
});
```

### Browser DevTools Debugging

- Check Network tab for SSE connections (should show as "eventsource" type)
- Look for proper `text/event-stream` content-type in response headers
- Monitor console for EventSource errors and reconnection attempts
- Verify authentication cookies are being sent with requests

## Performance Considerations

### Connection Management

```typescript
// [x] CORRECT - Proper connection cleanup
export class SSEService {
    disconnect(endpoint: string): void {
        const connection = this.connections.get(endpoint);
        if (connection) {
            connection.close();
            this.connections.delete(endpoint);
            this.updateConnectionStatus(endpoint, false);
        }
    }

    disconnectAll(): void {
        for (const [endpoint] of this.connections) {
            this.disconnect(endpoint);
        }
    }
}
```

### Reconnection Strategy

```typescript
// [x] CORRECT - Exponential backoff for reconnection
private scheduleReconnect(endpoint: string, onMessage: Function): void {
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

    setTimeout(() => {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.connect(endpoint, onMessage);
        }
    }, delay);
}
```

## Best Practices

1. **Always use `text/event-stream` media type** in backend responses
2. **Include authentication** with `withCredentials: true`
3. **Handle connection state properly** - only treat CLOSED as disconnected
4. **Implement keep-alive pings** to maintain connections
5. **Use exponential backoff** for reconnection attempts
6. **Clean up connections** when components unmount
7. **Test both success and failure scenarios** in development
8. **Monitor connection status** in production applications

## Anti-Patterns to Avoid

- Using `text/plain` instead of `text/event-stream`
- Treating all `onerror` events as connection failures
- Not implementing proper authentication for SSE endpoints
- Forgetting to clean up EventSource connections
- Not handling keep-alive ping messages
- Hardcoding connection endpoints without environment detection
