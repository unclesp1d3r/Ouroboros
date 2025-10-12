/**
 * Health schemas for Ouroboros
 * Used by /api/v1/web/health/* endpoints
 */

import { z } from 'zod';
import { StatusEnum, QueueType } from './base';

// Database health
export const PostgresHealth = z.object({
    status: StatusEnum,
    response_time_ms: z.number(),
});
export type PostgresHealth = z.infer<typeof PostgresHealth>;

export const PostgresHealthDetailed = z.object({
    status: StatusEnum,
    response_time_ms: z.number(),
    connection_count: z.number(),
    database_size_mb: z.number(),
});
export type PostgresHealthDetailed = z.infer<typeof PostgresHealthDetailed>;

// Redis health
export const RedisHealth = z.object({
    status: StatusEnum,
    response_time_ms: z.number(),
    memory_usage_mb: z.number(),
});
export type RedisHealth = z.infer<typeof RedisHealth>;

export const RedisHealthDetailed = z.object({
    status: StatusEnum,
    response_time_ms: z.number(),
    memory_usage_mb: z.number(),
    connected_clients: z.number(),
    keyspace_hits: z.number(),
    keyspace_misses: z.number(),
});
export type RedisHealthDetailed = z.infer<typeof RedisHealthDetailed>;

// MinIO health
export const MinioHealth = z.object({
    status: StatusEnum,
    response_time_ms: z.number(),
});
export type MinioHealth = z.infer<typeof MinioHealth>;

export const MinioHealthDetailed = z.object({
    status: StatusEnum,
    response_time_ms: z.number(),
    bucket_count: z.number(),
    total_objects: z.number(),
    total_size_mb: z.number(),
});
export type MinioHealthDetailed = z.infer<typeof MinioHealthDetailed>;

// Queue health
export const QueueHealth = z.object({
    queue_type: QueueType,
    status: StatusEnum,
    pending_jobs: z.number(),
    active_jobs: z.number(),
});
export type QueueHealth = z.infer<typeof QueueHealth>;

// System health overview
export const SystemHealthOverview = z.object({
    overall_status: StatusEnum,
    postgres: PostgresHealth,
    redis: RedisHealth,
    minio: MinioHealth,
    queues: z.array(QueueHealth),
});
export type SystemHealthOverview = z.infer<typeof SystemHealthOverview>;

export const SystemHealthComponents = z.object({
    postgres: PostgresHealthDetailed,
    redis: RedisHealthDetailed,
    minio: MinioHealthDetailed,
    queues: z.array(QueueHealth),
});
export type SystemHealthComponents = z.infer<typeof SystemHealthComponents>;

// System version
export const SystemVersionResponse = z.object({
    version: z.string(),
    build_date: z.string(),
    git_commit: z.string().nullish(),
});
export type SystemVersionResponse = z.infer<typeof SystemVersionResponse>;

// Cracker updates
export const CrackerUpdateResponse = z.object({
    available: z.boolean(),
    current_version: z.string(),
    latest_version: z.string().nullish(),
    download_url: z.string().nullish(),
});
export type CrackerUpdateResponse = z.infer<typeof CrackerUpdateResponse>;
