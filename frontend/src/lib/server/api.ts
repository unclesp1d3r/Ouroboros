import { env } from '$env/dynamic/private';
import { error } from '@sveltejs/kit';
import axios, {
    type AxiosInstance,
    type AxiosRequestConfig,
    type AxiosResponse,
    isAxiosError,
} from 'axios';
import { z } from 'zod';

/**
 * Server-side API client for Ouroboros backend
 * This client is designed to be used in +page.server.ts files and server actions
 */
export class ServerApiClient {
    private client: AxiosInstance;
    private baseURL: string;

    constructor(baseURL?: string) {
        this.baseURL = baseURL || env.API_BASE_URL || 'http://localhost:8000';
        this.client = axios.create({
            baseURL: this.baseURL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
                Accept: 'application/json',
            },
        });

        // Request interceptor for logging and auth
        this.client.interceptors.request.use(
            (config) => {
                if (process.env.NODE_ENV === 'development') {
                    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
                }
                return config;
            },
            (error) => {
                console.error('[API] Request error:', error);
                return Promise.reject(error);
            }
        );

        // Response interceptor for error handling
        this.client.interceptors.response.use(
            (response) => response,
            (error) => {
                if (error.response) {
                    console.error(
                        `[API] Response error ${error.response.status}:`,
                        error.response.data
                    );
                } else if (error.request) {
                    console.error('[API] Network error:', error.message);
                } else {
                    console.error('[API] Request setup error:', error.message);
                }
                return Promise.reject(error);
            }
        );
    }

    /**
     * Set authentication headers for requests
     */
    setAuth(token: string) {
        this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }

    /**
     * Set session cookie for requests
     */
    setSessionCookie(cookie: string) {
        this.client.defaults.headers.common['Cookie'] = cookie;
    }

    /**
     * Generic GET request with Zod validation
     */
    async get<T>(url: string, schema: z.ZodSchema<T>, config?: AxiosRequestConfig): Promise<T> {
        try {
            const response = await this.client.get(url, config);
            return schema.parse(response.data);
        } catch (err) {
            this.handleError(err, 'GET', url);
        }
    }

    /**
     * Generic POST request with Zod validation
     */
    async post<T>(
        url: string,
        data: unknown,
        schema: z.ZodSchema<T>,
        config?: AxiosRequestConfig
    ): Promise<T> {
        try {
            const response = await this.client.post(url, data, config);
            return schema.parse(response.data);
        } catch (err) {
            this.handleError(err, 'POST', url);
        }
    }

    /**
     * Generic PUT request with Zod validation
     */
    async put<T>(
        url: string,
        data: unknown,
        schema: z.ZodSchema<T>,
        config?: AxiosRequestConfig
    ): Promise<T> {
        try {
            const response = await this.client.put(url, data, config);
            return schema.parse(response.data);
        } catch (err) {
            this.handleError(err, 'PUT', url);
        }
    }

    /**
     * Generic PATCH request with Zod validation
     */
    async patch<T>(
        url: string,
        data: unknown,
        schema: z.ZodSchema<T>,
        config?: AxiosRequestConfig
    ): Promise<T> {
        try {
            const response = await this.client.patch(url, data, config);
            return schema.parse(response.data);
        } catch (err) {
            this.handleError(err, 'PATCH', url);
        }
    }

    /**
     * Generic DELETE request with Zod validation
     */
    async delete<T>(url: string, schema: z.ZodSchema<T>, config?: AxiosRequestConfig): Promise<T> {
        try {
            const response = await this.client.delete(url, config);
            return schema.parse(response.data);
        } catch (err) {
            this.handleError(err, 'DELETE', url);
        }
    }

    /**
     * Raw request methods without Zod validation (for cases where validation is handled elsewhere)
     */
    async getRaw(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
        try {
            return await this.client.get(url, config);
        } catch (err) {
            this.handleError(err, 'GET', url);
        }
    }

    async postRaw(
        url: string,
        data?: unknown,
        config?: AxiosRequestConfig
    ): Promise<AxiosResponse> {
        try {
            return await this.client.post(url, data, config);
        } catch (err) {
            this.handleError(err, 'POST', url);
        }
    }

    async putRaw(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse> {
        try {
            return await this.client.put(url, data, config);
        } catch (err) {
            this.handleError(err, 'PUT', url);
        }
    }

    async patchRaw(
        url: string,
        data?: unknown,
        config?: AxiosRequestConfig
    ): Promise<AxiosResponse> {
        try {
            return await this.client.patch(url, data, config);
        } catch (err) {
            this.handleError(err, 'PATCH', url);
        }
    }

    async deleteRaw(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
        try {
            return await this.client.delete(url, config);
        } catch (err) {
            this.handleError(err, 'DELETE', url);
        }
    }

    /**
     * Handle API errors and convert them to SvelteKit errors
     */
    private handleError(err: unknown, method: string, url: string): never {
        if (isAxiosError(err)) {
            const status = err.response?.status || 500;
            const message = err.response?.data?.detail || err.message || 'API request failed';

            console.error(`[API] ${method} ${url} failed with status ${status}:`, message);

            // Convert to SvelteKit error
            throw error(status, typeof message === 'string' ? message : 'API request failed');
        }

        console.error(`[API] ${method} ${url} failed:`, err);
        throw error(500, 'Internal server error');
    }
}

/**
 * Default server API client instance
 */
export const serverApi = new ServerApiClient();

/**
 * Create a server API client with authentication
 */
export function createAuthenticatedServerApi(token: string): ServerApiClient {
    const client = new ServerApiClient();
    client.setAuth(token);
    return client;
}

/**
 * Create a server API client with session cookie
 */
export function createSessionServerApi(cookie: string): ServerApiClient {
    const client = new ServerApiClient();
    client.setSessionCookie(cookie);
    return client;
}

// Common Zod schemas for API responses
export const ApiErrorSchema = z.object({
    detail: z.union([
        z.string(),
        z.array(
            z.object({
                msg: z.string(),
                loc: z.array(z.union([z.string(), z.number()])),
                type: z.string().optional(),
            })
        ),
    ]),
});

export const PaginatedResponseSchema = <T>(itemSchema: z.ZodSchema<T>) =>
    z.object({
        items: z.array(itemSchema),
        total: z.number(),
        page: z.number().optional(),
        page_size: z.number().optional(),
        search: z.string().optional().nullable(),
    });

export const SuccessResponseSchema = z.object({
    message: z.string(),
    success: z.boolean().optional(),
});

// Export types for use in server files
export type ApiError = z.infer<typeof ApiErrorSchema>;
export type PaginatedResponse<T> = {
    items: T[];
    total: number;
    page?: number;
    page_size?: number;
    search?: string | null;
};
export type SuccessResponse = z.infer<typeof SuccessResponseSchema>;
