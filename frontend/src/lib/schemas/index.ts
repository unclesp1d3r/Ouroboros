/**
 * Ouroboros Frontend Schema Library
 *
 * This module re-exports and organizes Zod schemas generated from the OpenAPI specification,
 * filtered for schemas relevant to `/api/v1/auth` and `/api/v1/web` endpoints.
 *
 * Organized by domain for better developer experience and maintainability.
 */

// Re-export all base schemas from generated file
export * from './base';

// Domain-specific schema exports
export * from './auth';
export * from './campaigns';
export * from './attacks';
export * from './agents';
export * from './projects';
export * from './users';
export * from './resources';
export * from './hashlists';
export * from './uploads';
export * from './dashboard';
export * from './health';
export * from './common';
