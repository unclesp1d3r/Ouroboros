<script lang="ts">
    import { goto } from '$app/navigation';
    import { page } from '$app/state';
    import AttackViewModal from '$lib/components/attacks/AttackViewModal.svelte';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Badge } from '$lib/components/ui/badge';
    import { Button } from '$lib/components/ui/button';
    import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
    import {
        DropdownMenu,
        DropdownMenuContent,
        DropdownMenuItem,
        DropdownMenuTrigger,
    } from '$lib/components/ui/dropdown-menu';
    import { Input } from '$lib/components/ui/input';
    import { Skeleton } from '$lib/components/ui/skeleton';
    import {
        Table,
        TableBody,
        TableCell,
        TableHead,
        TableHeader,
        TableRow,
    } from '$lib/components/ui/table';

    import {
        getAttackStateBadge,
        getAttackTypeBadge,
        type Attack,
        type AttacksResponse,
    } from '$lib/types/attack';
    import MoreHorizontalIcon from '@lucide/svelte/icons/more-horizontal';
    import PlusIcon from '@lucide/svelte/icons/plus';
    import SearchIcon from '@lucide/svelte/icons/search';

    // Helper function to format length range
    function formatLengthRange(
        minLength: number | null | undefined,
        maxLength: number | null | undefined
    ): string {
        if (minLength == null && maxLength == null) return '—';
        if (minLength == null) return maxLength?.toString() || '—';
        if (maxLength == null) return minLength.toString();
        if (minLength === maxLength) return minLength.toString();
        return `${minLength} → ${maxLength}`;
    }

    // Helper function to format keyspace with commas
    function formatKeyspaceWithCommas(keyspace: number | null | undefined): string {
        if (keyspace == null) return '—';
        return keyspace.toLocaleString();
    }

    // Define page data type
    interface PageData {
        attacks: AttacksResponse;
        error?: string;
    }

    // SSR data from +page.server.ts
    let { data } = $props<{ data: PageData }>();

    // Reactive state using Svelte 5 runes
    let searchQuery = $state(page.url.searchParams.get('q') || '');
    let loading = $state(false);
    let error = $state(data.error || '');

    // Extract attacks data from SSR using $derived
    let attacks = $derived(data.attacks?.items || []);
    let total = $derived(data.attacks?.total || 0);
    let totalPages = $derived(data.attacks?.total_pages || 0);
    let currentPage = $derived(data.attacks?.page || 1);

    // Debounce search
    let searchTimeout: ReturnType<typeof setTimeout>;

    function handleSearch(event: Event) {
        const target = event.target as HTMLInputElement;
        searchQuery = target.value;

        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            // Update URL with search parameters
            const url = new URL(page.url);
            if (searchQuery.trim()) {
                url.searchParams.set('q', searchQuery.trim());
            } else {
                url.searchParams.delete('q');
            }
            url.searchParams.set('page', '1'); // Reset to first page when searching
            goto(url.toString(), { replaceState: true });
        }, 300);
    }

    function handlePageChange(newPage: number) {
        const url = new URL(page.url);
        url.searchParams.set('page', newPage.toString());
        goto(url.toString());
    }

    function renderComplexityDots(score?: number): { filled: number; total: number } {
        const complexityScore = score || 0;
        return { filled: complexityScore, total: 5 };
    }

    // Modal state
    let showViewModal = $state(false);
    let selectedAttack: Attack | null = $state(null);

    async function handleNewAttack() {
        // Navigate to the new attack wizard route
        goto('/attacks/new');
    }

    async function handleEditAttack(attackId: number) {
        // Navigate to the edit attack wizard route
        goto(`/attacks/${attackId}/edit`);
    }

    async function handleViewAttack(attackId: number) {
        const attack = attacks.find((a: Attack) => a.id === attackId);
        if (attack) {
            selectedAttack = attack;
            showViewModal = true;
        }
    }

    function handleViewClose() {
        showViewModal = false;
        selectedAttack = null;
    }

    async function handleDuplicateAttack(attackId: number) {
        try {
            loading = true;
            const response = await fetch(`/api/v1/web/attacks/${attackId}/duplicate`, {
                method: 'POST',
            });
            if (!response.ok) {
                throw new Error('Failed to duplicate attack');
            }
            // Refresh page to show duplicated attack
            goto(page.url.toString(), { invalidateAll: true });
        } catch (e) {
            error = 'Failed to duplicate attack.';
        } finally {
            loading = false;
        }
    }

    async function handleDeleteAttack(attackId: number) {
        if (confirm('Are you sure you want to delete this attack?')) {
            try {
                loading = true;
                const response = await fetch(`/api/v1/web/attacks/${attackId}`, {
                    method: 'DELETE',
                });
                if (!response.ok) {
                    throw new Error('Failed to delete attack');
                }
                // Refresh page to remove deleted attack
                goto(page.url.toString(), { invalidateAll: true });
            } catch (e) {
                error = 'Failed to delete attack.';
            } finally {
                loading = false;
            }
        }
    }
</script>

<svelte:head>
    <title>Attacks - Ouroboros</title>
</svelte:head>

<div class="container mx-auto max-w-7xl p-6">
    <!-- Header -->
    <div class="mb-6">
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-3xl font-bold tracking-tight">Attacks</h1>
                <p class="text-muted-foreground mt-2">
                    Manage and monitor attack configurations across all campaigns
                </p>
            </div>
            <Button onclick={handleNewAttack} data-testid="new-attack-button">
                <PlusIcon class="mr-2 h-4 w-4" />
                New Attack
            </Button>
        </div>
    </div>

    <!-- Search Bar -->
    <Card class="mb-6">
        <CardContent class="pt-6">
            <div class="relative">
                <SearchIcon
                    class="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
                <Input
                    type="text"
                    placeholder="Search attacks by name, type, or settings..."
                    class="pl-10"
                    value={searchQuery}
                    oninput={handleSearch}
                    data-testid="search-input" />
            </div>
        </CardContent>
    </Card>

    <!-- Error Alert -->
    {#if error}
        <Alert class="mb-6" variant="destructive" data-testid="error-alert">
            <AlertDescription>{error}</AlertDescription>
        </Alert>
    {/if}

    <!-- Attacks Table -->
    <Card>
        <CardHeader>
            <CardTitle>
                Attacks
                {#if total > 0}
                    <span class="text-muted-foreground ml-2 text-sm font-normal">
                        ({total.toLocaleString()} total)
                    </span>
                {/if}
            </CardTitle>
        </CardHeader>
        <CardContent>
            {#if loading}
                <!-- Loading skeleton -->
                <div class="space-y-3" data-testid="loading-skeleton">
                    {#each Array(5) as _, i (i)}
                        <div class="flex space-x-4">
                            <Skeleton class="h-4 w-[150px]" />
                            <Skeleton class="h-4 w-[80px]" />
                            <Skeleton class="h-4 w-[60px]" />
                            <Skeleton class="h-4 w-[80px]" />
                            <Skeleton class="h-4 w-[100px]" />
                            <Skeleton class="h-4 w-[40px]" />
                        </div>
                    {/each}
                </div>
            {:else if attacks.length === 0}
                <!-- Empty state -->
                <div class="text-muted-foreground py-8 text-center" data-testid="empty-state">
                    {#if searchQuery}
                        <p>No attacks found matching "{searchQuery}".</p>
                        <Button
                            variant="link"
                            onclick={() => {
                                searchQuery = '';
                                const url = new URL(page.url);
                                url.searchParams.delete('q');
                                url.searchParams.set('page', '1');
                                goto(url.toString(), { replaceState: true });
                            }}
                            class="mt-2">
                            Clear search
                        </Button>
                    {:else}
                        <p>No attacks configured yet.</p>
                        <Button onclick={handleNewAttack} class="mt-4">
                            <PlusIcon class="mr-2 h-4 w-4" />
                            Create your first attack
                        </Button>
                    {/if}
                </div>
            {:else}
                <!-- Attacks table -->
                <Table data-testid="attacks-table">
                    <TableHeader>
                        <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead>State</TableHead>
                            <TableHead>Language</TableHead>
                            <TableHead>Length</TableHead>
                            <TableHead>Settings</TableHead>
                            <TableHead>Keyspace</TableHead>
                            <TableHead>Complexity</TableHead>
                            <TableHead>Campaign</TableHead>
                            <TableHead>Comments</TableHead>
                            <TableHead class="w-16"></TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {#each attacks as attack (attack.id)}
                            <TableRow data-testid="attack-row-{attack.id}">
                                <TableCell class="font-medium">
                                    {attack.name}
                                </TableCell>
                                <TableCell>
                                    <Badge
                                        variant={getAttackTypeBadge(attack.attack_mode || '')
                                            .variant as any}>
                                        {attack.type_label ||
                                            getAttackTypeBadge(attack.attack_mode || '').label}
                                    </Badge>
                                </TableCell>
                                <TableCell>
                                    <Badge
                                        variant={getAttackStateBadge(attack.state).variant as any}>
                                        {getAttackStateBadge(attack.state).label}
                                    </Badge>
                                </TableCell>
                                <TableCell>{attack.language || '—'}</TableCell>
                                <TableCell
                                    >{formatLengthRange(
                                        attack.min_length,
                                        attack.max_length
                                    )}</TableCell>
                                <TableCell>
                                    <span
                                        class="cursor-pointer text-blue-600 hover:text-blue-800"
                                        data-testid="settings-summary-{attack.id}">
                                        {attack.settings_summary}
                                    </span>
                                </TableCell>
                                <TableCell>{formatKeyspaceWithCommas(attack.keyspace)}</TableCell>
                                <TableCell>
                                    {#if attack.complexity_score}
                                        <div
                                            class="flex space-x-1"
                                            data-testid="complexity-{attack.id}">
                                            {#each Array(Math.min(attack.complexity_score, 5)) as _, i (i)}
                                                <span class="h-2 w-2 rounded-full bg-gray-600"
                                                ></span>
                                            {/each}
                                            {#each Array(Math.max(0, 5 - attack.complexity_score)) as _, i (i + Math.min(attack.complexity_score, 5))}
                                                <span class="h-2 w-2 rounded-full bg-gray-200"
                                                ></span>
                                            {/each}
                                        </div>
                                    {:else}
                                        —
                                    {/if}
                                </TableCell>
                                <TableCell>{attack.campaign_name || '—'}</TableCell>
                                <TableCell>{attack.comment || '—'}</TableCell>
                                <TableCell>
                                    <DropdownMenu>
                                        <DropdownMenuTrigger>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                data-testid="attack-menu-{attack.id}">
                                                <MoreHorizontalIcon class="h-4 w-4" />
                                                <span class="sr-only">Open menu</span>
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end">
                                            <DropdownMenuItem
                                                onclick={() => handleViewAttack(attack.id)}>
                                                View Details
                                            </DropdownMenuItem>
                                            <DropdownMenuItem
                                                onclick={() => handleEditAttack(attack.id)}>
                                                Edit
                                            </DropdownMenuItem>
                                            <DropdownMenuItem
                                                onclick={() => handleDuplicateAttack(attack.id)}>
                                                Duplicate
                                            </DropdownMenuItem>
                                            <DropdownMenuItem
                                                onclick={() => handleDeleteAttack(attack.id)}
                                                class="text-red-600">
                                                Delete
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </TableCell>
                            </TableRow>
                        {/each}
                    </TableBody>
                </Table>

                <!-- Pagination -->
                {#if totalPages > 1}
                    <div class="mt-6 flex items-center justify-between">
                        <div class="text-muted-foreground text-sm">
                            Showing page {currentPage} of {totalPages} ({total.toLocaleString()} total)
                        </div>
                        <div class="flex space-x-2">
                            <Button
                                variant="outline"
                                onclick={() => handlePageChange(currentPage - 1)}
                                disabled={currentPage <= 1}
                                data-testid="prev-page">
                                Previous
                            </Button>
                            <Button
                                variant="outline"
                                onclick={() => handlePageChange(currentPage + 1)}
                                disabled={currentPage >= totalPages}
                                data-testid="next-page">
                                Next
                            </Button>
                        </div>
                    </div>
                {/if}
            {/if}
        </CardContent>
    </Card>
</div>

<!-- Modals -->
<AttackViewModal bind:open={showViewModal} attack={selectedAttack} />
