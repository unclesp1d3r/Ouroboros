<script lang="ts">
    import { goto } from '$app/navigation';
    import { page } from '$app/state';
    import { Card, CardHeader, CardTitle, CardContent } from '$lib/components/ui/card';
    import {
        Table,
        TableHead,
        TableHeader,
        TableBody,
        TableRow,
        TableCell,
    } from '$lib/components/ui/table';
    import { Button } from '$lib/components/ui/button';
    import { Badge } from '$lib/components/ui/badge';
    import { Input } from '$lib/components/ui/input';
    import {
        DropdownMenu,
        DropdownMenuTrigger,
        DropdownMenuContent,
        DropdownMenuItem,
    } from '$lib/components/ui/dropdown-menu';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Skeleton } from '$lib/components/ui/skeleton';
    import AttackViewModal from '$lib/components/attacks/AttackViewModal.svelte';

    import MoreHorizontalIcon from '@lucide/svelte/icons/more-horizontal';
    import PlusIcon from '@lucide/svelte/icons/plus';
    import SearchIcon from '@lucide/svelte/icons/search';
    import {
        getAttackTypeBadge,
        getAttackStateBadge,
        formatLength,
        formatKeyspace,
        type Attack,
        type AttacksResponse,
    } from '$lib/types/attack';

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
                            <Skeleton class="h-4 w-[100px]" />
                            <Skeleton class="h-4 w-[80px]" />
                            <Skeleton class="h-4 w-[60px]" />
                            <Skeleton class="h-4 w-[120px]" />
                            <Skeleton class="h-4 w-[80px]" />
                            <Skeleton class="h-4 w-[60px]" />
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
                            <TableHead class="w-16"></TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {#each attacks as attack (attack.id)}
                            <TableRow data-testid="attack-row-{attack.id}">
                                <TableCell class="font-medium">
                                    {attack.name}
                                    {#if attack.comment}
                                        <div class="text-muted-foreground mt-1 text-xs">
                                            {attack.comment}
                                        </div>
                                    {/if}
                                </TableCell>
                                <TableCell>
                                    <Badge
                                        variant={getAttackTypeBadge(attack.attack_mode || '')
                                            .variant as any}>
                                        {getAttackTypeBadge(attack.attack_mode || '').label}
                                    </Badge>
                                </TableCell>
                                <TableCell>
                                    <Badge
                                        variant={getAttackStateBadge(attack.state).variant as any}>
                                        {getAttackStateBadge(attack.state).label}
                                    </Badge>
                                </TableCell>
                                <TableCell>{attack.language || '—'}</TableCell>
                                <TableCell>
                                    {formatLength(attack.min_length)}
                                </TableCell>
                                <TableCell>
                                    {#if attack.settings_summary}
                                        <span
                                            class="cursor-help text-sm text-blue-600 hover:underline"
                                            title={attack.settings_summary}
                                            data-testid="settings-summary-{attack.id}">
                                            {attack.settings_summary.length > 30
                                                ? attack.settings_summary.substring(0, 30) + '...'
                                                : attack.settings_summary}
                                        </span>
                                    {:else}
                                        —
                                    {/if}
                                </TableCell>
                                <TableCell>{formatKeyspace(attack.keyspace)}</TableCell>
                                <TableCell>
                                    {#if attack.complexity_score}
                                        <div
                                            class="flex space-x-1"
                                            title="Complexity: {attack.complexity_score}/5"
                                            data-testid="complexity-{attack.id}">
                                            {#each Array(5) as _, i (i)}
                                                <span
                                                    class={i < attack.complexity_score
                                                        ? 'h-2 w-2 rounded-full bg-gray-600'
                                                        : 'h-2 w-2 rounded-full bg-gray-200'}
                                                ></span>
                                            {/each}
                                        </div>
                                    {:else}
                                        —
                                    {/if}
                                </TableCell>
                                <TableCell>
                                    {#if attack.campaign_name}
                                        <span
                                            class="cursor-pointer text-sm text-blue-600 hover:underline">
                                            {attack.campaign_name}
                                        </span>
                                    {:else}
                                        <span class="text-muted-foreground">—</span>
                                    {/if}
                                </TableCell>
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
