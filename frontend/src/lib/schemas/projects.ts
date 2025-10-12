/**
 * Project schemas for Ouroboros
 * Used by /api/v1/web/projects/* endpoints
 * Based on authoritative backend API schema
 */

import { z } from 'zod';
import {
    DateTimeSchema,
    IdSchema,
    nullishNullableStringSchema,
    createListResponseSchema,
} from './common';

// Import UserRead for ProjectUsersResponse
// We'll reference it by import since it's defined in users.ts
import { UserRead } from './users';

// Core project schemas matching backend API
export const ProjectRead = z.object({
    id: z.number().int().describe('Project ID'),
    name: z.string().describe('Project name'),
    description: z.string().nullish().describe('Project description'),
    private: z.boolean().describe('Whether the project is private'),
    archived_at: z
        .union([z.string().datetime(), z.null()])
        .nullish()
        .describe('When the project was archived'),
    notes: z.string().nullish().describe('Project notes'),
    users: z.array(z.string().uuid()).describe('List of user IDs associated with the project'),
    created_at: z.string().datetime().describe('Creation timestamp'),
    updated_at: z.string().datetime().describe('Last update timestamp'),
});
export type ProjectRead = z.infer<typeof ProjectRead>;

export const ProjectCreate = z.object({
    name: z.string().min(1).max(128).describe('Project name'),
    description: z.string().nullish().describe('Project description'),
    private: z.boolean().default(false).describe('Whether the project is private'),
    archived_at: z
        .union([z.string().datetime(), z.null()])
        .nullish()
        .describe('When the project was archived'),
    notes: z.string().nullish().describe('Project notes'),
    users: z
        .union([z.array(z.string().uuid()), z.null()])
        .nullish()
        .describe('List of user IDs to associate with the project'),
});
export type ProjectCreate = z.infer<typeof ProjectCreate>;

export const ProjectUpdate = z.object({
    name: z.string().min(1).max(128).describe('Project name'),
    description: z.string().nullish().describe('Project description'),
    private: z.boolean().nullish().describe('Whether the project is private'),
    archived_at: z
        .union([z.string().datetime(), z.null()])
        .nullish()
        .describe('When the project was archived'),
    notes: z.string().nullish().describe('Project notes'),
    users: z
        .union([z.array(z.string().uuid()), z.null()])
        .nullish()
        .describe('List of user IDs to associate with the project'),
});
export type ProjectUpdate = z.infer<typeof ProjectUpdate>;

export const ProjectUpdateData = z.object({
    name: z.string().min(1).max(128).describe('Project name'),
    notes: z.string().nullish().describe('Project notes'),
});
export type ProjectUpdateData = z.infer<typeof ProjectUpdateData>;

// Project listings and responses
export const ProjectListResponse = z.object({
    items: z.array(ProjectRead).describe('List of projects'),
    total: z.number().int().describe('Total number of projects'),
    limit: z.number().int().min(1).max(100).describe('Number of items requested'),
    offset: z.number().int().min(0).describe('Number of items skipped'),
    search: z.string().nullish().describe('Search query'),
});
export type ProjectListResponse = z.infer<typeof ProjectListResponse>;

export const ProjectUsersResponse = z.object({
    items: z.array(UserRead).describe('List of users in the project'),
    total: z.number().int().describe('Total number of users'),
    limit: z.number().int().min(1).max(100).describe('Number of items requested'),
    offset: z.number().int().min(0).describe('Number of items skipped'),
});
export type ProjectUsersResponse = z.infer<typeof ProjectUsersResponse>;

// Form validation schemas
export const projectFormSchema = z.object({
    name: z.string().min(1, 'Project name is required').max(255, 'Project name too long'),
    description: z.string().max(1024, 'Description too long').nullish(),
});
export type ProjectFormData = z.infer<typeof projectFormSchema>;

export const projectSelectionSchema = z.object({
    project_id: z.number().int(),
});
export type ProjectSelection = z.infer<typeof projectSelectionSchema>;

// Legacy aliases for backward compatibility
export const ProjectReadType = ProjectRead;
export type ListProjectsResponseType = ProjectListResponse;
export type Project = ProjectRead;
