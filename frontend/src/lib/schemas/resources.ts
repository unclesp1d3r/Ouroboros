/**
 * Resource schemas for Ouroboros
 * Used by /api/v1/web/resources/* endpoints
 * Based on authoritative backend API schema
 */

import { z } from 'zod';
import { AttackResourceType } from './base';

// Core resource schemas
/**
 * Resource list item schema
 * Basic resource information for list views
 */
export const ResourceListItem = z.object({
    id: z.string().uuid().describe('Resource ID'),
    file_name: z.string().describe('Resource file name'),
    file_label: z.string().nullish().describe('Resource display label'),
    resource_type: AttackResourceType.describe('Type of resource'),
    line_count: z.number().nullish().describe('Number of lines in file'),
    byte_size: z.number().int().nullish().describe('File size in bytes'),
    checksum: z.string().default('').describe('File checksum'),
    updated_at: z.string().datetime().nullish().describe('Last update timestamp'),
    line_format: z.string().nullish().describe('Format of each line in the resource file'),
    line_encoding: z.string().nullish().describe('Encoding of the resource file lines'),
    used_for_modes: z
        .array(z.string())
        .nullish()
        .describe('Attack modes this resource is compatible with'),
    source: z
        .string()
        .nullish()
        .describe('Source of the resource file (upload, generated, linked)'),
    project_id: z.number().int().nullish().describe('Project ID'),
    unrestricted: z.boolean().nullish().describe('Whether resource is unrestricted'),
    is_uploaded: z.boolean().default(false).describe('Whether the resource has been uploaded'),
    tags: z.array(z.string()).nullish().describe('Resource tags'),
});
export type ResourceListItem = z.infer<typeof ResourceListItem>;

/**
 * Resource list response schema
 * Paginated list of resources with filtering options
 */
export const ResourceListResponse = z.object({
    items: z.array(ResourceListItem).describe('List of resources'),
    total: z.number().int().describe('Total number of items'),
    page: z.number().int().min(1).max(100).default(1).describe('Current page number'),
    page_size: z.number().int().min(1).max(100).default(20).describe('Number of items per page'),
    search: z.string().nullish().describe('Search query'),
});
export type ResourceListResponse = z.infer<typeof ResourceListResponse>;

/**
 * Resource detail response schema
 * Complete resource information including metadata and usage statistics
 */
export const ResourceDetailResponse = z.object({
    id: z.string().uuid().describe('Resource ID'),
    file_name: z.string().describe('Resource file name'),
    file_label: z.string().nullish().describe('Resource display label'),
    resource_type: AttackResourceType.describe('Type of resource'),
    line_count: z.number().nullish().describe('Number of lines in file'),
    byte_size: z.number().int().nullish().describe('File size in bytes'),
    checksum: z.string().default('').describe('File checksum'),
    updated_at: z.string().datetime().nullish().describe('Last update timestamp'),
    line_format: z.string().nullish().describe('Format of each line in the resource file'),
    line_encoding: z.string().nullish().describe('Encoding of the resource file lines'),
    used_for_modes: z
        .array(z.string())
        .nullish()
        .describe('Attack modes this resource is compatible with'),
    source: z
        .string()
        .nullish()
        .describe('Source of the resource file (upload, generated, linked)'),
    project_id: z.number().int().nullish().describe('Project ID'),
    unrestricted: z.boolean().nullish().describe('Whether resource is unrestricted'),
    is_uploaded: z.boolean().default(false).describe('Whether the resource has been uploaded'),
    tags: z.array(z.string()).nullish().describe('Resource tags'),
    created_at: z.string().datetime().describe('Creation timestamp'),
    uploaded_by: z.string().nullish().describe('User who uploaded the resource'),
    usage_count: z.number().int().describe('Number of times resource has been used'),
    last_used: z.string().nullish().describe('Last usage timestamp'),
});
export type ResourceDetailResponse = z.infer<typeof ResourceDetailResponse>;

// Attack resource file output schema (from OpenAPI spec)
/**
 * Attack resource file output schema
 * Information about resource files associated with attacks
 */
export const AttackResourceFileOut = z.object({
    id: z.string().uuid().describe('Resource file ID'),
    download_url: z.string().describe('Download URL for the resource'),
    checksum: z.string().describe('File checksum'),
    file_name: z.string().describe('Resource file name'),
    guid: z.string().uuid().describe('Resource GUID'),
    resource_type: AttackResourceType.describe('Type of resource file'),
    line_format: z.string().describe('Format of each line in the resource file'),
    line_encoding: z.string().describe('Encoding of the resource file lines'),
    used_for_modes: z.array(z.string()).describe('Attack modes this resource is compatible with'),
    source: z.string().describe('Source of the resource file (upload, generated, linked)'),
    line_count: z.number().int().describe('Number of lines in the resource file'),
    byte_size: z.number().int().describe('Size of the resource file in bytes'),
    content: z
        .union([z.record(z.array(z.string())), z.null()])
        .nullish()
        .describe('Resource content'),
    is_uploaded: z.boolean().default(false).describe('Whether the resource has been uploaded'),
});
export type AttackResourceFileOut = z.infer<typeof AttackResourceFileOut>;

// Resource dropdown items
/**
 * Resource dropdown item schema
 * Minimal resource information for dropdown selections
 */
export const ResourceDropdownItem = z.object({
    id: z.string().uuid().describe('Resource ID'),
    file_name: z.string().describe('Resource name'),
    file_label: z.string().nullish().describe('Resource description'),
    resource_type: AttackResourceType.describe('Type of resource'),
    line_count: z.number().int().nullish().describe('Number of lines in file'),
    byte_size: z.number().int().nullish().describe('File size in bytes'),
});
export type ResourceDropdownItem = z.infer<typeof ResourceDropdownItem>;

/**
 * Wordlist item schema
 * Wordlist-specific information for dropdown selections
 */
export const WordlistItem = z.object({
    id: z.string().uuid().describe('Wordlist ID'),
    file_name: z.string().describe('Wordlist name'),
    file_label: z.string().nullish().describe('Wordlist description'),
    line_count: z.number().int().nullish().describe('Number of words in wordlist'),
});
export type WordlistItem = z.infer<typeof WordlistItem>;

/**
 * Wordlist dropdown response schema
 * List of available wordlists for selection
 */
export const WordlistDropdownResponse = z.object({
    wordlists: z.array(WordlistItem).describe('Available wordlists'),
});
export type WordlistDropdownResponse = z.infer<typeof WordlistDropdownResponse>;

/**
 * Rulelist item schema
 * Rulelist-specific information for dropdown selections
 */
export const RulelistItem = z.object({
    id: z.string().uuid().describe('Rulelist ID'),
    file_name: z.string().describe('Rulelist name'),
    file_label: z.string().nullish().describe('Rulelist description'),
    line_count: z.number().int().nullish().describe('Number of rules in rulelist'),
});
export type RulelistItem = z.infer<typeof RulelistItem>;

/**
 * Rulelist dropdown response schema
 * List of available rulelists for selection
 */
export const RulelistDropdownResponse = z.object({
    rulelists: z.array(RulelistItem).describe('Available rulelists'),
});
export type RulelistDropdownResponse = z.infer<typeof RulelistDropdownResponse>;

// Resource content and lines
/**
 * Resource line schema
 * Individual line within a resource file
 */
export const ResourceLine = z.object({
    id: z.number().int().describe('Line ID'),
    line_number: z.number().int().describe('Line number within file'),
    content: z.string().describe('Line content'),
    resource_id: z.string().uuid().describe('Resource ID'),
    is_comment: z.boolean().nullish().describe('Whether line is a comment'),
});
export type ResourceLine = z.infer<typeof ResourceLine>;

/**
 * Resource lines response schema
 * Paginated view of resource file contents
 */
export const ResourceLinesResponse = z.object({
    lines: z.array(ResourceLine).describe('Resource file lines'),
    total_count: z.number().int().describe('Total number of lines in file'),
    page: z.number().int().describe('Current page number'),
    page_size: z.number().int().describe('Number of lines per page'),
    total_pages: z.number().int().describe('Total number of pages'),
});
export type ResourceLinesResponse = z.infer<typeof ResourceLinesResponse>;

/**
 * Resource content response schema
 * Full or partial content of a resource file
 */
export const ResourceContentResponse = z.object({
    content: z.string().describe('Resource file content'),
    file_name: z.string().describe('Original filename'),
    resource_type: AttackResourceType.describe('Type of resource'),
    line_count: z.number().int().describe('Number of lines in file'),
    byte_size: z.number().int().describe('File size in bytes'),
    encoding: z.string().describe('Content encoding (e.g., utf-8)'),
    is_truncated: z.boolean().describe('Whether content is truncated'),
    total_size: z.number().int().describe('Total file size in bytes'),
});
export type ResourceContentResponse = z.infer<typeof ResourceContentResponse>;

/**
 * Resource preview response schema
 * Preview of resource file content with sample lines
 */
export const ResourcePreviewResponse = ResourceDetailResponse.extend({
    preview_lines: z.array(z.string()).describe('Sample lines from the resource'),
    preview_error: z.string().nullish().describe('Error message if preview failed'),
    max_preview_lines: z.number().int().describe('Maximum number of preview lines'),
});
export type ResourcePreviewResponse = z.infer<typeof ResourcePreviewResponse>;

// Resource updates
/**
 * Resource update request schema
 * Fields that can be updated for an existing resource
 */
export const ResourceUpdateRequest = z.object({
    file_name: z.string().nullish().describe('New resource name'),
    file_label: z.string().nullish().describe('New resource description'),
    tags: z.array(z.string()).nullish().describe('Resource tags'),
});
export type ResourceUpdateRequest = z.infer<typeof ResourceUpdateRequest>;

// Resource uploads
/**
 * Resource upload form schema
 * Form validation schema for resource uploads
 */
export const ResourceUploadFormSchema = z.object({
    file_name: z.string().min(1).describe('Resource name'),
    file_label: z.string().nullish().describe('Resource description'),
    resource_type: AttackResourceType.describe('Type of resource'),
    tags: z.array(z.string()).nullish().describe('Resource tags'),
});
export type ResourceUploadFormSchema = z.infer<typeof ResourceUploadFormSchema>;

/**
 * Resource upload metadata schema
 * Metadata for resource upload operations
 */
export const ResourceUploadMeta = z.object({
    file_name: z.string().describe('Original filename'),
    byte_size: z.number().int().describe('File size in bytes'),
    checksum: z.string().describe('File checksum'),
    resource_type: AttackResourceType.describe('Type of resource'),
});
export type ResourceUploadMeta = z.infer<typeof ResourceUploadMeta>;

/**
 * Resource upload response schema
 * Response after initiating resource upload
 */
export const ResourceUploadResponse = z.object({
    upload_url: z.string().describe('Presigned upload URL'),
    resource_id: z.string().uuid().describe('Resource ID'),
    fields: z.record(z.string()).describe('Additional form fields for upload'),
});
export type ResourceUploadResponse = z.infer<typeof ResourceUploadResponse>;

/**
 * Resource uploaded response schema
 * Response after completing resource upload
 */
export const ResourceUploadedResponse = z.object({
    resource_id: z.string().uuid().describe('Resource ID'),
    file_name: z.string().describe('Uploaded filename'),
    byte_size: z.number().int().describe('File size in bytes'),
    checksum: z.string().describe('File checksum'),
    status: z.string().describe('Upload status'),
});
export type ResourceUploadedResponse = z.infer<typeof ResourceUploadedResponse>;

/**
 * Resource usage statistics point schema
 * Usage statistics data point for individual resources
 */
export const ResourceUsageStats = z.object({
    timestamp: z.string().datetime().describe('Usage timestamp'),
    usage_count: z.number().int().describe('Usage count at this time'),
});
export type ResourceUsageStats = z.infer<typeof ResourceUsageStats>;

/**
 * Rule explanation schema
 * Explanation of a hashcat rule
 */
export const RuleExplanation = z.object({
    rule: z.string().describe('Hashcat rule'),
    explanation: z.string().describe('Human-readable explanation'),
});
export type RuleExplanation = z.infer<typeof RuleExplanation>;

/**
 * Rule explanation list schema
 * List of rule explanations
 */
export const RuleExplanationList = z.object({
    explanations: z.array(RuleExplanation).describe('List of rule explanations'),
});
export type RuleExplanationList = z.infer<typeof RuleExplanationList>;

// API body schemas for specific endpoints
export const Body_add_resource_line_api_v1_web_resources__resource_id__lines_post = z.object({
    content: z.string().describe('Line content to add'),
    line_number: z.number().int().nullish().describe('Specific line number to insert at'),
});
export type Body_add_resource_line_api_v1_web_resources__resource_id__lines_post = z.infer<
    typeof Body_add_resource_line_api_v1_web_resources__resource_id__lines_post
>;

export const Body_update_resource_content_api_v1_web_resources__resource_id__content_patch =
    z.object({
        content: z.string().describe('New resource content'),
        encoding: z.string().nullish().describe('Content encoding'),
    });
export type Body_update_resource_content_api_v1_web_resources__resource_id__content_patch = z.infer<
    typeof Body_update_resource_content_api_v1_web_resources__resource_id__content_patch
>;

export const Body_update_resource_line_api_v1_web_resources__resource_id__lines__line_id__patch =
    z.object({
        content: z.string().describe('New line content'),
    });
export type Body_update_resource_line_api_v1_web_resources__resource_id__lines__line_id__patch =
    z.infer<
        typeof Body_update_resource_line_api_v1_web_resources__resource_id__lines__line_id__patch
    >;

export const Body_upload_resource_metadata_api_v1_web_resources__post = z.object({
    file_name: z.string().describe('Resource filename'),
    resource_type: AttackResourceType.describe('Type of resource'),
    byte_size: z.number().int().describe('File size in bytes'),
    checksum: z.string().describe('File checksum'),
    file_label: z.string().nullish().describe('Resource label'),
    tags: z.array(z.string()).nullish().describe('Resource tags'),
});
export type Body_upload_resource_metadata_api_v1_web_resources__post = z.infer<
    typeof Body_upload_resource_metadata_api_v1_web_resources__post
>;
