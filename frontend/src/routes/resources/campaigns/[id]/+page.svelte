<script lang="ts">
    import { page } from '$app/stores';
    import { Card, CardHeader, CardTitle, CardContent } from '$lib/components/ui/card';
    import { Button } from '$lib/components/ui/button';
    import { Badge } from '$lib/components/ui/badge';
    import { Progress } from '$lib/components/ui/progress';
    import {
        DropdownMenu,
        DropdownMenuTrigger,
        DropdownMenuContent,
        DropdownMenuItem,
    } from '$lib/components/ui/dropdown-menu';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { goto } from '$app/navigation';
    import CampaignProgress from '$lib/components/campaigns/CampaignProgress.svelte';
    import CampaignMetrics from '$lib/components/campaigns/CampaignMetrics.svelte';
    import AttackTableBody from '$lib/components/attacks/AttackTableBody.svelte';
    import type { PageData } from './$types';

    // Receive SSR data
    export let data: PageData = undefined as unknown as PageData;

    // Extract data from SSR
    $: campaign = data.campaign;
    $: progress = data.progress;
    $: metrics = data.metrics;
    $: campaignId = $page.params.id;

    // State for client-side interactions
    let error = '';

    function getStateBadge(state: string) {
        switch (state) {
            case 'running':
            case 'active':
                return { color: 'bg-green-600', label: 'Running' };
            case 'completed':
                return { color: 'bg-blue-600', label: 'Completed' };
            case 'error':
                return { color: 'bg-red-600', label: 'Error' };
            case 'paused':
                return { color: 'bg-yellow-500', label: 'Paused' };
            case 'draft':
                return { color: 'bg-gray-400', label: 'Draft' };
            default:
                return { color: 'bg-gray-200', label: state };
        }
    }

    function getAttackTypeBadge(type: string) {
        switch (type) {
            case 'dictionary':
                return { color: 'bg-blue-500', label: 'Dictionary' };
            case 'mask':
                return { color: 'bg-purple-500', label: 'Mask' };
            case 'brute_force':
                return { color: 'bg-orange-500', label: 'Brute Force' };
            case 'hybrid_dictionary':
                return { color: 'bg-teal-500', label: 'Hybrid Dictionary' };
            case 'hybrid_mask':
                return { color: 'bg-pink-500', label: 'Hybrid Mask' };
            default:
                return { color: 'bg-gray-400', label: type };
        }
    }

    function formatLength(length: number | null): string {
        if (length === null) return '—';
        return String(length);
    }

    function formatKeyspace(keyspace: number | null): string {
        if (keyspace === null) return '—';
        return keyspace.toLocaleString();
    }

    function transformAttacksForTable(attacks: typeof campaign.attacks) {
        return attacks.map((attack) => ({
            id: attack.id.toString(),
            name: attack.name,
            type_label: attack.type_label || '—',
            length_range: formatLength(attack.length),
            settings_summary: attack.settings_summary,
            keyspace: attack.keyspace ?? undefined,
            complexity_score: attack.complexity_score ?? undefined,
            comment: attack.comment || '',
            type: attack.attack_mode,
            type_badge: getAttackTypeBadge(attack.attack_mode),
            state: attack.state,
        }));
    }

    async function handleMoveAttackCallback(
        attackId: string,
        direction: 'up' | 'down' | 'top' | 'bottom'
    ) {
        try {
            const response = await fetch(`/api/v1/web/attacks/${attackId}/move`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ direction }),
            });

            if (!response.ok) {
                throw new Error('Failed to move attack');
            }

            // Refresh the page to get updated data
            goto($page.url.pathname, { replaceState: true });
        } catch (e) {
            error = 'Failed to move attack.';
        }
    }

    function renderComplexityDots(score: number | null): string {
        if (score === null) return '—';
        return '●'.repeat(score) + '○'.repeat(5 - score);
    }

    async function handleEditAttack(attackId: number) {
        // TODO: Implement attack edit modal
        console.log('Edit attack:', attackId);
    }

    async function handleDuplicateAttack(attackId: number) {
        try {
            const response = await fetch(`/api/v1/web/attacks/${attackId}/duplicate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to duplicate attack');
            }

            // Refresh the page to get updated data
            goto($page.url.pathname, { replaceState: true });
        } catch (e) {
            error = 'Failed to duplicate attack.';
        }
    }

    async function handleMoveAttack(attackId: number, direction: 'up' | 'down') {
        try {
            const response = await fetch(`/api/v1/web/attacks/${attackId}/move`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ direction }),
            });

            if (!response.ok) {
                throw new Error('Failed to move attack');
            }

            // Refresh the page to get updated data
            goto($page.url.pathname, { replaceState: true });
        } catch (e) {
            error = 'Failed to move attack.';
        }
    }

    async function handleRemoveAttack(attackId: number) {
        if (confirm('Are you sure you want to remove this attack?')) {
            try {
                const response = await fetch(`/api/v1/web/attacks/${attackId}`, {
                    method: 'DELETE',
                });

                if (!response.ok) {
                    throw new Error('Failed to remove attack');
                }

                // Refresh the page to get updated data
                goto($page.url.pathname, { replaceState: true });
            } catch (e) {
                error = 'Failed to remove attack.';
            }
        }
    }

    async function handleAddAttack() {
        // TODO: Implement add attack modal
        console.log('Add attack to campaign:', campaignId);
    }

    async function handleRemoveAllAttacks() {
        if (confirm('Remove all attacks from this campaign?')) {
            try {
                const response = await fetch(`/api/v1/web/campaigns/${campaignId}/clear_attacks`, {
                    method: 'POST',
                });

                if (!response.ok) {
                    throw new Error('Failed to remove all attacks');
                }

                // Refresh the page to get updated data
                goto($page.url.pathname, { replaceState: true });
            } catch (e) {
                error = 'Failed to remove all attacks.';
            }
        }
    }

    async function handleStartCampaign() {
        try {
            const response = await fetch(`/api/v1/web/campaigns/${campaignId}/start`, {
                method: 'POST',
            });

            if (!response.ok) {
                throw new Error('Failed to start campaign');
            }

            // Refresh the page to get updated data
            goto($page.url.pathname, { replaceState: true });
        } catch (e) {
            error = 'Failed to start campaign.';
        }
    }

    async function handleStopCampaign() {
        try {
            const response = await fetch(`/api/v1/web/campaigns/${campaignId}/stop`, {
                method: 'POST',
            });

            if (!response.ok) {
                throw new Error('Failed to stop campaign');
            }

            // Refresh the page to get updated data
            goto($page.url.pathname, { replaceState: true });
        } catch (e) {
            error = 'Failed to stop campaign.';
        }
    }
</script>

<svelte:head>
    <title>{campaign?.name || 'Campaign'} - Ouroboros</title>
</svelte:head>

<div class="container mx-auto max-w-7xl p-6">
    {#if error}
        <Alert class="mb-4" variant="destructive">
            <AlertDescription data-testid="error">{error}</AlertDescription>
        </Alert>
    {/if}

    {#if !campaign}
        <div class="flex items-center justify-center py-8">
            <div class="text-center">
                <div
                    class="text-lg font-medium text-gray-900 dark:text-white"
                    data-testid="loading">
                    Loading campaign details…
                </div>
            </div>
        </div>
    {:else}
        <!-- Campaign Header -->
        <div class="mb-6">
            <div class="flex items-center justify-between">
                <div>
                    <h1
                        class="text-2xl font-semibold text-gray-900 dark:text-white"
                        data-testid="campaign-name">
                        {campaign.name}
                    </h1>
                    {#if campaign.description}
                        <p
                            class="mt-1 text-gray-600 dark:text-gray-400"
                            data-testid="campaign-description">
                            {campaign.description}
                        </p>
                    {/if}
                </div>
                <div class="flex items-center gap-4">
                    <Badge class={getStateBadge(campaign.state).color} data-testid="campaign-state">
                        {getStateBadge(campaign.state).label}
                    </Badge>
                    {#if campaign.state === 'draft' || campaign.state === 'paused'}
                        <Button onclick={handleStartCampaign} data-testid="start-campaign">
                            Start Campaign
                        </Button>
                    {:else if campaign.state === 'active'}
                        <Button
                            onclick={handleStopCampaign}
                            variant="outline"
                            data-testid="stop-campaign">
                            Stop Campaign
                        </Button>
                    {/if}
                </div>
            </div>

            <!-- Progress Bar -->
            {#if campaign.progress > 0}
                <div class="mt-4">
                    <Progress
                        value={campaign.progress}
                        class="h-2"
                        data-testid="campaign-progress" />
                    <p class="mt-1 text-sm text-gray-600">Progress: {campaign.progress}%</p>
                </div>
            {/if}
        </div>

        <!-- Progress and Metrics -->
        <div class="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <CampaignProgress
                campaignId={parseInt(campaignId ?? '0')}
                initialProgress={progress}
                enableAutoRefresh={true} />
            <CampaignMetrics
                campaignId={parseInt(campaignId ?? '0')}
                initialMetrics={metrics}
                enableAutoRefresh={true} />
        </div>

        <!-- Attacks Table -->
        <Card>
            <CardHeader>
                <div class="flex items-center justify-between">
                    <CardTitle>Attacks</CardTitle>
                    <div class="flex gap-2">
                        <Button onclick={handleAddAttack} data-testid="add-attack">
                            + Add Attack
                        </Button>
                        {#if campaign.attacks.length > 0}
                            <Button
                                onclick={handleRemoveAllAttacks}
                                variant="outline"
                                class="text-red-600"
                                data-testid="remove-all-attacks">
                                🗑️ All
                            </Button>
                        {/if}
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                {#if campaign.attacks.length === 0}
                    <div class="py-8 text-center text-gray-500" data-testid="no-attacks">
                        No attacks configured for this campaign.
                    </div>
                {:else}
                    <div class="overflow-x-auto" data-testid="attacks-table">
                        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                            <thead class="bg-gray-50 dark:bg-gray-700">
                                <tr>
                                    <th
                                        class="px-4 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-300"
                                        >Name</th>
                                    <th
                                        class="px-4 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-300"
                                        >Type</th>
                                    <th
                                        class="px-4 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-300"
                                        >Length</th>
                                    <th
                                        class="px-4 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-300"
                                        >Settings</th>
                                    <th
                                        class="px-4 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-300"
                                        >Keyspace</th>
                                    <th
                                        class="px-4 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-300"
                                        >Complexity</th>
                                    <th
                                        class="px-4 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-300"
                                        >Comment</th>
                                    <th
                                        class="w-16 px-4 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-300"
                                    ></th>
                                </tr>
                            </thead>
                            <tbody
                                class="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
                                <AttackTableBody
                                    attacks={transformAttacksForTable(campaign.attacks)}
                                    onMoveAttack={handleMoveAttackCallback}
                                    onEditAttack={(attackId) =>
                                        handleEditAttack(parseInt(attackId))}
                                    onDeleteAttack={(attackId) =>
                                        handleRemoveAttack(parseInt(attackId))}
                                    onDuplicateAttack={(attackId) =>
                                        handleDuplicateAttack(parseInt(attackId))} />
                            </tbody>
                        </table>
                    </div>
                {/if}
            </CardContent>
        </Card>

        <!-- Campaign Actions -->
        <div class="mt-6 flex justify-between">
            <Button onclick={() => goto('/campaigns')} variant="outline">
                ← Back to Campaigns
            </Button>
            <div class="flex gap-2">
                <!-- TODO: Add more campaign actions like export/import -->
            </div>
        </div>
    {/if}
</div>
