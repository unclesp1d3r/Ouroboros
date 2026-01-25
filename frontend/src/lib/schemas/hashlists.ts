/**
 * Hash list schemas for Ouroboros
 * Used by /api/v1/web/hash_lists/* endpoints
 * Based on authoritative backend API schema
 */

import { z } from 'zod';

// Core hash list schemas
/**
 * Hash list output schema
 * Complete hash list information including items
 */
export const HashListOut = z.object({
    id: z.number().int().describe('Unique identifier for the hash list'),
    name: z.string().describe('Name of the hash list'),
    description: z.union([z.string(), z.null()]).nullish().describe('Description of the hash list'),
    project_id: z.number().int().describe('Project ID'),
    hash_type_id: z.number().int().describe('Hash type ID'),
    is_unavailable: z.boolean().describe('True if the hash list is not yet ready for use'),
    items: z.array(z.lazy(() => HashItemOut)).describe('Hashes in the hash list'),
    created_at: z.string().datetime().describe('Creation timestamp'),
    updated_at: z.string().datetime().describe('Last update timestamp'),
});
export type HashListOut = z.infer<typeof HashListOut>;

/**
 * Hash list creation schema
 * Required fields for creating a new hash list
 */
export const HashListCreate = z.object({
    name: z.string().min(1).max(128).describe('Name of the hash list'),
    description: z
        .union([z.string().max(512), z.null()])
        .nullish()
        .describe('Description of the hash list'),
    project_id: z.number().int().min(1).describe('Project ID'),
    hash_type_id: z.number().int().min(0).describe('Hash type ID'),
    is_unavailable: z
        .boolean()
        .default(false)
        .describe('True if the hash list is not yet ready for use'),
});
export type HashListCreate = z.infer<typeof HashListCreate>;

/**
 * Hash list update schema
 * nullish fields for updating an existing hash list
 */
export const HashListUpdateData = z.object({
    name: z
        .union([z.string().min(1).max(128), z.null()])
        .nullish()
        .describe('Name of the hash list'),
    description: z
        .union([z.string().max(512), z.null()])
        .nullish()
        .describe('Description of the hash list'),
    is_unavailable: z
        .union([z.boolean(), z.null()])
        .nullish()
        .describe('True if the hash list is not yet ready for use'),
});
export type HashListUpdateData = z.infer<typeof HashListUpdateData>;

// Hash list pagination
/**
 * Paginated hash list response schema
 * Paginated list of hash lists
 */
export const PaginatedResponse_HashListOut_ = z.object({
    items: z.array(HashListOut).describe('List of hash lists'),
    total: z.number().int().describe('Total number of items'),
    page: z.number().int().describe('Current page number'),
    page_size: z.number().int().describe('Number of items per page'),
    total_pages: z.number().int().describe('Total number of pages'),
});
export type PaginatedResponse_HashListOut_ = z.infer<typeof PaginatedResponse_HashListOut_>;

// Hash items
/**
 * Hash item output schema
 * Individual hash within a hash list
 */
export const HashItemOut = z.object({
    id: z.number().int().describe('Unique identifier for the hash item'),
    hash: z.string().describe('Hash value'),
    salt: z.string().nullish().describe('Salt value, if present'),
    meta: z
        .union([z.record(z.string(), z.unknown()), z.null()])
        .nullish()
        .describe('User-defined metadata for the hash item'),
    plain_text: z
        .union([z.string(), z.null()])
        .nullish()
        .describe('Cracked plain text, if available'),
});
export type HashItemOut = z.infer<typeof HashItemOut>;

// Hash types
/**
 * Hash type dropdown item schema
 * Hash type information for dropdown selections
 */
export const HashTypeDropdownItem = z.object({
    mode: z.number().int().describe('Hashcat mode number'),
    name: z.string().describe('Hash type name'),
    category: z.string().describe('Hash type category'),
    confidence: z.number().nullish().describe('Confidence level'),
});
export type HashTypeDropdownItem = z.infer<typeof HashTypeDropdownItem>;

// Hashcat specific
/**
 * Hashcat guess schema
 * Individual guess result from hashcat
 */
export const HashcatGuess = z.object({
    guess_base: z.string().describe('The base value used for the guess (for example, the mask)'),
    guess_base_count: z.number().int().describe('The number of times the base value was used'),
    guess_base_offset: z.number().int().describe('The offset of the guess base'),
    guess_base_percentage: z.number().describe('The percentage of the guess base completed'),
    guess_mod_count: z.number().int().describe('The number of modifications applied to the guess'),
    guess_mod_offset: z.number().int().describe('The offset of the guess modification'),
    guess_mod_percentage: z.number().describe('The percentage of the guess modification completed'),
});
export type HashcatGuess = z.infer<typeof HashcatGuess>;

/**
 * Hashcat benchmark schema
 * Benchmark results from hashcat
 */
export const HashcatBenchmark = z.object({
    hash_type: z.number().int().describe('The hashcat hash type'),
    runtime: z.number().int().describe('The runtime of the benchmark in milliseconds'),
    hash_speed: z.number().describe('The speed of the benchmark in hashes per second'),
    device: z.number().int().describe('The device used for the benchmark'),
});
export type HashcatBenchmark = z.infer<typeof HashcatBenchmark>;
