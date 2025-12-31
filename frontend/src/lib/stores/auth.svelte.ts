import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { resolve } from '$app/paths';
import {
    Body_login_api_v1_web_auth_login_post,
    ChangePasswordRequest,
    ContextResponse,
    LoginResult,
    SetContextRequest,
    UserSession,
} from '$lib/schemas/auth';

// Authentication state
const authState = $state({
    user: null as UserSession | null,
    loading: false,
    error: null as string | null,
    isAuthenticated: false,
});

// Derived state
const currentUser = $derived(authState.user);
const isAdmin = $derived(authState.user?.role === 'admin');
const isProjectAdmin = $derived(authState.user?.role === 'project_admin' || isAdmin);
const currentProject = $derived(
    authState.user?.projects?.find((p) => p.id === authState.user?.current_project_id)
);

// Import SSE service for reconnection after auth recovery
let sseService: { reconnectAfterAuth: () => void } | null = null;
if (browser) {
    void import('$lib/services/sse').then((module) => {
        sseService = module.sseService;
        return null;
    });
}

// Token refresh function
async function refreshSession(): Promise<boolean> {
    if (!browser) return false;

    try {
        const response = await fetch('/api/v1/web/auth/refresh', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ auto_refresh: true }),
        });

        if (response.ok) {
            const data = await response.json();
            const loginResult = LoginResult.parse(data);

            // Backend returns either "Session refreshed." or "Token is still valid."
            if (
                loginResult.message === 'Session refreshed.' ||
                loginResult.message === 'Token is still valid.'
            ) {
                // Get updated user context after refresh
                const contextResponse = await fetch('/api/v1/web/auth/context', {
                    credentials: 'include',
                });

                if (contextResponse.ok) {
                    const contextData = ContextResponse.parse(await contextResponse.json());
                    const wasAuthenticated = authState.isAuthenticated;

                    authState.user = {
                        id: contextData.user.id,
                        email: contextData.user.email,
                        name: contextData.user.name,
                        role: contextData.user.role as UserSession['role'],
                        projects: contextData.available_projects.map((p) => ({
                            id: p.id,
                            name: p.name,
                            role: 'member', // Default role, should be enhanced with actual role data
                        })),
                        current_project_id: contextData.active_project?.id,
                        is_authenticated: true,
                    };
                    authState.isAuthenticated = true;

                    // If authentication was restored, reconnect SSE streams
                    if (!wasAuthenticated && sseService) {
                        sseService.reconnectAfterAuth();
                    }

                    return true;
                }
            }
        }
    } catch (error) {
        console.error('Token refresh failed:', error);
        // If refresh fails, mark as unauthenticated so the interval will stop
        authState.isAuthenticated = false;
    }

    return false;
}

// Automatic token refresh setup
if (browser) {
    // Check session more frequently - every 2 minutes instead of 5
    // Since tokens expire in 1 hour, this gives us plenty of opportunities to refresh
    setInterval(
        async () => {
            // Continue refreshing even if authState.isAuthenticated is false
            // This handles cases where tokens become corrupted but cookies still exist
            const hasSessionCookie = document.cookie.includes('access_token=');
            if (authState.isAuthenticated || hasSessionCookie) {
                const refreshed = await refreshSession();
                if (!refreshed && authState.isAuthenticated) {
                    // Only redirect if we were previously authenticated but refresh failed
                    // This prevents redirect loops when already on login page
                    authState.user = null;
                    authState.isAuthenticated = false;
                    if (!window.location.pathname.includes('/login')) {
                        goto(resolve('/login'));
                    }
                }
            }
        },
        2 * 60 * 1000
    ); // 2 minutes

    // Also add a more frequent heartbeat for active sessions
    setInterval(async () => {
        if (authState.isAuthenticated) {
            // Just ping the context endpoint to verify session is still valid
            try {
                const response = await fetch('/api/v1/web/auth/context', {
                    credentials: 'include',
                });
                if (!response.ok && response.status === 401) {
                    // Token expired during active session
                    const refreshed = await refreshSession();
                    if (!refreshed) {
                        authState.user = null;
                        authState.isAuthenticated = false;
                        if (!window.location.pathname.includes('/login')) {
                            goto(resolve('/login'));
                        }
                    }
                }
            } catch (error) {
                console.warn('Session heartbeat failed:', error);
            }
        }
    }, 30 * 1000); // 30 seconds heartbeat
}

// Authentication store
export const authStore = {
    // Getters for reactive state
    get user() {
        return currentUser;
    },
    get loading() {
        return authState.loading;
    },
    get error() {
        return authState.error;
    },
    get isAuthenticated() {
        return authState.isAuthenticated;
    },
    get isAdmin() {
        return isAdmin;
    },
    get isProjectAdmin() {
        return isProjectAdmin;
    },
    get currentProject() {
        return currentProject;
    },

    // Actions
    setUser(user: UserSession) {
        authState.user = user;
        authState.isAuthenticated = true;
        authState.error = null;
    },

    setLoading(loading: boolean) {
        authState.loading = loading;
    },

    setError(error: string | null) {
        authState.error = error;
    },

    async login(email: string, password: string, remember: boolean = false): Promise<boolean> {
        if (!browser) return false;

        authState.loading = true;
        authState.error = null;

        try {
            // Validate input data
            const loginData = Body_login_api_v1_web_auth_login_post.parse({
                email,
                password,
            });

            // Create form data as expected by the FastAPI endpoint
            const formData = new FormData();
            formData.append('email', loginData.email);
            formData.append('password', loginData.password);

            const response = await fetch('/api/v1/web/auth/login', {
                method: 'POST',
                credentials: 'include',
                body: formData,
            });

            const data = await response.json();

            if (response.ok) {
                const loginResult = LoginResult.parse(data);

                if (loginResult.message === 'Login successful.') {
                    // Login successful, now get user context
                    const authSuccess = await this.checkAuth();
                    if (authSuccess) {
                        return true;
                    } else {
                        authState.error = 'Login succeeded but failed to get user data';
                        return false;
                    }
                } else {
                    authState.error = loginResult.message;
                    return false;
                }
            } else {
                authState.error = data.detail || data.error || 'Login failed';
                return false;
            }
        } catch (error) {
            if (error instanceof Error) {
                authState.error = error.message;
            } else {
                authState.error = 'Network error. Please try again.';
            }
            return false;
        } finally {
            authState.loading = false;
        }
    },

    async logout(): Promise<void> {
        if (!browser) return;

        try {
            await fetch('/api/v1/web/auth/logout', {
                method: 'POST',
                credentials: 'include',
            });
        } catch (error) {
            console.error('Logout API call failed:', error);
        } finally {
            // Clear state regardless of API response
            authState.user = null;
            authState.isAuthenticated = false;
            authState.error = null;
            goto(resolve('/login'));
        }
    },

    async switchProject(projectId: number): Promise<boolean> {
        if (!browser || !authState.user) return false;

        try {
            const requestData = SetContextRequest.parse({ project_id: projectId });

            const response = await fetch('/api/v1/web/auth/context', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(requestData),
            });

            if (response.ok) {
                const contextData = ContextResponse.parse(await response.json());

                // Update user with new context
                authState.user = {
                    ...authState.user,
                    current_project_id: contextData.active_project?.id,
                    projects: contextData.available_projects.map((p) => ({
                        id: p.id,
                        name: p.name,
                        role:
                            authState.user?.projects?.find((up) => up.id === p.id)?.role ||
                            'member',
                    })),
                };
                return true;
            }
        } catch (error) {
            console.error('Project switch failed:', error);
        }

        return false;
    },

    async changePassword(
        oldPassword: string,
        newPassword: string,
        confirmPassword: string
    ): Promise<boolean> {
        if (!browser) return false;

        try {
            const requestData = ChangePasswordRequest.parse({
                old_password: oldPassword,
                new_password: newPassword,
                new_password_confirm: confirmPassword,
            });

            const response = await fetch('/api/v1/web/auth/change_password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(requestData),
            });

            if (response.ok) {
                const result = LoginResult.parse(await response.json());
                return result.message === 'Password changed successfully.';
            }
        } catch (error) {
            console.error('Password change failed:', error);
        }

        return false;
    },

    // Check authentication status
    async checkAuth(): Promise<boolean> {
        if (!browser) return false;

        try {
            const response = await fetch('/api/v1/web/auth/context', {
                credentials: 'include',
            });

            if (response.ok) {
                const contextData = ContextResponse.parse(await response.json());
                const wasAuthenticated = authState.isAuthenticated;

                // If user has no active project but has available projects, automatically select the first one
                if (!contextData.active_project && contextData.available_projects.length > 0) {
                    const firstProject = contextData.available_projects[0];
                    console.log(
                        `[Auth] No active project found, auto-selecting first project: ${firstProject.name}`
                    );

                    // Set the project context via API
                    const switchSuccess = await this.switchProject(firstProject.id);
                    if (switchSuccess) {
                        // Refetch context to get updated data with active project
                        const updatedResponse = await fetch('/api/v1/web/auth/context', {
                            credentials: 'include',
                        });
                        if (updatedResponse.ok) {
                            const updatedContextData = ContextResponse.parse(
                                await updatedResponse.json()
                            );
                            authState.user = {
                                id: updatedContextData.user.id,
                                email: updatedContextData.user.email,
                                name: updatedContextData.user.name,
                                role: updatedContextData.user.role as UserSession['role'],
                                projects: updatedContextData.available_projects.map((p) => ({
                                    id: p.id,
                                    name: p.name,
                                    role: 'member', // Default role, should be enhanced with actual role data
                                })),
                                current_project_id: updatedContextData.active_project?.id,
                                is_authenticated: true,
                            };
                        }
                    }
                } else {
                    // Normal case: user already has active project or no projects available
                    authState.user = {
                        id: contextData.user.id,
                        email: contextData.user.email,
                        name: contextData.user.name,
                        role: contextData.user.role as UserSession['role'],
                        projects: contextData.available_projects.map((p) => ({
                            id: p.id,
                            name: p.name,
                            role: 'member', // Default role, should be enhanced with actual role data
                        })),
                        current_project_id: contextData.active_project?.id,
                        is_authenticated: true,
                    };
                }

                authState.isAuthenticated = true;

                // If authentication was restored (first login, page refresh, etc.), reconnect SSE streams
                if (!wasAuthenticated && sseService) {
                    sseService.reconnectAfterAuth();
                }

                return true;
            }
        } catch (error) {
            console.error('Auth check failed:', error);
        }

        authState.user = null;
        authState.isAuthenticated = false;
        return false;
    },

    // Hydrate from SSR data
    hydrate(user: UserSession | null) {
        if (user) {
            authState.user = user;
            authState.isAuthenticated = true;
        } else {
            authState.user = null;
            authState.isAuthenticated = false;
        }
        authState.loading = false;
        authState.error = null;
    },

    // Check permissions
    hasProjectAccess(projectId: number): boolean {
        if (!authState.user) return false;
        if (authState.user.role === 'admin') return true;
        return authState.user.projects?.some((p) => p.id === projectId) || false;
    },

    hasProjectAdminAccess(projectId: number): boolean {
        if (!authState.user) return false;
        if (authState.user.role === 'admin') return true;
        const project = authState.user.projects?.find((p) => p.id === projectId);
        return project?.role === 'project_admin';
    },
};
