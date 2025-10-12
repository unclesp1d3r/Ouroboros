# Agent Performance Time Series Storage and Reduction

## Overview

Ouroboros tracks agent device performance (guesses/sec) over time for each device attached to an agent. This data is used for real-time dashboard charts, historical analysis, and performance tuning.

## Data Model

A new model, `AgentDevicePerformance`, is introduced to store time series data for each device on each agent:

- `id`: Primary key
- `agent_id`: Foreign key to Agent
- `device_name`: String (device label as reported by agent)
- `timestamp`: UTC datetime (when the measurement was recorded)
- `speed`: Float (guesses/sec at that timestamp)

## Storage Strategy

- Each time an agent submits a device status update, the backend records a new `AgentDevicePerformance` row for each device, capturing the current speed.
- Data is retained for a rolling window (e.g., 8 hours, configurable). Older data is periodically purged to keep storage efficient.
- Indexes are maintained on `(agent_id, device_name, timestamp)` for fast retrieval.

## Reduction Logic

- For dashboard and charting, the API reduces raw data to a fixed number of points (e.g., 48 points for 8 hours at 10-minute intervals).
- Reduction is performed by grouping data into time buckets (e.g., 10-minute intervals) and computing the average speed per bucket.
- If no data exists for a bucket, a zero or null value is returned for that interval.

## Access Pattern

- The `/api/v1/web/agents/{id}/performance` endpoint queries the reduced time series for each device on the agent, returning a list of `{timestamp, speed}` pairs for charting.
- The reduction logic is implemented in the service layer for testability and reuse.

## Future Considerations

- For long-term analysis, data can be further downsampled and archived.
- Additional metrics (e.g., temperature, utilization) can be added to the model as needed.

---

## Last Updated

2024-06-10
