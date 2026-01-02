import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { resolve } from '$app/paths';

/**
 * Centralized API client for client-side fetch calls
 * Automatically includes credentials and handles auth errors
 */

export class ApiError extends Error {
    constructor(
        message: string,
        public status: number,
        public response?: unknown
    ) {
        super(message);
        this.name = 'ApiError';
    }
}

/**
 * Enhanced fetch wrapper that:
 * - Always includes credentials for cookie-based auth
 * - Handles 401 errors by redirecting to login
 * - Provides consistent error handling
 */
export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
    if (!browser) {
        throw new Error('apiFetch can only be used in the browser');
    }

    const response = await fetch(url, {
        credentials: 'include',
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
    });

    // Handle authentication errors by redirecting to login
    if (response.status === 401) {
        goto(resolve('/login'));
        throw new ApiError('Authentication required', 401);
    }

    return response;
}

/**
 * GET request with automatic error handling
 */
export async function apiGet<T = unknown>(url: string): Promise<T> {
    const response = await apiFetch(url);

    if (!response.ok) {
        throw new ApiError(`HTTP ${response.status}`, response.status);
    }

    return response.json();
}

/**
 * POST request with automatic error handling
 */
export async function apiPost<T = unknown>(url: string, data?: unknown): Promise<T> {
    const response = await apiFetch(url, {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined,
    });

    if (!response.ok) {
        throw new ApiError(`HTTP ${response.status}`, response.status);
    }

    return response.json();
}

/**
 * PUT request with automatic error handling
 */
export async function apiPut<T = unknown>(url: string, data?: unknown): Promise<T> {
    const response = await apiFetch(url, {
        method: 'PUT',
        body: data ? JSON.stringify(data) : undefined,
    });

    if (!response.ok) {
        throw new ApiError(`HTTP ${response.status}`, response.status);
    }

    return response.json();
}

/**
 * DELETE with automatic error handling
 */
export async function apiDelete(url: string): Promise<void> {
    const response = await apiFetch(url, {
        method: 'DELETE',
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
            errorData.detail || errorData.message || 'API request failed',
            response.status,
            errorData
        );
    }
}
