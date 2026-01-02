<script lang="ts">
    import { goto } from '$app/navigation';
    import { resolve } from '$app/paths';
    import * as Accordion from '$lib/components/ui/accordion/index.js';
    import Badge from '$lib/components/ui/badge/badge.svelte';
    import CardContent from '$lib/components/ui/card/card-content.svelte';
    import CardHeader from '$lib/components/ui/card/card-header.svelte';
    import CardTitle from '$lib/components/ui/card/card-title.svelte';
    import Card from '$lib/components/ui/card/card.svelte';
    import Progress from '$lib/components/ui/progress/progress.svelte';
    import * as Sheet from '$lib/components/ui/sheet/index.js';
    import { Skeleton } from '$lib/components/ui/skeleton';
    import {
        connectDashboardSSE,
        disconnectDashboardSSE,
        sseConnectionStatus,
    } from '$lib/services/sse';
    import { dashboardStore } from '$lib/stores/dashboard.svelte';
    import { projectsStore } from '$lib/stores/projects.svelte';
    import { onDestroy, onMount } from 'svelte';
    import { toast } from 'svelte-sonner';
    import type { PageData } from './$types';

    let { data }: { data: PageData } = $props();

    let showAgentSheet = $state(false);

    // Extract context data from SSR
    const context = data.context;
    const {
        user,
        activeProject: active_project,
        availableProjects: available_projects,
    } = context || {
        user: null,
        activeProject: null,
        availableProjects: [],
    };

    // Hydrate store with SSR project context data
    $effect(() => {
        if (context && user) {
            projectsStore.hydrateProjectContext(active_project, available_projects, {
                id: user.id,
                email: user.email,
                name: user.name || '',
                role: user.role,
            });
        }
    });

    // Initialize dashboard store with SSR data and set up SSE
    $effect(() => {
        if (data.dashboard && data.campaigns) {
            dashboardStore.initialize(data.dashboard, data.campaigns.items || []);

            // Connect to SSE for real-time updates
            connectDashboardSSE();
        }
    });

    // Cleanup SSE connections on component destroy
    onDestroy(() => {
        disconnectDashboardSSE();
    });

    // Reactive dashboard data from store
    const dashboardSummary = $derived(dashboardStore.summary || data.dashboard);
    const campaigns = $derived.by(() => {
        const storeCampaigns = dashboardStore.campaigns;
        if (storeCampaigns.length > 0) {
            return storeCampaigns.map((campaign) => ({
                ...campaign,
                attacks: [],
                progress: 0,
                summary: campaign.description || 'No description available',
            }));
        }
        // Fallback to SSR data
        return (data.campaigns?.items || []).map((campaign) => ({
            ...campaign,
            attacks: [],
            progress: 0,
            summary: campaign.description || 'No description available',
        }));
    });

    // Connection status indicators
    const isConnected = $derived($sseConnectionStatus.connected);
    const isStale = $derived(dashboardStore.isStale);
    const isLoading = $derived(dashboardStore.isLoading);
    const lastUpdated = $derived(dashboardStore.lastUpdated);

    function openAgentSheet() {
        showAgentSheet = true;
    }

    function navigateToCampaigns() {
        goto(resolve('/campaigns'));
    }

    function navigateToResources() {
        goto(resolve('/resources'));
    }

    function navigateToCampaignDetail(campaignId: number) {
        goto(resolve(`/campaigns/${campaignId}`));
    }

    function triggerToast(msg: string) {
        toast(msg);
    }

    // Manual refresh function
    function refreshDashboard() {
        dashboardStore.refreshData();
    }

    // Trigger demo toast after component mounts
    onMount(() => {
        setTimeout(() => triggerToast('Dashboard loaded with real-time updates!'), 2000);
    });
</script>

<svelte:head>
    <title>Dashboard - Ouroboros</title>
</svelte:head>

<div class="flex flex-col gap-y-6">
    <!-- Connection Status Indicator -->
    {#if isStale || !isConnected}
        <div
            class="rounded-md border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-800 dark:bg-yellow-900/50">
            <div class="flex items-center gap-2">
                <div class="h-2 w-2 rounded-full {isConnected ? 'bg-yellow-500' : 'bg-red-500'}">
                </div>
                <span class="text-sm text-yellow-800 dark:text-yellow-200">
                    {#if !isConnected}
                        Real-time updates disconnected
                    {:else if isStale}
                        Data may be stale (last updated: {lastUpdated?.toLocaleTimeString()})
                    {/if}
                </span>
                <button
                    type="button"
                    onclick={refreshDashboard}
                    class="ml-auto text-sm text-yellow-800 underline hover:text-yellow-900 dark:text-yellow-200 dark:hover:text-yellow-100"
                    disabled={isLoading}>
                    {isLoading ? 'Refreshing...' : 'Refresh Now'}
                </button>
            </div>
        </div>
    {/if}

    <!-- Top Metric Cards -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-4">
        <button
            type="button"
            class="h-full w-full cursor-pointer text-left"
            onclick={openAgentSheet}
            aria-label="Show Active Agents">
            <Card class="transition-all duration-200 hover:shadow-md">
                <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                        Active Agents
                        {#if isLoading}
                            <div
                                class="border-primary h-3 w-3 animate-spin rounded-full border-2 border-t-transparent">
                            </div>
                        {/if}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {#if isLoading && !dashboardSummary}
                        <!-- Skeleton loader for initial loading -->
                        <div class="flex items-center justify-between">
                            <Skeleton class="h-10 w-16" />
                            <Skeleton class="h-6 w-12" />
                        </div>
                        <Skeleton class="mt-2 h-3 w-20" />
                    {:else}
                        <div class="flex items-center justify-between">
                            <span class="text-3xl font-bold transition-all duration-300"
                                >{dashboardSummary?.active_agents ?? 0}</span>
                            <span class="text-muted-foreground"
                                >/ {dashboardSummary?.total_agents ?? 0}</span>
                        </div>
                        <div class="mt-2 text-xs">Online / Total</div>
                    {/if}
                </CardContent>
            </Card>
        </button>
        <Card
            class="cursor-pointer transition-all duration-200 hover:shadow-md"
            onclick={navigateToCampaigns}
            role="button"
            tabindex={0}>
            <CardHeader>
                <CardTitle class="flex items-center gap-2">
                    Running Tasks
                    {#if isLoading}
                        <div
                            class="border-primary h-3 w-3 animate-spin rounded-full border-2 border-t-transparent">
                        </div>
                    {/if}
                </CardTitle>
            </CardHeader>
            <CardContent>
                {#if isLoading && !dashboardSummary}
                    <!-- Skeleton loader for initial loading -->
                    <Skeleton class="h-10 w-12" />
                    <Skeleton class="mt-2 h-3 w-24" />
                {:else}
                    <div class="text-3xl font-bold transition-all duration-300">
                        {dashboardSummary?.running_tasks ?? 0}
                    </div>
                    <div class="mt-2 text-xs">Active Campaigns</div>
                {/if}
            </CardContent>
        </Card>
        <Card
            class="cursor-pointer transition-all duration-200 hover:shadow-md"
            onclick={navigateToCampaigns}
            role="button"
            tabindex={0}>
            <CardHeader>
                <CardTitle class="flex items-center gap-2">
                    Recently Cracked Hashes
                    {#if isLoading}
                        <div
                            class="border-primary h-3 w-3 animate-spin rounded-full border-2 border-t-transparent">
                        </div>
                    {/if}
                </CardTitle>
            </CardHeader>
            <CardContent>
                {#if isLoading && !dashboardSummary}
                    <!-- Skeleton loader for initial loading -->
                    <Skeleton class="h-10 w-12" />
                    <Skeleton class="mt-2 h-3 w-16" />
                {:else}
                    <div class="text-3xl font-bold transition-all duration-300">
                        {dashboardSummary?.recently_cracked_hashes ?? 0}
                    </div>
                    <div class="mt-2 text-xs">Last 24h</div>
                {/if}
            </CardContent>
        </Card>
        <Card
            class="cursor-pointer transition-all duration-200 hover:shadow-md"
            onclick={navigateToResources}
            role="button"
            tabindex={0}>
            <CardHeader>
                <CardTitle class="flex items-center gap-2">
                    Resource Usage
                    {#if isLoading}
                        <div
                            class="border-primary h-3 w-3 animate-spin rounded-full border-2 border-t-transparent">
                        </div>
                    {/if}
                </CardTitle>
            </CardHeader>
            <CardContent>
                {#if isLoading && !dashboardSummary}
                    <!-- Skeleton loader for initial loading -->
                    <div class="flex h-8 items-end gap-1">
                        {#each Array(8) as _, i (i)}
                            <Skeleton
                                class="w-2 rounded"
                                style="height: {Math.random() * 20 + 8}px" />
                        {/each}
                    </div>
                    <Skeleton class="mt-2 h-3 w-20" />
                {:else}
                    <!-- Sparkline chart for resource usage -->
                    <div class="flex h-8 items-end gap-1">
                        {#each dashboardSummary?.resource_usage ?? [] as usage, i (i)}
                            <div
                                class="bg-primary w-2 rounded transition-all duration-300"
                                style="height: {Math.max(
                                    2,
                                    Math.min(32, (usage.hash_rate || 0) / 50000)
                                )}px">
                            </div>
                        {/each}
                        {#if !dashboardSummary?.resource_usage || dashboardSummary.resource_usage.length === 0}
                            <div
                                class="text-muted-foreground flex h-8 w-full items-center justify-center text-xs">
                                No data
                            </div>
                        {/if}
                    </div>
                    <div class="mt-2 text-xs">Hashrate (8h)</div>
                {/if}
            </CardContent>
        </Card>
    </div>

    <!-- Campaign Overview List -->
    <div>
        <h2 class="mb-2 text-xl font-semibold">Campaign Overview</h2>
        {#if isLoading && campaigns.length === 0}
            <!-- Skeleton loader for campaign list -->
            <div class="space-y-2">
                {#each Array(3) as _, i (i)}
                    <div class="border-border rounded-lg border p-4">
                        <div class="flex items-center gap-4">
                            <Skeleton class="h-5 w-32" />
                            <Skeleton class="mx-4 h-2 flex-1" />
                            <Skeleton class="h-5 w-16" />
                            <Skeleton class="h-4 w-24" />
                        </div>
                    </div>
                {/each}
            </div>
        {:else if campaigns.length === 0}
            <div class="text-muted-foreground py-8 text-center">
                No active campaigns yet. Join or create one to begin.
            </div>
        {:else}
            <Accordion.Root type="multiple" class="w-full">
                {#each campaigns as campaign (campaign.id)}
                    <Accordion.Item value={String(campaign.id)} class="mb-2">
                        <Accordion.Trigger class="flex items-center gap-4">
                            <span class="font-semibold">{campaign.name}</span>
                            <Progress value={campaign.progress} class="mx-4 flex-1" />
                            <Badge
                                class="ml-2"
                                color={(campaign.state === 'active'
                                    ? 'purple'
                                    : campaign.state === 'draft'
                                      ? 'yellow'
                                      : campaign.state === 'archived'
                                        ? 'gray'
                                        : 'gray') as string}>{campaign.state}</Badge>
                            <span class="text-muted-foreground ml-2 text-xs"
                                >{campaign.summary}</span>
                        </Accordion.Trigger>
                        <Accordion.Content>
                            <div class="pl-6">
                                <!-- No attacks data in summary, placeholder only -->
                                <div class="text-muted-foreground text-xs">
                                    No attack details available.
                                </div>
                            </div>
                        </Accordion.Content>
                    </Accordion.Item>
                {/each}
            </Accordion.Root>
        {/if}
    </div>
</div>

<!-- Agent Status Sheet -->
<Sheet.Root bind:open={showAgentSheet}>
    <Sheet.Portal>
        <Sheet.Overlay />
        <Sheet.Content class="flex h-full w-[400px] flex-col">
            <Sheet.Header>
                <Sheet.Title class="flex items-center gap-2">
                    Agent Status
                    <div class="h-2 w-2 rounded-full {isConnected ? 'bg-green-500' : 'bg-red-500'}">
                    </div>
                </Sheet.Title>
            </Sheet.Header>
            <div class="flex-1 space-y-4 overflow-y-auto p-4">
                <div class="text-muted-foreground text-center">
                    {#if dashboardSummary?.total_agents === 0}
                        No agents registered yet.
                    {:else}
                        {dashboardSummary?.active_agents ?? 0} of {dashboardSummary?.total_agents ??
                            0} agents online
                    {/if}
                </div>
                {#if lastUpdated}
                    <div class="text-muted-foreground text-center text-xs">
                        Last updated: {lastUpdated.toLocaleTimeString()}
                    </div>
                {/if}
            </div>
        </Sheet.Content>
    </Sheet.Portal>
</Sheet.Root>

<!-- Toast Notification handled by svelte-sonner global Toaster -->
