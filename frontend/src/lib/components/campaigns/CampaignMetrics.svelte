<script lang="ts">
    import { onDestroy } from 'svelte';
    import { Card, CardHeader, CardTitle, CardContent } from '$lib/components/ui/card';
    import { Progress } from '$lib/components/ui/progress';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { campaignsStore } from '$lib/stores/campaigns.svelte';
    import type { CampaignMetrics } from '$lib/types/campaign';

    export let campaignId: number = undefined as unknown as number;
    export let initialMetrics: CampaignMetrics | null = null;
    export let refreshInterval: number = 5000; // 5 seconds default
    export let enableAutoRefresh: boolean = false; // Allow disabling auto-refresh

    // State management using derived values from store
    let intervalId: NodeJS.Timeout | null = null;

    // Initialize store with SSR data if provided
    $: if (initialMetrics && campaignId) {
        campaignsStore.setCampaignMetrics(campaignId, initialMetrics);
    }

    // Reactive values from store
    $: metrics = campaignsStore.getCampaignMetrics(campaignId) || initialMetrics;
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

    function formatNumber(num: number): string {
        return num.toLocaleString();
    }
</script>

<Card data-testid="campaign-metrics-card">
    <CardHeader>
        <CardTitle>Campaign Metrics</CardTitle>
    </CardHeader>
    <CardContent>
        {#if loading}
            <div class="py-4 text-center text-gray-500" data-testid="metrics-loading">
                Loading...
            </div>
        {:else if error}
            <Alert variant="destructive">
                <AlertDescription data-testid="metrics-error">{error}</AlertDescription>
            </Alert>
        {:else if metrics}
            <div class="space-y-4">
                <!-- Hash Statistics -->
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div class="space-y-2">
                        <div class="flex justify-between" data-testid="total-hashes">
                            <span class="text-gray-600">Total Hashes:</span>
                            <span class="font-medium">{formatNumber(metrics.total_hashes)}</span>
                        </div>
                        <div class="flex justify-between" data-testid="cracked-hashes">
                            <span class="text-gray-600">Cracked:</span>
                            <span class="font-medium text-green-600"
                                >{formatNumber(metrics.cracked_hashes)}</span>
                        </div>
                        <div class="flex justify-between" data-testid="uncracked-hashes">
                            <span class="text-gray-600">Remaining:</span>
                            <span class="font-medium text-red-600"
                                >{formatNumber(metrics.uncracked_hashes)}</span>
                        </div>
                    </div>
                    <div class="space-y-2">
                        <div class="flex justify-between" data-testid="percent-cracked">
                            <span class="text-gray-600">Progress:</span>
                            <span class="font-medium text-blue-600"
                                >{metrics.percent_cracked.toFixed(1)}%</span>
                        </div>
                    </div>
                </div>

                <!-- Cracking Progress Bar -->
                <div class="space-y-2">
                    <div class="flex items-center justify-between">
                        <span class="text-sm font-medium">Cracking Progress</span>
                        <span class="text-sm text-gray-600" data-testid="cracking-percentage">
                            {metrics.percent_cracked.toFixed(1)}%
                        </span>
                    </div>
                    <Progress
                        value={metrics.percent_cracked}
                        class="h-2"
                        data-testid="campaign-cracking-progress-bar" />
                </div>

                <!-- Overall Progress Bar -->
                <div class="space-y-2">
                    <div class="flex items-center justify-between">
                        <span class="text-sm font-medium">Overall Progress</span>
                        <span class="text-sm text-gray-600" data-testid="overall-percentage">
                            {metrics.progress_percent.toFixed(1)}%
                        </span>
                    </div>
                    <Progress
                        value={metrics.progress_percent}
                        class="h-2"
                        data-testid="campaign-overall-progress-bar" />
                </div>

                <!-- Summary -->
                {#if metrics.total_hashes > 0}
                    <div class="pt-2 text-xs text-gray-500" data-testid="metrics-summary">
                        {formatNumber(metrics.cracked_hashes)} of {formatNumber(
                            metrics.total_hashes
                        )} hashes cracked ({metrics.percent_cracked.toFixed(1)}%)
                    </div>
                {/if}
            </div>
        {:else}
            <div class="py-4 text-center text-gray-500" data-testid="no-metrics-data">
                Loading...
            </div>
        {/if}
    </CardContent>
</Card>
