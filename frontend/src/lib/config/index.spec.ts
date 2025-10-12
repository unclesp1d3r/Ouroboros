import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { AppConfig } from './index';

// Mock SvelteKit modules
vi.mock('$app/environment', () => ({
    browser: false,
}));

vi.mock('$env/dynamic/private', () => ({
    env: {},
}));

vi.mock('$env/dynamic/public', () => ({
    env: {},
}));

vi.mock('$env/static/private', () => ({
    API_BASE_URL: undefined,
    VITE_API_BASE_URL: undefined,
    VITE_TOKEN_EXPIRE_MINUTES: undefined,
    VITE_DEBUG: undefined,
    VITE_APP_NAME: undefined,
    VITE_APP_VERSION: undefined,
    VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
}));

vi.mock('$env/static/public', () => ({
    PUBLIC_API_BASE_URL: undefined,
}));

describe('Configuration System', () => {
    beforeEach(() => {
        // Reset modules before each test
        vi.resetModules();
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    describe('Default Configuration', () => {
        it('should load default configuration values', async () => {
            const { config } = await import('./index');

            expect(config.apiBaseUrl).toBe('http://localhost:8000');
            expect(config.publicApiBaseUrl).toBe('http://localhost:8000');
            expect(config.tokenExpireMinutes).toBe(60);
            expect(config.debug).toBe(false);
            expect(config.appName).toBe('Ouroboros');
            expect(config.appVersion).toBe('2.0.0');
            expect(config.enableExperimentalFeatures).toBe(false);
        });

        it('should have valid default URLs', async () => {
            const { config } = await import('./index');

            expect(() => new URL(config.apiBaseUrl)).not.toThrow();
            expect(() => new URL(config.publicApiBaseUrl)).not.toThrow();
        });
    });

    describe('Environment Variable Loading', () => {
        it('should load server-side environment variables', async () => {
            vi.doMock('$env/dynamic/private', () => ({
                env: {
                    API_BASE_URL: 'http://api.example.com',
                    VITE_TOKEN_EXPIRE_MINUTES: '120',
                    VITE_DEBUG: 'true',
                    VITE_APP_NAME: 'Ouroboros Dev',
                    VITE_APP_VERSION: '2.1.0',
                    VITE_ENABLE_EXPERIMENTAL_FEATURES: 'true',
                },
            }));

            vi.doMock('$env/static/private', () => ({
                API_BASE_URL: undefined,
                VITE_API_BASE_URL: undefined,
                VITE_TOKEN_EXPIRE_MINUTES: undefined,
                VITE_DEBUG: undefined,
                VITE_APP_NAME: undefined,
                VITE_APP_VERSION: undefined,
                VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
            }));

            const { config } = await import('./index');

            expect(config.apiBaseUrl).toBe('http://api.example.com');
            expect(config.tokenExpireMinutes).toBe(120);
            expect(config.debug).toBe(true);
            expect(config.appName).toBe('Ouroboros Dev');
            expect(config.appVersion).toBe('2.1.0');
            expect(config.enableExperimentalFeatures).toBe(true);
        });

        it('should load public environment variables', async () => {
            vi.doMock('$env/dynamic/public', () => ({
                env: {
                    PUBLIC_API_BASE_URL: 'http://public.example.com',
                },
            }));

            vi.doMock('$env/static/public', () => ({
                PUBLIC_API_BASE_URL: undefined,
            }));

            const { config } = await import('./index');

            expect(config.publicApiBaseUrl).toBe('http://public.example.com');
        });

        it('should prioritize API_BASE_URL over VITE_API_BASE_URL', async () => {
            vi.doMock('$env/dynamic/private', () => ({
                env: {
                    API_BASE_URL: 'http://priority.example.com',
                    VITE_API_BASE_URL: 'http://fallback.example.com',
                },
            }));

            vi.doMock('$env/static/private', () => ({
                API_BASE_URL: undefined,
                VITE_API_BASE_URL: undefined,
                VITE_TOKEN_EXPIRE_MINUTES: undefined,
                VITE_DEBUG: undefined,
                VITE_APP_NAME: undefined,
                VITE_APP_VERSION: undefined,
                VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
            }));

            const { config } = await import('./index');

            expect(config.apiBaseUrl).toBe('http://priority.example.com');
        });

        it('should fall back to VITE_API_BASE_URL when API_BASE_URL is not set', async () => {
            vi.doMock('$env/dynamic/private', () => ({
                env: {
                    VITE_API_BASE_URL: 'http://fallback.example.com',
                },
            }));

            vi.doMock('$env/static/private', () => ({
                API_BASE_URL: undefined,
                VITE_API_BASE_URL: undefined,
                VITE_TOKEN_EXPIRE_MINUTES: undefined,
                VITE_DEBUG: undefined,
                VITE_APP_NAME: undefined,
                VITE_APP_VERSION: undefined,
                VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
            }));

            const { config } = await import('./index');

            expect(config.apiBaseUrl).toBe('http://fallback.example.com');
        });
    });

    describe('Browser vs Server Configuration', () => {
        it('should only load public config in browser environment', async () => {
            vi.doMock('$app/environment', () => ({
                browser: true,
            }));

            vi.doMock('$env/dynamic/private', () => ({
                env: {
                    API_BASE_URL: 'http://server-only.example.com',
                    VITE_DEBUG: 'true',
                },
            }));

            vi.doMock('$env/dynamic/public', () => ({
                env: {
                    PUBLIC_API_BASE_URL: 'http://public.example.com',
                },
            }));

            vi.doMock('$env/static/private', () => ({
                API_BASE_URL: undefined,
                VITE_API_BASE_URL: undefined,
                VITE_TOKEN_EXPIRE_MINUTES: undefined,
                VITE_DEBUG: undefined,
                VITE_APP_NAME: undefined,
                VITE_APP_VERSION: undefined,
                VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
            }));
            vi.doMock('$env/static/public', () => ({
                PUBLIC_API_BASE_URL: undefined,
            }));

            const { config } = await import('./index');

            // Should use default server config since we're in browser
            expect(config.apiBaseUrl).toBe('http://localhost:8000');
            expect(config.debug).toBe(false);

            // Should use public config
            expect(config.publicApiBaseUrl).toBe('http://public.example.com');
        });
    });

    describe('Utility Functions', () => {
        describe('getApiBaseUrl', () => {
            it('should return server API URL when not in browser', async () => {
                vi.doMock('$app/environment', () => ({
                    browser: false,
                }));

                vi.doMock('$env/dynamic/private', () => ({
                    env: {
                        API_BASE_URL: 'http://server.example.com',
                    },
                }));

                vi.doMock('$env/dynamic/public', () => ({
                    env: {
                        PUBLIC_API_BASE_URL: 'http://public.example.com',
                    },
                }));

                vi.doMock('$env/static/private', () => ({
                    API_BASE_URL: undefined,
                    VITE_API_BASE_URL: undefined,
                    VITE_TOKEN_EXPIRE_MINUTES: undefined,
                    VITE_DEBUG: undefined,
                    VITE_APP_NAME: undefined,
                    VITE_APP_VERSION: undefined,
                    VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
                }));
                vi.doMock('$env/static/public', () => ({
                    PUBLIC_API_BASE_URL: undefined,
                }));

                const { getApiBaseUrl } = await import('./index');

                expect(getApiBaseUrl()).toBe('http://server.example.com');
            });

            it('should return public API URL when in browser', async () => {
                vi.doMock('$app/environment', () => ({
                    browser: true,
                }));

                vi.doMock('$env/dynamic/public', () => ({
                    env: {
                        PUBLIC_API_BASE_URL: 'http://public.example.com',
                    },
                }));

                vi.doMock('$env/static/public', () => ({
                    PUBLIC_API_BASE_URL: undefined,
                }));

                const { getApiBaseUrl } = await import('./index');

                expect(getApiBaseUrl()).toBe('http://public.example.com');
            });
        });

        describe('getApiUrl', () => {
            it('should construct full API URLs correctly', async () => {
                vi.doMock('$app/environment', () => ({
                    browser: false,
                }));

                vi.doMock('$env/dynamic/private', () => ({
                    env: {
                        API_BASE_URL: 'http://api.example.com',
                    },
                }));

                vi.doMock('$env/dynamic/public', () => ({
                    env: {},
                }));

                vi.doMock('$env/static/private', () => ({
                    API_BASE_URL: undefined,
                    VITE_API_BASE_URL: undefined,
                    VITE_TOKEN_EXPIRE_MINUTES: undefined,
                    VITE_DEBUG: undefined,
                    VITE_APP_NAME: undefined,
                    VITE_APP_VERSION: undefined,
                    VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
                }));
                vi.doMock('$env/static/public', () => ({
                    PUBLIC_API_BASE_URL: undefined,
                }));

                const { getApiUrl } = await import('./index');

                expect(getApiUrl('/api/v1/web/campaigns')).toBe(
                    'http://api.example.com/api/v1/web/campaigns'
                );
                expect(getApiUrl('api/v1/web/campaigns')).toBe(
                    'http://api.example.com/api/v1/web/campaigns'
                );
            });
        });

        describe('isDevelopment', () => {
            it('should return true when debug is enabled', async () => {
                vi.doMock('$app/environment', () => ({
                    browser: false,
                }));

                vi.doMock('$env/dynamic/private', () => ({
                    env: {
                        VITE_DEBUG: 'true',
                    },
                }));

                vi.doMock('$env/dynamic/public', () => ({
                    env: {},
                }));

                vi.doMock('$env/static/private', () => ({
                    API_BASE_URL: undefined,
                    VITE_API_BASE_URL: undefined,
                    VITE_TOKEN_EXPIRE_MINUTES: undefined,
                    VITE_DEBUG: undefined,
                    VITE_APP_NAME: undefined,
                    VITE_APP_VERSION: undefined,
                    VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
                }));
                vi.doMock('$env/static/public', () => ({
                    PUBLIC_API_BASE_URL: undefined,
                }));

                const { isDevelopment } = await import('./index');

                expect(isDevelopment()).toBe(true);
            });

            it('should return true when app name contains "dev"', async () => {
                vi.doMock('$app/environment', () => ({
                    browser: false,
                }));

                vi.doMock('$env/dynamic/private', () => ({
                    env: {
                        VITE_APP_NAME: 'Ouroboros Dev',
                        VITE_DEBUG: 'false',
                    },
                }));

                vi.doMock('$env/dynamic/public', () => ({
                    env: {},
                }));

                vi.doMock('$env/static/private', () => ({
                    API_BASE_URL: undefined,
                    VITE_API_BASE_URL: undefined,
                    VITE_TOKEN_EXPIRE_MINUTES: undefined,
                    VITE_DEBUG: undefined,
                    VITE_APP_NAME: undefined,
                    VITE_APP_VERSION: undefined,
                    VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
                }));
                vi.doMock('$env/static/public', () => ({
                    PUBLIC_API_BASE_URL: undefined,
                }));

                const { isDevelopment } = await import('./index');

                expect(isDevelopment()).toBe(true);
            });

            it('should return false in production mode', async () => {
                vi.doMock('$app/environment', () => ({
                    browser: false,
                }));

                vi.doMock('$env/dynamic/private', () => ({
                    env: {
                        VITE_DEBUG: 'false',
                        VITE_APP_NAME: 'Ouroboros',
                    },
                }));

                vi.doMock('$env/dynamic/public', () => ({
                    env: {},
                }));

                vi.doMock('$env/static/private', () => ({
                    API_BASE_URL: undefined,
                    VITE_API_BASE_URL: undefined,
                    VITE_TOKEN_EXPIRE_MINUTES: undefined,
                    VITE_DEBUG: undefined,
                    VITE_APP_NAME: undefined,
                    VITE_APP_VERSION: undefined,
                    VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
                }));
                vi.doMock('$env/static/public', () => ({
                    PUBLIC_API_BASE_URL: undefined,
                }));

                const { isDevelopment } = await import('./index');

                expect(isDevelopment()).toBe(false);
            });
        });

        describe('isExperimentalEnabled', () => {
            it('should return true when experimental features are enabled', async () => {
                vi.doMock('$app/environment', () => ({
                    browser: false,
                }));

                vi.doMock('$env/dynamic/private', () => ({
                    env: {
                        VITE_ENABLE_EXPERIMENTAL_FEATURES: 'true',
                    },
                }));

                vi.doMock('$env/dynamic/public', () => ({
                    env: {},
                }));

                vi.doMock('$env/static/private', () => ({
                    API_BASE_URL: undefined,
                    VITE_API_BASE_URL: undefined,
                    VITE_TOKEN_EXPIRE_MINUTES: undefined,
                    VITE_DEBUG: undefined,
                    VITE_APP_NAME: undefined,
                    VITE_APP_VERSION: undefined,
                    VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
                }));
                vi.doMock('$env/static/public', () => ({
                    PUBLIC_API_BASE_URL: undefined,
                }));

                const { isExperimentalEnabled } = await import('./index');

                expect(isExperimentalEnabled()).toBe(true);
            });

            it('should return false when experimental features are disabled', async () => {
                vi.doMock('$app/environment', () => ({
                    browser: false,
                }));

                vi.doMock('$env/dynamic/private', () => ({
                    env: {},
                }));

                vi.doMock('$env/dynamic/public', () => ({
                    env: {},
                }));

                vi.doMock('$env/static/private', () => ({
                    API_BASE_URL: undefined,
                    VITE_API_BASE_URL: undefined,
                    VITE_TOKEN_EXPIRE_MINUTES: undefined,
                    VITE_DEBUG: undefined,
                    VITE_APP_NAME: undefined,
                    VITE_APP_VERSION: undefined,
                    VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
                }));
                vi.doMock('$env/static/public', () => ({
                    PUBLIC_API_BASE_URL: undefined,
                }));

                const { isExperimentalEnabled } = await import('./index');

                expect(isExperimentalEnabled()).toBe(false);
            });
        });
    });

    describe('Configuration Validation', () => {
        it('should throw error for invalid API base URL', async () => {
            vi.doMock('$app/environment', () => ({
                browser: false,
            }));

            vi.doMock('$env/dynamic/private', () => ({
                env: {
                    API_BASE_URL: 'invalid-url',
                },
            }));

            vi.doMock('$env/dynamic/public', () => ({
                env: {},
            }));

            vi.doMock('$env/static/private', () => ({
                API_BASE_URL: undefined,
                VITE_API_BASE_URL: undefined,
                VITE_TOKEN_EXPIRE_MINUTES: undefined,
                VITE_DEBUG: undefined,
                VITE_APP_NAME: undefined,
                VITE_APP_VERSION: undefined,
                VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
            }));
            vi.doMock('$env/static/public', () => ({
                PUBLIC_API_BASE_URL: undefined,
            }));

            await expect(import('./index')).rejects.toThrow('Configuration validation failed');
        });

        it('should throw error for invalid public API base URL', async () => {
            vi.doMock('$app/environment', () => ({
                browser: false,
            }));

            vi.doMock('$env/dynamic/private', () => ({
                env: {},
            }));

            vi.doMock('$env/dynamic/public', () => ({
                env: {
                    PUBLIC_API_BASE_URL: 'invalid-url',
                },
            }));

            vi.doMock('$env/static/private', () => ({
                API_BASE_URL: undefined,
                VITE_API_BASE_URL: undefined,
                VITE_TOKEN_EXPIRE_MINUTES: undefined,
                VITE_DEBUG: undefined,
                VITE_APP_NAME: undefined,
                VITE_APP_VERSION: undefined,
                VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
            }));
            vi.doMock('$env/static/public', () => ({
                PUBLIC_API_BASE_URL: undefined,
            }));

            await expect(import('./index')).rejects.toThrow('Configuration validation failed');
        });

        it('should throw error for invalid token expiration', async () => {
            vi.doMock('$app/environment', () => ({
                browser: false,
            }));

            vi.doMock('$env/dynamic/private', () => ({
                env: {
                    VITE_TOKEN_EXPIRE_MINUTES: '-1',
                },
            }));

            vi.doMock('$env/dynamic/public', () => ({
                env: {},
            }));

            vi.doMock('$env/static/private', () => ({
                API_BASE_URL: undefined,
                VITE_API_BASE_URL: undefined,
                VITE_TOKEN_EXPIRE_MINUTES: undefined,
                VITE_DEBUG: undefined,
                VITE_APP_NAME: undefined,
                VITE_APP_VERSION: undefined,
                VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
            }));
            vi.doMock('$env/static/public', () => ({
                PUBLIC_API_BASE_URL: undefined,
            }));

            await expect(import('./index')).rejects.toThrow('Configuration validation failed');
        });

        it('should throw error for empty app name', async () => {
            vi.doMock('$app/environment', () => ({
                browser: false,
            }));

            vi.doMock('$env/dynamic/private', () => ({
                env: {
                    VITE_APP_NAME: '   ',
                },
            }));

            vi.doMock('$env/dynamic/public', () => ({
                env: {},
            }));

            vi.doMock('$env/static/private', () => ({
                API_BASE_URL: undefined,
                VITE_API_BASE_URL: undefined,
                VITE_TOKEN_EXPIRE_MINUTES: undefined,
                VITE_DEBUG: undefined,
                VITE_APP_NAME: undefined,
                VITE_APP_VERSION: undefined,
                VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
            }));
            vi.doMock('$env/static/public', () => ({
                PUBLIC_API_BASE_URL: undefined,
            }));

            await expect(import('./index')).rejects.toThrow('Configuration validation failed');
        });
    });

    describe('Type Safety', () => {
        it('should export AppConfig interface', async () => {
            vi.doMock('$app/environment', () => ({
                browser: false,
            }));

            vi.doMock('$env/dynamic/private', () => ({
                env: {},
            }));

            vi.doMock('$env/dynamic/public', () => ({
                env: {},
            }));

            vi.doMock('$env/static/private', () => ({
                API_BASE_URL: undefined,
                VITE_API_BASE_URL: undefined,
                VITE_TOKEN_EXPIRE_MINUTES: undefined,
                VITE_DEBUG: undefined,
                VITE_APP_NAME: undefined,
                VITE_APP_VERSION: undefined,
                VITE_ENABLE_EXPERIMENTAL_FEATURES: undefined,
            }));
            vi.doMock('$env/static/public', () => ({
                PUBLIC_API_BASE_URL: undefined,
            }));

            const module = await import('./index');

            // This test ensures the interface is exported and can be used
            const testConfig: AppConfig = {
                apiBaseUrl: 'http://test.com',
                publicApiBaseUrl: 'http://test.com',
                tokenExpireMinutes: 30,
                debug: true,
                appName: 'Test App',
                appVersion: '1.0.0',
                enableExperimentalFeatures: false,
            };

            expect(testConfig).toBeDefined();
            expect(typeof testConfig.apiBaseUrl).toBe('string');
            expect(typeof testConfig.tokenExpireMinutes).toBe('number');
            expect(typeof testConfig.debug).toBe('boolean');
        });
    });
});
