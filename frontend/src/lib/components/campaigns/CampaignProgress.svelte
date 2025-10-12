<script lang="ts">
    import { onDestroy } from 'svelte';
    import { Card, CardHeader, CardTitle, CardContent } from '$lib/components/ui/card';
    import { Badge } from '$lib/components/ui/badge';
    import { Progress } from '$lib/components/ui/progress';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { campaignsStore } from '$lib/stores/campaigns.svelte';
    import type { CampaignProgress } from '$lib/types/campaign';

    export let campaignId: number = undefined as unknown as number;
    export let initialProgress: CampaignProgress | null = null;
    export let refreshInterval: number = 5000; // 5 seconds default
    export let enableAutoRefresh: boolean = false; // Allow disabling auto-refresh

    // State management using derived values from store
    let intervalId: NodeJS.Timeout | null = null;

    // Initialize store with SSR data if provided
    $: if (initialProgress && campaignId) {
        campaignsStore.setCampaignProgress(campaignId, initialProgress);
    }

    // Reactive values from store
    $: progress = campaignsStore.getCampaignProgress(campaignId) || initialProgress;
    $: loading = campaignsStore.isCampaignLoading(campaignId);
    $: error = campaignsStore.getCampaignError(campaignId);

    function startPolling() {
        if (!enableAutoRefresh) return;

        if (intervalId) {
            clearInterval(intervalId);
        }
        intervalId = setInterval(() => {
            campaignsStore.updateCampaignData(campaignId);
        }, refreshInterval);
    }

    function stopPolling() {
        if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
        }
    }

    // Start polling when auto-refresh is enabled
    $: if (enableAutoRefresh) {
        startPolling();
    } else {
        stopPolling();
    }

    onDestroy(() => {
        stopPolling();
    });

    function getStatusBadge(status: string | null | undefined) {
        switch (status) {
            case 'running':
                return { color: 'bg-green-600', label: 'Running' };
            case 'completed':
                return { color: 'bg-blue-600', label: 'Completed' };
            case 'failed':
                return { color: 'bg-red-600', label: 'Failed' };
            case 'pending':
                return { color: 'bg-yellow-500', label: 'Pending' };
            case 'paused':
                return { color: 'bg-yellow-600', label: 'Paused' };
            case 'abandoned':
                return { color: 'bg-gray-600', label: 'Abandoned' };
            default:
                return { color: 'bg-gray-400', label: status || 'Unknown' };
        }
    }
</script>

<Card data-testid="campaign-progress-card">
    <CardHeader>
        <CardTitle>Campaign Progress</CardTitle>
    </CardHeader>
    <CardContent>
        {#if loading}
            <div class="py-4 text-center text-gray-500" data-testid="progress-loading">
                Loading...
            </div>
        {:else if error}
            <Alert variant="destructive">
                <AlertDescription data-testid="progress-error">{error}</AlertDescription>
            </Alert>
        {:else if progress}
            <div class="space-y-4">
                <!-- Progress Bar -->
                <div class="space-y-2">
                    <div class="flex items-center justify-between">
                        <span class="text-sm font-medium">Progress</span>
                        <span class="text-sm text-gray-600" data-testid="progress-percentage">
                            {progress.percentage_complete.toFixed(1)}%
                        </span>
                    </div>
                    <Progress
                        value={progress.percentage_complete}
                        class="h-2"
                        data-testid="campaign-progress-bar" />
                </div>

                <!-- Status and Agents -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="text-sm font-medium">Status:</span>
                        <Badge
                            class={getStatusBadge(progress.overall_status).color}
                            data-testid="progress-status">
                            {getStatusBadge(progress.overall_status).label}
                        </Badge>
                    </div>
                    <div class="text-sm text-gray-600" data-testid="active-agents">
                        <span class="font-medium">Active Agents:</span>
                        {progress.active_agents}
                    </div>
                </div>

                <!-- Task Breakdown -->
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div class="space-y-1">
                        <div class="flex justify-between" data-testid="total-tasks">
                            <span class="text-gray-600">Total Tasks:</span>
                            <span class="font-medium">{progress.total_tasks}</span>
                        </div>
                        <div class="flex justify-between" data-testid="completed-tasks">
                            <span class="text-gray-600">Completed:</span>
                            <span class="font-medium text-green-600"
                                >{progress.completed_tasks}</span>
                        </div>
                        <div class="flex justify-between" data-testid="active-tasks">
                            <span class="text-gray-600">Active:</span>
                            <span class="font-medium text-blue-600">{progress.active_tasks}</span>
                        </div>
                    </div>
                    <div class="space-y-1">
                        <div class="flex justify-between" data-testid="pending-tasks">
                            <span class="text-gray-600">Pending:</span>
                            <span class="font-medium text-yellow-600"
                                >{progress.pending_tasks}</span>
                        </div>
                        <div class="flex justify-between" data-testid="failed-tasks">
                            <span class="text-gray-600">Failed:</span>
                            <span class="font-medium text-red-600">{progress.failed_tasks}</span>
                        </div>
                        {#if progress.active_attack_id}
                            <div class="flex justify-between" data-testid="active-attack">
                                <span class="text-gray-600">Active Attack:</span>
                                <span class="font-medium">#{progress.active_attack_id}</span>
                            </div>
                        {/if}
                    </div>
                </div>
            </div>
        {:else}
            <div class="py-4 text-center text-gray-500" data-testid="no-progress-data">
                Loading...
            </div>
        {/if}
    </CardContent>
</Card>
