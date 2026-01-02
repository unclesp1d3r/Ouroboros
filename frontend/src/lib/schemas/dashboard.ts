/**
 * Dashboard schemas for Ouroboros
 * Used by /api/v1/web/dashboard/* endpoints
 * Based on authoritative backend API schema
 */

import { z } from 'zod';

/**
 * Resource usage point schema
 * Single point in resource usage time series
 */
export const ResourceUsagePoint = z.object({
    timestamp: z.string().datetime().describe('UTC timestamp for the measurement'),
    hash_rate: z.number().describe('Hash rate value at this timestamp (hashes per second)'),
});
export type ResourceUsagePoint = z.infer<typeof ResourceUsagePoint>;

/**
 * Dashboard summary schema
 * High-level system statistics for dashboard display
 */
export const DashboardSummary = z.object({
    active_agents: z
        .number()
        .int()
        .describe(
            'Number of agents currently online and accessible (not stopped, error, or offline)'
        ),
    total_agents: z
        .number()
        .int()
        .describe('Total number of agents in the system (includes stopped, error, and offline)'),
    running_tasks: z
        .number()
        .int()
        .describe(
            'Number of currently running tasks (only includes attacks with tasks being actively processed)'
        ),
    total_tasks: z
        .number()
        .int()
        .describe('Total number of tasks (includes pending, running, and failed tasks)'),
    recently_cracked_hashes: z
        .number()
        .int()
        .describe('Number of recently cracked hashes (last 24 hours, not including duplicates)'),
    resource_usage: z
        .array(ResourceUsagePoint)
        .describe('Resource usage points (hash rate over last 12 hours, 1h intervals)'),
});
export type DashboardSummary = z.infer<typeof DashboardSummary>;

// Recent activity
export const RecentActivityStats = z.object({
    recent_cracks: z.number(),
    recent_campaigns: z.number(),
    recent_agents: z.number(),
});
export type RecentActivityStats = z.infer<typeof RecentActivityStats>;

// Queue status
export const QueueStatus = z.object({
    high_priority: z.number(),
    normal_priority: z.number(),
    low_priority: z.number(),
    total_pending: z.number(),
    processing: z.number(),
});
export type QueueStatus = z.infer<typeof QueueStatus>;

export const QueueStatusResponse = z.object({
    queues: z.record(z.string(), QueueStatus),
    total_pending: z.number(),
    total_processing: z.number(),
    recent_activity: RecentActivityStats,
});
export type QueueStatusResponse = z.infer<typeof QueueStatusResponse>;
