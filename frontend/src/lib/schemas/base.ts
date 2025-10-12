/**
 * Base schemas and enums for Ouroboros
 * Core types used across the application
 */

import { z } from 'zod';

// Agent related enums
/**
 * Agent state enumeration
 * Represents the current operational state of a Ouroboros agent
 */
export const AgentState = z.enum(['pending', 'active', 'stopped', 'error']);
export type AgentState = z.infer<typeof AgentState>;

/**
 * Agent type enumeration
 * Defines the type of agent (currently only 'hashcat' is supported)
 */
export const AgentType = z.enum(['hashcat']);
export type AgentType = z.infer<typeof AgentType>;

/**
 * Operating system enumeration
 * Supported operating systems for Ouroboros agents
 */
export const OperatingSystemEnum = z.enum(['windows', 'linux', 'macos', 'freebsd', 'other']);
export type OperatingSystemEnum = z.infer<typeof OperatingSystemEnum>;

// Campaign related enums
/**
 * Campaign state enumeration
 * Represents the lifecycle state of a password cracking campaign
 */
export const CampaignState = z.enum([
    'draft',
    'active',
    'archived',
    'paused',
    'completed',
    'error',
]);
export type CampaignState = z.infer<typeof CampaignState>;

// Attack related enums
/**
 * Attack mode enumeration
 * Defines the type of password cracking attack to perform
 */
export const AttackMode = z.enum(['dictionary', 'mask', 'hybrid_dictionary', 'hybrid_mask']);
export type AttackMode = z.infer<typeof AttackMode>;

/**
 * Attack state enumeration
 * Represents the current state of an attack within a campaign
 */
export const AttackState = z.enum([
    'draft',
    'pending',
    'running',
    'completed',
    'failed',
    'abandoned',
]);
export type AttackState = z.infer<typeof AttackState>;

// Task related enums
/**
 * Task status enumeration
 * Represents the execution status of individual cracking tasks
 */
export const TaskStatus = z.enum([
    'pending',
    'running',
    'paused',
    'completed',
    'failed',
    'abandoned',
]);
export type TaskStatus = z.infer<typeof TaskStatus>;

/**
 * Wordlist source enumeration
 * Defines where wordlists originate from
 */
export const WordlistSource = z.enum(['uploaded', 'generated']);
export type WordlistSource = z.infer<typeof WordlistSource>;

/**
 * Attack resource type enumeration
 * Types of resources that can be used in attacks
 */
export const AttackResourceType = z.enum([
    'mask_list',
    'rule_list',
    'word_list',
    'charset',
    'dynamic_word_list',
    'ephemeral_word_list',
    'ephemeral_mask_list',
    'ephemeral_rule_list',
]);
export type AttackResourceType = z.infer<typeof AttackResourceType>;

/**
 * Attack move direction enumeration
 * Directions for reordering attacks within a campaign
 */
export const AttackMoveDirection = z.enum(['up', 'down', 'top', 'bottom']);
export type AttackMoveDirection = z.infer<typeof AttackMoveDirection>;

// Device related enums
/**
 * Device status enumeration
 * Status of compute devices available to agents
 */
export const DeviceStatus = z.enum(['available', 'busy', 'error', 'disabled']);
export type DeviceStatus = z.infer<typeof DeviceStatus>;

/**
 * Login result level enumeration
 * Severity levels for login attempt results
 */
export const LoginResultLevel = z.enum(['info', 'warning', 'error']);
export type LoginResultLevel = z.infer<typeof LoginResultLevel>;

/**
 * Queue type enumeration
 * Priority levels for task queues
 */
export const QueueType = z.enum(['high', 'default', 'low']);
export type QueueType = z.infer<typeof QueueType>;

/**
 * Status enumeration
 * General health/status indicator for system components
 */
export const StatusEnum = z.enum(['healthy', 'unhealthy', 'unknown']);
export type StatusEnum = z.infer<typeof StatusEnum>;

/**
 * Upload processing step schema
 * Represents a single step in the upload processing pipeline
 */
export const UploadProcessingStep = z.object({
    step_name: z.string().describe('Name of the processing step'),
    status: z.string().describe('Status of this step: pending, running, completed, failed'),
    started_at: z
        .union([z.string(), z.null()])
        .nullish()
        .describe('ISO8601 start time for this step'),
    finished_at: z
        .union([z.string(), z.null()])
        .nullish()
        .describe('ISO8601 finish time for this step'),
    error_message: z
        .union([z.string(), z.null()])
        .nullish()
        .describe('Error message if step failed'),
    progress_percentage: z
        .union([z.number().int().min(0).max(100), z.null()])
        .nullish()
        .describe('Progress percentage for this step'),
});
export type UploadProcessingStep = z.infer<typeof UploadProcessingStep>;

// Error schemas
/**
 * Validation error schema
 * Represents a single validation error with location and message
 */
export const ValidationError = z.object({
    loc: z.array(z.union([z.string(), z.number()])),
    msg: z.string(),
    type: z.string(),
});
export type ValidationError = z.infer<typeof ValidationError>;

/**
 * HTTP validation error schema
 * Container for multiple validation errors from HTTP requests
 */
export const HTTPValidationError = z.object({
    detail: z.array(ValidationError).nullish(),
});
export type HTTPValidationError = z.infer<typeof HTTPValidationError>;

/**
 * Generic error object schema
 * Standard error response format for API endpoints
 */
export const ErrorObject = z.object({
    error: z.string(),
});
export type ErrorObject = z.infer<typeof ErrorObject>;
