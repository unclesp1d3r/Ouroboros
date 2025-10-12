/**
 * Authentication schemas for Ouroboros
 * Used by /api/v1/auth/* and /api/v1/web/auth/* endpoints
 */

import { z } from 'zod';
import { LoginResultLevel } from './base';

// Login request/response schemas
/**
 * Login request schema
 * Standard email/password authentication request
 */
export const LoginRequest = z.object({
    email: z.string(),
    password: z.string(),
});
export type LoginRequest = z.infer<typeof LoginRequest>;

/**
 * Login schema for forms
 * Form validation schema for login forms
 */
export const loginSchema = z.object({
    email: z
        .string()
        .min(1, 'Please enter a valid email address')
        .email('Please enter a valid email address'),
    password: z.string().min(1, 'Password is required'),
    remember: z.boolean().default(false).optional(),
});
export type LoginSchema = z.infer<typeof loginSchema>;

/**
 * JWT login request schema
 * Form-based JWT authentication request
 */
export const JwtLoginRequest = z.object({
    email: z.string(),
    password: z.string(),
});
export type JwtLoginRequest = z.infer<typeof JwtLoginRequest>;

/**
 * Login result schema
 * Response containing login status and nullish message
 */
export const LoginResult = z.object({
    message: z.string(),
    level: LoginResultLevel,
    access_token: z.string().nullish(),
});
export type LoginResult = z.infer<typeof LoginResult>;

/**
 * Change password request schema
 * Request to change user password with current password verification
 */
export const ChangePasswordRequest = z.object({
    old_password: z.string(),
    new_password: z.string(),
    new_password_confirm: z.string(),
});
export type ChangePasswordRequest = z.infer<typeof ChangePasswordRequest>;

/**
 * Refresh token request schema
 * Request to refresh JWT token using refresh token
 */
export const RefreshTokenRequest = z.object({
    auto_refresh: z.boolean().default(false),
});
export type RefreshTokenRequest = z.infer<typeof RefreshTokenRequest>;

// Context schemas
/**
 * User context detail schema
 * Information about the currently authenticated user
 */
export const UserContextDetail = z.object({
    id: z.string(),
    email: z.string(),
    name: z.string(),
    role: z.string(),
});
export type UserContextDetail = z.infer<typeof UserContextDetail>;

/**
 * Project context detail schema
 * Information about the user's current project context
 */
export const ProjectContextDetail = z.object({
    id: z.number(),
    name: z.string(),
});
export type ProjectContextDetail = z.infer<typeof ProjectContextDetail>;

/**
 * Context response schema
 * Combined user and project context information
 */
export const ContextResponse = z.object({
    user: UserContextDetail,
    active_project: ProjectContextDetail.nullable(),
    available_projects: z.array(ProjectContextDetail),
});
export type ContextResponse = z.infer<typeof ContextResponse>;

// Export alias for contextResponseSchema
export const contextResponseSchema = ContextResponse;

/**
 * Set context request schema
 * Request to change the user's current project context
 */
export const SetContextRequest = z.object({
    project_id: z.number(),
});
export type SetContextRequest = z.infer<typeof SetContextRequest>;

// API Key schemas
/**
 * API key information response schema
 * Information about user's API keys and permissions
 */
export const ApiKeyInfoResponse = z.object({
    has_api_key: z.boolean(),
    key_prefix: z.string().nullish(),
    created_at: z.string().nullish(),
});
export type ApiKeyInfoResponse = z.infer<typeof ApiKeyInfoResponse>;

/**
 * API key rotation response schema
 * Response when generating or rotating API keys
 */
export const ApiKeyRotationResponse = z.object({
    api_key: z.string(),
    message: z.string(),
});
export type ApiKeyRotationResponse = z.infer<typeof ApiKeyRotationResponse>;

// Form body schemas for API endpoints
/**
 * Login form body schema
 * Form data for web-based login endpoint
 */
export const Body_login_api_v1_web_auth_login_post = z.object({
    email: z
        .string()
        .max(255)
        .min(1)
        .regex(/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/),
    password: z.string().max(255).min(1),
});
export type Body_login_api_v1_web_auth_login_post = z.infer<
    typeof Body_login_api_v1_web_auth_login_post
>;

/**
 * JWT login form body schema
 * Form data for JWT-based login endpoint
 */
export const Body_jwt_login_api_v1_auth_jwt_login_post = z.object({
    email: z.string(),
    password: z.string(),
});
export type Body_jwt_login_api_v1_auth_jwt_login_post = z.infer<
    typeof Body_jwt_login_api_v1_auth_jwt_login_post
>;

/**
 * Change password form body schema
 * Form data for password change endpoint
 */
export const Body_change_password_api_v1_web_auth_change_password_post = z.object({
    old_password: z.string(),
    new_password: z.string(),
    new_password_confirm: z.string(),
});
export type Body_change_password_api_v1_web_auth_change_password_post = z.infer<
    typeof Body_change_password_api_v1_web_auth_change_password_post
>;

/**
 * Refresh token form body schema
 * Form data for token refresh endpoint
 */
export const Body_refresh_token_api_v1_web_auth_refresh_post = z.object({
    auto_refresh: z.boolean().default(false),
});
export type Body_refresh_token_api_v1_web_auth_refresh_post = z.infer<
    typeof Body_refresh_token_api_v1_web_auth_refresh_post
>;

/**
 * User session schema
 * Frontend user session state representation
 */
export const UserSession = z.object({
    id: z.string(),
    email: z.string(),
    name: z.string().nullish(),
    username: z.string().nullish(),
    role: z.enum(['admin', 'project_admin', 'user', 'operator', 'analyst']),
    projects: z
        .array(
            z.object({
                id: z.number(),
                name: z.string(),
                role: z.string(),
            })
        )
        .nullish(),
    current_project_id: z.number().nullish(),
    is_authenticated: z.boolean(),
});
export type UserSession = z.infer<typeof UserSession>;
