import {
    ProjectRead,
    ProjectCreate,
    ProjectUpdate,
    ProjectListResponse,
} from '$lib/schemas/projects';
import { browser } from '$app/environment';
import { SvelteURLSearchParams } from 'svelte/reactivity';

// Store state interfaces
interface ProjectState {
    projects: ProjectRead[];
    loading: boolean;
    error: string | null;
    total: number;
    limit: number;
    offset: number;
    searchQuery: string | null;
}

interface ProjectDetailState {
    details: Record<string, ProjectRead>;
    loading: Record<string, boolean>;
    errors: Record<string, string | null>;
}

interface ProjectContextState {
    activeProject: { id: number; name: string } | null;
    availableProjects: { id: number; name: string }[];
    user: {
        id: string;
        email: string;
        name: string;
        role: string;
    } | null;
    loading: boolean;
    error: string | null;
}

// Create reactive state using SvelteKit 5 runes
const projectState = $state<ProjectState>({
    projects: [],
    loading: false,
    error: null,
    total: 0,
    limit: 20,
    offset: 0,
    searchQuery: null,
});

const projectDetailState = $state<ProjectDetailState>({
    details: {},
    loading: {},
    errors: {},
});

const projectContextState = $state<ProjectContextState>({
    activeProject: null,
    availableProjects: [],
    user: null,
    loading: false,
    error: null,
});

// Derived stores at module level
const projects = $derived(projectState.projects);
const projectsLoading = $derived(projectState.loading);
const projectsError = $derived(projectState.error);
const projectsPagination = $derived({
    total: projectState.total,
    limit: projectState.limit,
    offset: projectState.offset,
    searchQuery: projectState.searchQuery,
});

const activeProject = $derived(projectContextState.activeProject);
const availableProjects = $derived(projectContextState.availableProjects);
const contextUser = $derived(projectContextState.user);
const contextLoading = $derived(projectContextState.loading);
const contextError = $derived(projectContextState.error);

// Export functions that return the derived values
export function getProjects() {
    return projects;
}

export function getProjectsLoading() {
    return projectsLoading;
}

export function getProjectsError() {
    return projectsError;
}

export function getProjectsPagination() {
    return projectsPagination;
}

export function getActiveProject() {
    return activeProject;
}

export function getAvailableProjects() {
    return availableProjects;
}

export function getContextUser() {
    return contextUser;
}

export function getContextLoading() {
    return contextLoading;
}

export function getContextError() {
    return contextError;
}

// Project store actions
export const projectsStore = {
    // Getters for reactive state
    get projects() {
        return projectState.projects;
    },
    get loading() {
        return projectState.loading;
    },
    get error() {
        return projectState.error;
    },
    get pagination() {
        return {
            total: projectState.total,
            limit: projectState.limit,
            offset: projectState.offset,
            searchQuery: projectState.searchQuery,
        };
    },
    get activeProject() {
        return projectContextState.activeProject;
    },
    get availableProjects() {
        return projectContextState.availableProjects;
    },
    get contextUser() {
        return projectContextState.user;
    },
    get contextLoading() {
        return projectContextState.loading;
    },
    get contextError() {
        return projectContextState.error;
    },

    // Basic project operations
    setProjects: (data: ProjectListResponse) => {
        projectState.projects = data.items;
        projectState.total = data.total;
        projectState.limit = data.limit;
        projectState.offset = data.offset;
        projectState.searchQuery = data.search || null;
        projectState.loading = false;
        projectState.error = null;
    },

    addProject: (project: ProjectRead) => {
        projectState.projects = [...projectState.projects, project];
        projectState.total = projectState.total + 1;
    },

    updateProject: (projectId: number, updatedProject: Partial<ProjectRead>) => {
        projectState.projects = projectState.projects.map((project) =>
            project.id === projectId ? { ...project, ...updatedProject } : project
        );

        // Update detail cache if exists
        if (projectDetailState.details[projectId.toString()]) {
            projectDetailState.details[projectId.toString()] = {
                ...projectDetailState.details[projectId.toString()],
                ...updatedProject,
            };
        }
    },

    removeProject: (projectId: number) => {
        projectState.projects = projectState.projects.filter((project) => project.id !== projectId);
        projectState.total = Math.max(0, projectState.total - 1);

        // Clean up detail cache
        const projectIdStr = projectId.toString();
        delete projectDetailState.details[projectIdStr];
        delete projectDetailState.loading[projectIdStr];
        delete projectDetailState.errors[projectIdStr];
    },

    setLoading: (loading: boolean) => {
        projectState.loading = loading;
    },

    setError: (error: string | null) => {
        projectState.error = error;
        projectState.loading = false;
    },

    clearError: () => {
        projectState.error = null;
    },

    // API operations
    async fetchProjects(limit: number = 20, offset: number = 0, search?: string): Promise<void> {
        if (!browser) return;

        this.setLoading(true);
        this.clearError();

        try {
            const params = new SvelteURLSearchParams({
                limit: limit.toString(),
                offset: offset.toString(),
            });

            if (search) {
                params.append('search', search);
            }

            const response = await fetch(`/api/v1/web/projects?${params}`, {
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch projects: ${response.status}`);
            }

            const data = ProjectListResponse.parse(await response.json());
            this.setProjects(data);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
        }
    },

    async createProject(projectData: ProjectCreate): Promise<ProjectRead | null> {
        if (!browser) return null;

        try {
            const response = await fetch('/api/v1/web/projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(projectData),
            });

            if (!response.ok) {
                throw new Error(`Failed to create project: ${response.status}`);
            }

            const project = ProjectRead.parse(await response.json());
            this.addProject(project);
            return project;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return null;
        }
    },

    async updateProjectById(
        projectId: number,
        updates: ProjectUpdate
    ): Promise<ProjectRead | null> {
        if (!browser) return null;

        try {
            const response = await fetch(`/api/v1/web/projects/${projectId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(updates),
            });

            if (!response.ok) {
                throw new Error(`Failed to update project: ${response.status}`);
            }

            const project = ProjectRead.parse(await response.json());
            this.updateProject(projectId, project);
            return project;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return null;
        }
    },

    async deleteProject(projectId: number): Promise<boolean> {
        if (!browser) return false;

        try {
            const response = await fetch(`/api/v1/web/projects/${projectId}`, {
                method: 'DELETE',
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`Failed to delete project: ${response.status}`);
            }

            this.removeProject(projectId);
            return true;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return false;
        }
    },

    // Project detail operations
    getProjectDetail: (projectId: string): ProjectRead | null => {
        return projectDetailState.details[projectId] || null;
    },

    setProjectDetail: (projectId: string, project: ProjectRead) => {
        projectDetailState.details[projectId] = project;
        projectDetailState.loading[projectId] = false;
        projectDetailState.errors[projectId] = null;
    },

    setProjectDetailLoading: (projectId: string, loading: boolean) => {
        projectDetailState.loading[projectId] = loading;
        if (loading) {
            projectDetailState.errors[projectId] = null;
        }
    },

    setProjectDetailError: (projectId: string, error: string | null) => {
        projectDetailState.errors[projectId] = error;
        projectDetailState.loading[projectId] = false;
    },

    getProjectDetailLoading: (projectId: string): boolean => {
        return projectDetailState.loading[projectId] || false;
    },

    getProjectDetailError: (projectId: string): string | null => {
        return projectDetailState.errors[projectId] || null;
    },

    async fetchProjectDetail(projectId: number): Promise<ProjectRead | null> {
        if (!browser) return null;

        const projectIdStr = projectId.toString();
        this.setProjectDetailLoading(projectIdStr, true);

        try {
            const response = await fetch(`/api/v1/web/projects/${projectId}`, {
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch project: ${response.status}`);
            }

            const project = ProjectRead.parse(await response.json());
            this.setProjectDetail(projectIdStr, project);
            return project;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setProjectDetailError(projectIdStr, errorMessage);
            return null;
        }
    },

    // Project context operations
    setProjectContext: (
        activeProject: { id: number; name: string } | null,
        availableProjects: { id: number; name: string }[],
        user: {
            id: string;
            email: string;
            name: string;
            role: string;
        } | null
    ) => {
        projectContextState.activeProject = activeProject;
        projectContextState.availableProjects = availableProjects;
        projectContextState.user = user;
        projectContextState.loading = false;
        projectContextState.error = null;
    },

    setContextLoading: (loading: boolean) => {
        projectContextState.loading = loading;
    },

    setContextError: (error: string | null) => {
        projectContextState.error = error;
        projectContextState.loading = false;
    },

    setActiveProject: (project: { id: number; name: string } | null) => {
        projectContextState.activeProject = project;
    },

    // SSR hydration methods
    hydrate(data: ProjectListResponse) {
        this.setProjects(data);
    },

    // Method alias for components that expect it
    hydrateProjects(data: ProjectListResponse) {
        this.hydrate(data);
    },

    hydrateProjectDetail(projectId: string, project: ProjectRead) {
        this.setProjectDetail(projectId, project);
    },

    hydrateProjectContext(
        activeProject: { id: number; name: string } | null,
        availableProjects: { id: number; name: string }[],
        user: {
            id: string;
            email: string;
            name: string;
            role: string;
        } | null
    ) {
        this.setProjectContext(activeProject, availableProjects, user);
    },

    // Clear all state
    clear() {
        projectState.projects = [];
        projectState.loading = false;
        projectState.error = null;
        projectState.total = 0;
        projectState.limit = 20;
        projectState.offset = 0;
        projectState.searchQuery = null;
        projectDetailState.details = {};
        projectDetailState.loading = {};
        projectDetailState.errors = {};
        projectContextState.activeProject = null;
        projectContextState.availableProjects = [];
        projectContextState.user = null;
        projectContextState.loading = false;
        projectContextState.error = null;
    },
};
