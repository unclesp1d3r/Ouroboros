/**
 * Campaign schemas for Ouroboros
 * Used by /api/v1/web/campaigns/* endpoints
 */

import { z } from 'zod';
import { CampaignState, TaskStatus } from './base';
import { AttackSummary } from './attacks';

// Core campaign schemas
/**
 * Campaign read schema
 * Complete campaign information including metadata and state
 */
export const CampaignRead = z.object({
    name: z.string().max(128).describe('Campaign name'),
    description: z.string().max(1024).nullish().describe('Campaign description'),
    project_id: z.number().int().describe('Project ID'),
    priority: z.number().int().min(0).optional().describe('Campaign priority'),
    hash_list_id: z.number().int().describe('Hash list ID'),
    is_unavailable: z
        .boolean()
        .optional()
        .describe('True if the campaign is not yet ready for use'),
    id: z.number().int().describe('Campaign ID'),
    state: CampaignState.describe('Campaign state'),
    created_at: z.string().datetime().describe('Creation timestamp'),
    updated_at: z.string().datetime().describe('Last update timestamp'),
});
export type CampaignRead = z.infer<typeof CampaignRead>;

/**
 * Campaign creation schema
 * Required fields for creating a new campaign
 */
export const CampaignCreate = z.object({
    name: z.string().max(128).describe('Campaign name'),
    description: z.string().max(1024).nullish().describe('Campaign description'),
    project_id: z.number().int().describe('Project ID'),
    priority: z.number().int().min(0).optional().describe('Campaign priority'),
    hash_list_id: z.number().int().describe('Hash list ID'),
    is_unavailable: z
        .boolean()
        .optional()
        .describe('True if the campaign is not yet ready for use'),
});
export type CampaignCreate = z.infer<typeof CampaignCreate>;

/**
 * Campaign update schema
 * nullish fields for updating an existing campaign
 */
export const CampaignUpdate = z.object({
    name: z.string().max(128).nullish().describe('Campaign name'),
    description: z.string().max(1024).nullish().describe('Campaign description'),
    priority: z.number().int().min(0).nullish().describe('Campaign priority'),
});
export type CampaignUpdate = z.infer<typeof CampaignUpdate>;

/**
 * Campaign detail response schema
 * Campaign information with associated attacks
 */
export const CampaignDetailResponse = z.object({
    campaign: CampaignRead.describe('Campaign information'),
    attacks: z.array(AttackSummary).describe('List of attacks in the campaign'),
});
export type CampaignDetailResponse = z.infer<typeof CampaignDetailResponse>;

// Campaign listing and pagination
/**
 * Campaign list response schema
 * Paginated list of campaigns with metadata
 */
export const CampaignListResponse = z.object({
    items: z.array(CampaignRead).describe('List of campaigns'),
    total: z.number().int().describe('Total number of campaigns'),
    page: z.number().int().describe('Current page number'),
    size: z.number().int().describe('Number of campaigns per page'),
    total_pages: z.number().int().describe('Total number of pages'),
});
export type CampaignListResponse = z.infer<typeof CampaignListResponse>;

// Campaign metrics and progress
/**
 * Campaign metrics schema
 * Statistical information about campaign progress
 */
export const CampaignMetrics = z.object({
    total_hashes: z.number().int().describe('Total number of hashes'),
    cracked_hashes: z.number().int().describe('Number of cracked hashes'),
    uncracked_hashes: z.number().int().describe('Number of uncracked hashes'),
    percent_cracked: z.number().describe('Percentage of cracked hashes'),
    progress_percent: z.number().describe('Progress percentage'),
});
export type CampaignMetrics = z.infer<typeof CampaignMetrics>;

/**
 * Campaign progress schema
 * Detailed progress information including task counts and agent activity
 */
export const CampaignProgress = z.object({
    total_tasks: z.number().int().default(0).describe('Total number of tasks in the campaign'),
    active_agents: z
        .number()
        .int()
        .min(0)
        .default(0)
        .describe('Number of active agents in the campaign'),
    completed_tasks: z.number().int().min(0).default(0).describe('Number of completed tasks'),
    pending_tasks: z.number().int().min(0).default(0).describe('Number of pending tasks'),
    active_tasks: z.number().int().min(0).default(0).describe('Number of active tasks'),
    failed_tasks: z.number().int().min(0).default(0).describe('Number of failed tasks'),
    percentage_complete: z
        .number()
        .min(0)
        .max(100)
        .default(0)
        .describe('Percentage of completed tasks'),
    overall_status: TaskStatus.nullish().describe('Overall status of the campaign'),
    active_attack_id: z
        .number()
        .int()
        .min(0)
        .nullish()
        .describe('ID of the active attack in the campaign'),
});
export type CampaignProgress = z.infer<typeof CampaignProgress>;

// Campaign templates and import/export
/**
 * Campaign with attacks schema
 * Campaign information including all associated attacks
 */
export const CampaignWithAttacks = CampaignRead.extend({
    attacks: z.array(z.unknown()).describe('List of attacks in the campaign'),
});
export type CampaignWithAttacks = z.infer<typeof CampaignWithAttacks>;

/**
 * Campaign template input schema
 * Template structure for importing campaigns
 */
export const CampaignTemplate_Input = z.object({
    schema_version: z.string().default('20250511').describe('Schema version for compatibility'),
    name: z.string().describe('Campaign name'),
    description: z.string().nullish().describe('Campaign description'),
    attacks: z.array(z.unknown()).default([]).describe('List of attack templates'),
    hash_list_id: z.number().int().nullish().describe('ID of the hash list to use'),
});
export type CampaignTemplate_Input = z.infer<typeof CampaignTemplate_Input>;

/**
 * Campaign template output schema
 * Template structure for exporting campaigns
 */
export const CampaignTemplate_Output = z.object({
    schema_version: z.string().default('20250511').describe('Schema version for compatibility'),
    name: z.string().describe('Campaign name'),
    description: z.string().nullish().describe('Campaign description'),
    attacks: z.array(z.unknown()).default([]).describe('List of attack templates'),
    hash_list_id: z.number().int().nullish().describe('ID of the hash list to use'),
});
export type CampaignTemplate_Output = z.infer<typeof CampaignTemplate_Output>;

// Pagination response
/**
 * Offset paginated response schema for campaigns
 * Alternative pagination format with offset/limit parameters
 */
export const OffsetPaginatedResponse_CampaignRead_ = z.object({
    items: z.array(CampaignRead).describe('List of campaigns'),
    total: z.number().int().describe('Total number of campaigns'),
    limit: z.number().int().min(1).max(100).describe('Number of items requested'),
    offset: z.number().int().min(0).describe('Number of items skipped'),
});
export type OffsetPaginatedResponse_CampaignRead_ = z.infer<
    typeof OffsetPaginatedResponse_CampaignRead_
>;
