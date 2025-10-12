/**
 * User schemas for Ouroboros
 * Used by /api/v1/web/users/* endpoints
 * Based on authoritative backend API schema
 */

import { z } from 'zod';

// Core user schemas matching backend API
export const UserRead = z.object({
    id: z.string().uuid().describe('User ID'),
    email: z.string().email().describe('User email address'),
    name: z.string().describe('User full name'),
    is_active: z.boolean().describe('Whether the user account is active'),
    is_superuser: z.boolean().describe('Whether the user has superuser privileges'),
    created_at: z.string().datetime().describe('Account creation timestamp'),
    updated_at: z.string().datetime().describe('Last update timestamp'),
    role: z.string().describe('User role'),
});
export type UserRead = z.infer<typeof UserRead>;

export const UserCreate = z.object({
    email: z.string().email().describe('User email address'),
    name: z.string().describe('User full name'),
    password: z.string().describe('User password'),
});
export type UserCreate = z.infer<typeof UserCreate>;

/**
 * User update request schema
 * Fields that can be updated for a user
 */
export const UserUpdate = z.object({
    email: z.string().email().nullish().describe('User email address'),
    name: z.string().nullish().describe('User full name'),
    password: z.string().nullish().describe('User password'),
    role: z.string().nullish().describe('User role'),
});
export type UserUpdate = z.infer<typeof UserUpdate>;

/**
 * User update data schema
 */
export const UserUpdateData = z.object({
    role: z.string().nullish().describe('User role'),
});
export type UserUpdateData = z.infer<typeof UserUpdateData>;

export const UserCreateControl = z.object({
    email: z.string().email().describe('User email address'),
    name: z.string().describe('User full name'),
    password: z.string().describe('User password'),
    role: z.string().nullish().describe('User role'),
    is_superuser: z.boolean().nullish().describe('Whether the user has superuser privileges'),
    is_active: z.boolean().nullish().describe('Whether the user account is active'),
});
export type UserCreateControl = z.infer<typeof UserCreateControl>;

export const UserListResponse = z.object({
    items: z.array(UserRead).describe('List of users'),
    total: z.number().int().describe('Total number of users'),
    limit: z.number().int().min(1).max(100).describe('Number of items requested'),
    offset: z.number().int().min(0).describe('Number of items skipped'),
    search: z.string().nullish().describe('Search query'),
});
export type UserListResponse = z.infer<typeof UserListResponse>;

export const PaginatedUserList = z.object({
    items: z.array(UserRead).describe('List of items'),
    total: z.number().int().describe('Total number of items'),
    page: z.number().int().min(1).max(100).default(1).describe('Current page number'),
    page_size: z.number().int().min(1).max(100).default(20).describe('Number of items per page'),
    search: z.string().nullish().describe('Search query'),
});
export type PaginatedUserList = z.infer<typeof PaginatedUserList>;

/**
 * User list request schema
 * Query parameters for listing users
 */
export const UserListRequest = z.object({
    page: z.number().int().min(1).default(1).describe('Page number'),
    page_size: z.number().int().min(1).max(100).default(10).describe('Items per page'),
    search: z.string().nullish().describe('Search query'),
});
export type UserListRequest = z.infer<typeof UserListRequest>;

/**
 * User search request schema
 */
export const UserSearchRequest = z.object({
    search: z.string().nullish().describe('Search query'),
});
export type UserSearchRequest = z.infer<typeof UserSearchRequest>;
