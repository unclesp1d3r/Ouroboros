/**
 * Upload schemas for Ouroboros
 * Used by /api/v1/web/uploads/* endpoints
 * Based on authoritative backend API schema
 */

import { z } from 'zod';
import { UploadProcessingStep } from './base';

/**
 * Upload status output schema
 * Complete status information for an upload task
 */
export const UploadStatusOut = z.object({
    status: z.string().describe('Current status of the upload task'),
    started_at: z.string().nullish().describe('ISO8601 start time'),
    finished_at: z.string().nullish().describe('ISO8601 finish time'),
    error_count: z.number().int().describe('Number of errors encountered'),
    hash_type: z.string().nullish().describe('Inferred hash type name'),
    hash_type_id: z.number().int().nullish().describe('Inferred hash type ID'),
    preview: z.array(z.string()).describe('Preview of extracted hashes'),
    validation_state: z.string().describe('Validation state: valid, invalid, partial, pending'),
    upload_resource_file_id: z.string().describe('UUID of the upload resource file'),
    upload_task_id: z.number().int().describe('ID of the upload task'),
    processing_steps: z
        .array(UploadProcessingStep)
        .describe('Detailed information about each processing step'),
    current_step: z.string().nullish().describe('Name of the currently executing step'),
    total_hashes_found: z
        .number()
        .int()
        .nullish()
        .describe('Total number of hashes found in the file'),
    total_hashes_parsed: z
        .number()
        .int()
        .nullish()
        .describe('Total number of hashes successfully parsed'),
    campaign_id: z.number().int().nullish().describe('ID of the created campaign, if available'),
    hash_list_id: z.number().int().nullish().describe('ID of the created hash list, if available'),
    overall_progress_percentage: z
        .number()
        .int()
        .min(0)
        .max(100)
        .nullish()
        .describe('Overall progress percentage of the upload task'),
});
export type UploadStatusOut = z.infer<typeof UploadStatusOut>;

// Upload errors
export const UploadErrorEntryOut = z.object({
    line_number: z.number(),
    content: z.string(),
    error_message: z.string(),
    severity: z.string(),
});
export type UploadErrorEntryOut = z.infer<typeof UploadErrorEntryOut>;

export const UploadErrorEntryListResponse = z.object({
    items: z.array(UploadErrorEntryOut),
    total_count: z.number(),
    page: z.number(),
    page_size: z.number(),
    total_pages: z.number(),
});
export type UploadErrorEntryListResponse = z.infer<typeof UploadErrorEntryListResponse>;

// Form body schemas
export const Body_upload_resource_metadata_api_v1_web_uploads__post = z.object({
    filename: z.string(),
    hash_type_id: z.number(),
    description: z.string().nullish(),
    salt_format: z.string().nullish(),
});
export type Body_upload_resource_metadata_api_v1_web_uploads__post = z.infer<
    typeof Body_upload_resource_metadata_api_v1_web_uploads__post
>;
