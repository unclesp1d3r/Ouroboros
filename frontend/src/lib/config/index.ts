import { browser } from '$app/environment';
import { env } from '$env/dynamic/private';
import { env as publicEnv } from '$env/dynamic/public';
import * as staticEnv from '$env/static/private';
import * as staticPublicEnv from '$env/static/public';

/**
 * Configuration schema for type safety
 */
export interface AppConfig {
    /** Backend API base URL for server-side requests */
    apiBaseUrl: string;
    /** Public API base URL for client-side requests */
    publicApiBaseUrl: string;
    /** JWT token expiration time in minutes */
    tokenExpireMinutes: number;
    /** Enable debug mode */
    debug: boolean;
    /** Application name */
    appName: string;
    /** Application version */
    appVersion: string;
    /** Enable experimental features */
    enableExperimentalFeatures: boolean;
}

/**
 * Default configuration values
 */
const defaultConfig: AppConfig = {
    apiBaseUrl: 'http://localhost:8000',
    publicApiBaseUrl: 'http://localhost:8000',
    tokenExpireMinutes: 60,
    debug: false, // Default to false, enable via environment variable
    appName: 'Ouroboros',
    appVersion: '2.0.0',
    enableExperimentalFeatures: false,
};

/**
 * Load configuration from environment variables with type safety
 */
function loadConfig(): AppConfig {
    // Server-side configuration (private env vars)
    // Use static env during prerendering, dynamic env during runtime
    const serverConfig = browser
        ? {}
        : {
              apiBaseUrl:
                  staticEnv.API_BASE_URL ||
                  env.API_BASE_URL ||
                  env.VITE_API_BASE_URL ||
                  defaultConfig.apiBaseUrl,
              tokenExpireMinutes: parseInt(
                  env.VITE_TOKEN_EXPIRE_MINUTES || String(defaultConfig.tokenExpireMinutes),
                  10
              ),
              debug:
                  env.VITE_DEBUG === 'true' ||
                  (env.VITE_DEBUG === undefined && defaultConfig.debug),
              appName: env.VITE_APP_NAME || defaultConfig.appName,
              appVersion: env.VITE_APP_VERSION || defaultConfig.appVersion,
              enableExperimentalFeatures:
                  env.VITE_ENABLE_EXPERIMENTAL_FEATURES === 'true' ||
                  defaultConfig.enableExperimentalFeatures,
          };

    // Client-side configuration (public env vars)
    const clientConfig = {
        publicApiBaseUrl:
            staticPublicEnv.PUBLIC_API_BASE_URL ||
            publicEnv.PUBLIC_API_BASE_URL ||
            defaultConfig.publicApiBaseUrl,
    };

    return {
        ...defaultConfig,
        ...serverConfig,
        ...clientConfig,
    };
}

/**
 * Application configuration instance
 */
export const config: AppConfig = loadConfig();

/**
 * Get the appropriate API base URL based on environment
 * @returns API base URL for the current environment (server or client)
 */
export function getApiBaseUrl(): string {
    return browser ? config.publicApiBaseUrl : config.apiBaseUrl;
}

/**
 * Check if we're in development mode
 */
export function isDevelopment(): boolean {
    return config.debug || config.appName.toLowerCase().includes('dev');
}

/**
 * Check if experimental features are enabled
 */
export function isExperimentalEnabled(): boolean {
    return config.enableExperimentalFeatures;
}

/**
 * Get full API endpoint URL
 * @param endpoint - API endpoint path (e.g., '/api/v1/web/campaigns')
 * @returns Full URL to the API endpoint
 */
export function getApiUrl(endpoint: string): string {
    const baseUrl = getApiBaseUrl();
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${baseUrl}${cleanEndpoint}`;
}

/**
 * Configuration validation
 */
function validateConfig(config: AppConfig): void {
    const errors: string[] = [];

    // Validate URLs
    try {
        void new URL(config.apiBaseUrl);
    } catch {
        errors.push(`Invalid API base URL: ${config.apiBaseUrl}`);
    }

    try {
        void new URL(config.publicApiBaseUrl);
    } catch {
        errors.push(`Invalid public API base URL: ${config.publicApiBaseUrl}`);
    }

    // Validate token expiration
    if (config.tokenExpireMinutes <= 0) {
        errors.push(`Token expiration must be positive: ${config.tokenExpireMinutes}`);
    }

    // Validate app name
    if (!config.appName.trim()) {
        errors.push('App name cannot be empty');
    }

    if (errors.length > 0) {
        throw new Error(`Configuration validation failed:\n${errors.join('\n')}`);
    }
}

// Validate configuration on load
validateConfig(config);
