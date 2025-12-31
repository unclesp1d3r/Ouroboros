import {
    CampaignRead,
    CampaignCreate,
    CampaignUpdate,
    CampaignListResponse,
    CampaignMetrics,
    CampaignProgress,
    CampaignDetailResponse,
    CampaignWithAttacks,
    CampaignTemplate_Input,
    CampaignTemplate_Output,
} from '$lib/schemas/campaigns';
import { browser } from '$app/environment';
import { SvelteURLSearchParams } from 'svelte/reactivity';

// Store state interfaces
interface CampaignState {
    campaigns: CampaignRead[];
    loading: boolean;
    error: string | null;
    totalPages: number;
    currentPage: number;
    pageSize: number;
    total: number;
}

interface CampaignDataState {
    metrics: Record<number, CampaignMetrics>;
    progress: Record<number, CampaignProgress>;
    loading: Record<number, boolean>;
    errors: Record<number, string | null>;
}

// Create reactive state using SvelteKit 5 runes
const campaignState = $state<CampaignState>({
    campaigns: [],
    loading: false,
    error: null,
    totalPages: 0,
    currentPage: 1,
    pageSize: 20,
    total: 0,
});

const campaignDataState = $state<CampaignDataState>({
    metrics: {},
    progress: {},
    loading: {},
    errors: {},
});

// Derived stores at module level
const campaigns = $derived(campaignState.campaigns);
const campaignsLoading = $derived(campaignState.loading);
const campaignsError = $derived(campaignState.error);
const totalPages = $derived(campaignState.totalPages);
const currentPage = $derived(campaignState.currentPage);
const pageSize = $derived(campaignState.pageSize);
const total = $derived(campaignState.total);

// Export functions that return the derived values
export function getCampaigns() {
    return campaigns;
}

export function getCampaignsLoading() {
    return campaignsLoading;
}

export function getCampaignsError() {
    return campaignsError;
}

export function getTotalPages() {
    return totalPages;
}

export function getCurrentPage() {
    return currentPage;
}

export function getPageSize() {
    return pageSize;
}

export function getTotal() {
    return total;
}

// Campaign store actions
export const campaignsStore = {
    // Getters for reactive state
    get campaigns() {
        return campaignState.campaigns;
    },
    get loading() {
        return campaignState.loading;
    },
    get error() {
        return campaignState.error;
    },
    get totalPages() {
        return campaignState.totalPages;
    },
    get currentPage() {
        return campaignState.currentPage;
    },
    get pageSize() {
        return campaignState.pageSize;
    },
    get total() {
        return campaignState.total;
    },

    // Basic campaign operations
    setCampaigns: (data: CampaignListResponse) => {
        campaignState.campaigns = data.items;
        campaignState.total = data.total;
        campaignState.currentPage = data.page;
        campaignState.pageSize = data.size;
        campaignState.totalPages = data.total_pages;
        campaignState.loading = false;
        campaignState.error = null;
    },

    addCampaign: (campaign: CampaignRead) => {
        campaignState.campaigns = [...campaignState.campaigns, campaign];
        campaignState.total += 1;
    },

    updateCampaign: (id: number, updates: Partial<CampaignRead>) => {
        campaignState.campaigns = campaignState.campaigns.map((c) =>
            c.id === id ? { ...c, ...updates } : c
        );
    },

    removeCampaign: (id: number) => {
        campaignState.campaigns = campaignState.campaigns.filter((c) => c.id !== id);
        campaignState.total = Math.max(0, campaignState.total - 1);
        // Clean up associated data
        delete campaignDataState.metrics[id];
        delete campaignDataState.progress[id];
        delete campaignDataState.loading[id];
        delete campaignDataState.errors[id];
    },

    setLoading: (loading: boolean) => {
        campaignState.loading = loading;
    },

    setError: (error: string | null) => {
        campaignState.error = error;
        campaignState.loading = false;
    },

    // Campaign data operations
    setCampaignMetrics: (campaignId: number, metrics: CampaignMetrics) => {
        campaignDataState.metrics[campaignId] = metrics;
        campaignDataState.loading[campaignId] = false;
        campaignDataState.errors[campaignId] = null;
    },

    setCampaignProgress: (campaignId: number, progress: CampaignProgress) => {
        campaignDataState.progress[campaignId] = progress;
        campaignDataState.loading[campaignId] = false;
        campaignDataState.errors[campaignId] = null;
    },

    setCampaignData: (campaignId: number, metrics: CampaignMetrics, progress: CampaignProgress) => {
        campaignDataState.metrics[campaignId] = metrics;
        campaignDataState.progress[campaignId] = progress;
        campaignDataState.loading[campaignId] = false;
        campaignDataState.errors[campaignId] = null;
    },

    setCampaignLoading: (campaignId: number, loading: boolean) => {
        campaignDataState.loading[campaignId] = loading;
    },

    setCampaignError: (campaignId: number, error: string | null) => {
        campaignDataState.errors[campaignId] = error;
        campaignDataState.loading[campaignId] = false;
    },

    // Getters
    getCampaignMetrics: (campaignId: number): CampaignMetrics | null => {
        return campaignDataState.metrics[campaignId] || null;
    },

    getCampaignProgress: (campaignId: number): CampaignProgress | null => {
        return campaignDataState.progress[campaignId] || null;
    },

    isCampaignLoading: (campaignId: number): boolean => {
        return campaignDataState.loading[campaignId] || false;
    },

    getCampaignError: (campaignId: number): string | null => {
        return campaignDataState.errors[campaignId] || null;
    },

    // API operations
    async fetchCampaigns(page: number = 1, size: number = 20, name?: string): Promise<void> {
        if (!browser) return;

        this.setLoading(true);
        this.setError(null);

        try {
            const params = new SvelteURLSearchParams({
                page: page.toString(),
                size: size.toString(),
            });

            if (name) {
                params.append('name', name);
            }

            const response = await fetch(`/api/v1/web/campaigns?${params}`, {
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch campaigns: ${response.status}`);
            }

            const data = CampaignListResponse.parse(await response.json());
            this.setCampaigns(data);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
        }
    },

    async createCampaign(campaignData: CampaignCreate): Promise<CampaignRead | null> {
        if (!browser) return null;

        try {
            const response = await fetch('/api/v1/web/campaigns', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(campaignData),
            });

            if (!response.ok) {
                throw new Error(`Failed to create campaign: ${response.status}`);
            }

            const campaign = CampaignRead.parse(await response.json());
            this.addCampaign(campaign);
            return campaign;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return null;
        }
    },

    async updateCampaignById(id: number, updates: CampaignUpdate): Promise<CampaignRead | null> {
        if (!browser) return null;

        try {
            const response = await fetch(`/api/v1/web/campaigns/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(updates),
            });

            if (!response.ok) {
                throw new Error(`Failed to update campaign: ${response.status}`);
            }

            const campaign = CampaignRead.parse(await response.json());
            this.updateCampaign(id, campaign);
            return campaign;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return null;
        }
    },

    async deleteCampaign(id: number): Promise<boolean> {
        if (!browser) return false;

        try {
            const response = await fetch(`/api/v1/web/campaigns/${id}`, {
                method: 'DELETE',
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`Failed to delete campaign: ${response.status}`);
            }

            this.removeCampaign(id);
            return true;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return false;
        }
    },

    async getCampaignDetail(id: number): Promise<CampaignDetailResponse | null> {
        if (!browser) return null;

        try {
            const response = await fetch(`/api/v1/web/campaigns/${id}`, {
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch campaign: ${response.status}`);
            }

            return CampaignDetailResponse.parse(await response.json());
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return null;
        }
    },

    async startCampaign(id: number): Promise<boolean> {
        if (!browser) return false;

        try {
            const response = await fetch(`/api/v1/web/campaigns/${id}/start`, {
                method: 'POST',
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`Failed to start campaign: ${response.status}`);
            }

            // Update campaign state locally
            this.updateCampaign(id, { state: 'active' });
            return true;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return false;
        }
    },

    async stopCampaign(id: number): Promise<boolean> {
        if (!browser) return false;

        try {
            const response = await fetch(`/api/v1/web/campaigns/${id}/stop`, {
                method: 'POST',
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`Failed to stop campaign: ${response.status}`);
            }

            // Update campaign state locally - stopping returns to draft state
            this.updateCampaign(id, { state: 'draft' });
            return true;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return false;
        }
    },

    async relaunchCampaign(id: number): Promise<CampaignDetailResponse | null> {
        if (!browser) return null;

        try {
            const response = await fetch(`/api/v1/web/campaigns/${id}/relaunch`, {
                method: 'POST',
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`Failed to relaunch campaign: ${response.status}`);
            }

            return CampaignDetailResponse.parse(await response.json());
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return null;
        }
    },

    async exportCampaign(id: number): Promise<CampaignTemplate_Output | null> {
        if (!browser) return null;

        try {
            const response = await fetch(`/api/v1/web/campaigns/${id}/export`, {
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`Failed to export campaign: ${response.status}`);
            }

            return CampaignTemplate_Output.parse(await response.json());
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return null;
        }
    },

    async importCampaign(template: CampaignTemplate_Input): Promise<CampaignWithAttacks | null> {
        if (!browser) return null;

        try {
            const response = await fetch('/api/v1/web/campaigns/import_json', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(template),
            });

            if (!response.ok) {
                throw new Error(`Failed to import campaign: ${response.status}`);
            }

            return CampaignWithAttacks.parse(await response.json());
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setError(errorMessage);
            return null;
        }
    },

    async updateCampaignData(campaignId: number): Promise<void> {
        if (!browser) return;

        this.setCampaignLoading(campaignId, true);

        try {
            // Fetch both metrics and progress in parallel
            const [metricsResponse, progressResponse] = await Promise.all([
                fetch(`/api/v1/web/campaigns/${campaignId}/metrics`, {
                    credentials: 'include',
                }),
                fetch(`/api/v1/web/campaigns/${campaignId}/progress`, {
                    credentials: 'include',
                }),
            ]);

            if (!metricsResponse.ok || !progressResponse.ok) {
                throw new Error('Failed to fetch campaign data');
            }

            const [metricsData, progressData] = await Promise.all([
                metricsResponse.json(),
                progressResponse.json(),
            ]);

            const metrics = CampaignMetrics.parse(metricsData);
            const progress = CampaignProgress.parse(progressData);

            this.setCampaignData(campaignId, metrics, progress);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.setCampaignError(campaignId, errorMessage);
        }
    },

    // Hydration from SSR data
    hydrate(data: CampaignListResponse) {
        this.setCampaigns(data);
    },

    hydrateCampaignData(
        campaignId: number,
        metrics?: CampaignMetrics,
        progress?: CampaignProgress
    ) {
        if (metrics && progress) {
            this.setCampaignData(campaignId, metrics, progress);
        } else if (metrics) {
            this.setCampaignMetrics(campaignId, metrics);
        } else if (progress) {
            this.setCampaignProgress(campaignId, progress);
        }
    },
};
