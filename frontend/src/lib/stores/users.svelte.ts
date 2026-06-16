import {
    UserRead,
    UserCreate,
    UserUpdate,
    PaginatedUserList,
    UserListRequest,
} from '$lib/schemas/users';
import { browser } from '$app/environment';
import { SvelteURLSearchParams } from 'svelte/reactivity';

// Store state interfaces
interface UserState {
    users: UserRead[];
    loading: boolean;
    error: string | null;
    total: number;
    page: number;
    pageSize: number;
    searchQuery: string | null;
}

interface UserDetailState {
    details: Record<string, UserRead>;
    loading: Record<string, boolean>;
    errors: Record<string, string | null>;
}

// Create reactive state using SvelteKit 5 runes
const userState = $state<UserState>({
    users: [],
    loading: false,
    error: null,
    total: 0,
    page: 1,
    pageSize: 20,
    searchQuery: null,
});

const userDetailState = $state<UserDetailState>({
    details: {},
    loading: {},
    errors: {},
});

// Derived stores at module level
const users = $derived(userState.users);
const usersLoading = $derived(userState.loading);
const usersError = $derived(userState.error);
const usersPagination = $derived({
    total: userState.total,
    page: userState.page,
    pageSize: userState.pageSize,
    searchQuery: userState.searchQuery,
});

// Export functions that return the derived values
export function getUsers() {
    return users;
}

export function getUsersLoading() {
    return usersLoading;
}

export function getUsersError() {
    return usersError;
}

export function getUsersPagination() {
    return usersPagination;
}

// User store actions
export const usersStore = {
    // Getters for reactive state
    get users() {
        return userState.users;
    },
    get loading() {
        return userState.loading;
    },
    get error() {
        return userState.error;
    },
    get pagination() {
        return {
            total: userState.total,
            page: userState.page,
            pageSize: userState.pageSize,
            searchQuery: userState.searchQuery,
        };
    },

    // Basic user operations
    setUsers: (data: PaginatedUserList) => {
        userState.users = data.items;
        userState.total = data.total;
        userState.page = data.page;
        userState.pageSize = data.page_size;
        userState.searchQuery = data.search || null;
        userState.loading = false;
        userState.error = null;
    },

    addUser: (user: UserRead) => {
        userState.users = [...userState.users, user];
        userState.total = userState.total + 1;
    },

    updateUser: (userId: string, updatedUser: Partial<UserRead>) => {
        userState.users = userState.users.map((user) =>
            user.id === userId ? { ...user, ...updatedUser } : user
        );

        // Update detail cache if exists
        if (userDetailState.details[userId]) {
            userDetailState.details[userId] = {
                ...userDetailState.details[userId],
                ...updatedUser,
            };
        }
    },

    removeUser: (userId: string) => {
        userState.users = userState.users.filter((user) => user.id !== userId);
        userState.total = Math.max(0, userState.total - 1);

        // Clean up detail cache
        delete userDetailState.details[userId];
        delete userDetailState.loading[userId];
        delete userDetailState.errors[userId];
    },

    setLoading: (loading: boolean) => {
        userState.loading = loading;
    },

    setError: (error: string | null) => {
        userState.error = error;
        userState.loading = false;
    },

    clearError: () => {
        userState.error = null;
    },

    // API operations
    async fetchUsers(page: number = 1, pageSize: number = 20, search?: string): Promise<void> {
        if (!browser) return;

        this.setLoading(true);
        this.clearError();

        try {
            const params = new SvelteURLSearchParams({
                page: page.toString(),
                page_size: pageSize.toString(),
            });

            if (search) {
                params.append('search', search);
            }

            const response = await fetch(`/api/v1/web/users?${params}`, {
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch users: ${response.status}`);
            }

            const data = PaginatedUserList.parse(await response.json());
            this.setUsers(data);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
        }
    },

    async createUser(userData: UserCreate): Promise<UserRead | null> {
        if (!browser) return null;

        try {
            const response = await fetch('/api/v1/web/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(userData),
            });

            if (!response.ok) {
                throw new Error(`Failed to create user: ${response.status}`);
            }

            const user = UserRead.parse(await response.json());
            this.addUser(user);
            return user;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return null;
        }
    },

    async updateUserById(userId: string, updates: UserUpdate): Promise<UserRead | null> {
        if (!browser) return null;

        try {
            const response = await fetch(`/api/v1/web/users/${userId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(updates),
            });

            if (!response.ok) {
                throw new Error(`Failed to update user: ${response.status}`);
            }

            const user = UserRead.parse(await response.json());
            this.updateUser(userId, user);
            return user;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return null;
        }
    },

    async deleteUser(userId: string): Promise<boolean> {
        if (!browser) return false;

        try {
            const response = await fetch(`/api/v1/web/users/${userId}`, {
                method: 'DELETE',
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`Failed to delete user: ${response.status}`);
            }

            this.removeUser(userId);
            return true;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return false;
        }
    },

    // User detail operations
    getUserDetail: (userId: string): UserRead | null => {
        return userDetailState.details[userId] || null;
    },

    setUserDetail: (userId: string, user: UserRead) => {
        userDetailState.details[userId] = user;
        userDetailState.loading[userId] = false;
        userDetailState.errors[userId] = null;
    },

    setUserDetailLoading: (userId: string, loading: boolean) => {
        userDetailState.loading[userId] = loading;
        if (loading) {
            userDetailState.errors[userId] = null;
        }
    },

    setUserDetailError: (userId: string, error: string | null) => {
        userDetailState.errors[userId] = error;
        userDetailState.loading[userId] = false;
    },

    getUserDetailLoading: (userId: string): boolean => {
        return userDetailState.loading[userId] || false;
    },

    getUserDetailError: (userId: string): string | null => {
        return userDetailState.errors[userId] || null;
    },

    async fetchUserDetail(userId: string): Promise<UserRead | null> {
        if (!browser) return null;

        this.setUserDetailLoading(userId, true);

        try {
            const response = await fetch(`/api/v1/web/users/${userId}`, {
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch user: ${response.status}`);
            }

            const user = UserRead.parse(await response.json());
            this.setUserDetail(userId, user);
            return user;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setUserDetailError(userId, errorMessage);
            return null;
        }
    },

    // SSR hydration methods
    hydrate(data: PaginatedUserList) {
        this.setUsers(data);
    },

    // Method alias for components that expect it
    hydrateUsers(data: PaginatedUserList) {
        this.hydrate(data);
    },

    hydrateUserDetail(userId: string, user: UserRead) {
        this.setUserDetail(userId, user);
    },

    // Clear all state
    clear() {
        userState.users = [];
        userState.loading = false;
        userState.error = null;
        userState.total = 0;
        userState.page = 1;
        userState.pageSize = 20;
        userState.searchQuery = null;
        userDetailState.details = {};
        userDetailState.loading = {};
        userDetailState.errors = {};
    },
};
