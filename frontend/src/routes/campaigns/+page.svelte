<script lang="ts">
    import { browser } from '$app/environment';
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { Badge } from '$lib/components/ui/badge';
    import { Button } from '$lib/components/ui/button';
    import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
    import {
        DropdownMenu,
        DropdownMenuCheckboxItem,
        DropdownMenuContent,
        DropdownMenuLabel,
        DropdownMenuSeparator,
        DropdownMenuTrigger,
    } from '$lib/components/ui/dropdown-menu';
    import { Input } from '$lib/components/ui/input';
    import * as Pagination from '$lib/components/ui/pagination';
    import { Popover, PopoverContent, PopoverTrigger } from '$lib/components/ui/popover';
    import { Progress } from '$lib/components/ui/progress';
    import {
        Table,
        TableBody,
        TableCell,
        TableHead,
        TableHeader,
        TableRow,
    } from '$lib/components/ui/table';
    import {
        ChevronDown,
        ChevronUp,
        ChevronsUpDown,
        Funnel,
        MoreHorizontal,
        Plus,
        X,
    } from '@lucide/svelte';
    import { onMount } from 'svelte';

    import CrackableUploadModal from '$lib/components/campaigns/CrackableUploadModal.svelte';
    import { CampaignState, type CampaignState as CampaignStateType } from '$lib/schemas/base';
    import type { CampaignWithUIData } from './+page.server';

    interface PageData {
        campaigns: CampaignWithUIData[];
        pagination: {
            page: number;
            size: number;
            total: number;
            pages: number;
        };
    }

    let { data }: { data: PageData } = $props();

    // Browser storage keys
    const STORAGE_KEY_SEARCH = 'campaigns-search-term';
    const STORAGE_KEY_STATUS = 'campaigns-status-filters';
    const STORAGE_KEY_SORT = 'campaigns-sort-config';

    // Modal state
    let showUploadModal = $state(false);

    // UI state
    let expandedRows = $state<{ [key: string]: boolean }>({});

    // Sorting state
    type SortField = 'name' | 'state' | 'progress' | 'updated_at';
    type SortDirection = 'asc' | 'desc';

    interface SortConfig {
        field: SortField;
        direction: SortDirection;
    }

    let sortConfig = $state<SortConfig>({ field: 'state', direction: 'asc' });

    // Use actual CampaignState values from OpenAPI schema
    const allStatuses = CampaignState.options; // ['draft', 'active', 'archived']

    // Filter state with browser storage persistence
    let searchTerm = $state('');

    // Initialize selectedStatuses with all statuses selected by default
    function createDefaultStatusMap(): { [key: string]: boolean } {
        const statusMap: { [key: string]: boolean } = {};
        for (const status of allStatuses) {
            statusMap[status] = true;
        }
        return statusMap;
    }
    let selectedStatuses = $state<{ [key: string]: boolean }>(createDefaultStatusMap());

    // Initialize filters from browser storage
    onMount(() => {
        if (browser) {
            // Load search term from localStorage
            const savedSearch = localStorage.getItem(STORAGE_KEY_SEARCH);
            if (savedSearch) {
                searchTerm = savedSearch;
            }

            // Load status filters from localStorage
            const savedStatuses = localStorage.getItem(STORAGE_KEY_STATUS);
            if (savedStatuses) {
                try {
                    const parsed = JSON.parse(savedStatuses);
                    selectedStatuses = parsed;
                } catch (e) {
                    console.warn('Failed to parse saved status filters:', e);
                    // Keep the default initialization (all selected)
                }
            }
            // If no saved statuses, keep the default initialization (all selected)

            // Load sort configuration from localStorage
            const savedSort = localStorage.getItem(STORAGE_KEY_SORT);
            if (savedSort) {
                try {
                    const parsed = JSON.parse(savedSort);
                    sortConfig = parsed;
                } catch (e) {
                    console.warn('Failed to parse saved sort configuration:', e);
                    // Keep the default initialization
                }
            }
        }
    });

    // Reset status filters to all selected
    function resetStatusFilters() {
        const statusMap: { [key: string]: boolean } = {};
        for (const status of allStatuses) {
            statusMap[status] = true;
        }
        selectedStatuses = statusMap;
    }

    // Save filters to browser storage
    function saveFiltersToStorage() {
        if (browser) {
            localStorage.setItem(STORAGE_KEY_SEARCH, searchTerm);
            localStorage.setItem(STORAGE_KEY_STATUS, JSON.stringify(selectedStatuses));
            localStorage.setItem(STORAGE_KEY_SORT, JSON.stringify(sortConfig));
        }
    }

    // Sorting functions
    function handleSort(field: SortField) {
        if (sortConfig.field === field) {
            // Toggle direction if same field
            sortConfig.direction = sortConfig.direction === 'asc' ? 'desc' : 'asc';
        } else {
            // Set new field with default ascending direction
            sortConfig.field = field;
            sortConfig.direction = 'asc';
        }
        sortConfig = { ...sortConfig }; // Trigger reactivity
        saveFiltersToStorage();
    }

    function getSortIcon(field: SortField) {
        if (sortConfig.field !== field) {
            return ChevronsUpDown;
        }
        return sortConfig.direction === 'asc' ? ChevronUp : ChevronDown;
    }

    function sortCampaigns(campaigns: CampaignWithUIData[]): CampaignWithUIData[] {
        const sorted = [...campaigns].sort((a, b) => {
            let aValue: string | number;
            let bValue: string | number;

            switch (sortConfig.field) {
                case 'name': {
                    aValue = a.name.toLowerCase();
                    bValue = b.name.toLowerCase();
                    break;
                }
                case 'state': {
                    // Sort by state priority: active > draft > archived
                    const statePriority = { active: 3, draft: 2, archived: 1 };
                    aValue = statePriority[a.state as keyof typeof statePriority] || 0;
                    bValue = statePriority[b.state as keyof typeof statePriority] || 0;
                    break;
                }
                case 'progress': {
                    aValue = a.progress;
                    bValue = b.progress;
                    break;
                }
                case 'updated_at': {
                    aValue = new Date(a.updated_at).getTime();
                    bValue = new Date(b.updated_at).getTime();
                    break;
                }
                default:
                    return 0;
            }

            if (aValue < bValue) {
                return sortConfig.direction === 'asc' ? -1 : 1;
            }
            if (aValue > bValue) {
                return sortConfig.direction === 'asc' ? 1 : -1;
            }
            return 0;
        });

        return sorted;
    }

    // Real-time filtered and sorted campaigns
    let filteredCampaigns = $derived.by(() => {
        let filtered = data.campaigns;

        // Filter by search term (case-insensitive)
        if (searchTerm.trim()) {
            const searchLower = searchTerm.toLowerCase();
            filtered = filtered.filter(
                (campaign) =>
                    campaign.name.toLowerCase().includes(searchLower) ||
                    campaign.summary.toLowerCase().includes(searchLower)
            );
        }

        // Filter by selected statuses
        const activeStatuses = Object.entries(selectedStatuses)
            .filter(([, isSelected]) => isSelected)
            .map(([status]) => status);

        if (activeStatuses.length > 0 && activeStatuses.length < allStatuses.length) {
            filtered = filtered.filter((campaign) => activeStatuses.includes(campaign.state));
        }

        // Apply sorting
        return sortCampaigns(filtered);
    });

    // Handle search input changes (real-time)
    function handleSearchChange() {
        saveFiltersToStorage();
    }

    // Handle status filter changes
    function handleStatusChange(status: string, checked: boolean) {
        selectedStatuses[status] = checked;
        selectedStatuses = { ...selectedStatuses }; // Trigger reactivity
        saveFiltersToStorage();
    }

    // Clear all filters
    function clearFilters() {
        searchTerm = '';
        resetStatusFilters();
        sortConfig = { field: 'state', direction: 'asc' }; // Reset to default sort
        saveFiltersToStorage();
    }

    function handleClearFilters() {
        clearFilters();
    }

    // Count active filters for display
    const activeFilterCount = $derived.by(() => {
        let count = 0;
        if (searchTerm.trim()) count++;

        const activeStatuses = Object.values(selectedStatuses).filter(Boolean).length;
        if (activeStatuses < allStatuses.length) count++;

        return count;
    });

    function campaignStatusBadge(state: CampaignStateType): {
        variant: 'default' | 'secondary' | 'destructive' | 'outline';
        label: string;
    } {
        switch (state) {
            case 'active':
                return { variant: 'default', label: 'Active' };
            case 'draft':
                return { variant: 'secondary', label: 'Draft' };
            case 'archived':
                return { variant: 'outline', label: 'Archived' };
            default:
                return { variant: 'secondary', label: state };
        }
    }

    function toggleRow(campaignId: number) {
        expandedRows[campaignId] = !expandedRows[campaignId];
    }

    function openCreateModal() {
        goto('/campaigns/new');
    }

    function openUploadModal() {
        showUploadModal = true;
    }

    function openEditModal(campaign: CampaignWithUIData) {
        console.log('Edit', campaign.id);
        // Implement modal logic
    }

    function openDeleteModal(campaign: CampaignWithUIData) {
        console.log('Delete', campaign.id);
        // Implement modal logic
    }

    function handlePageChange(newPage: number) {
        const url = new URL($page.url);
        url.searchParams.set('page', newPage.toString());
        goto(url.toString());
    }

    function formatLastUpdated(dateString: string): string {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

        if (diffInSeconds < 60) {
            return 'Just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes}m ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours}h ago`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days}d ago`;
        }
    }
</script>

<svelte:head>
    <title>Campaigns - Ouroboros</title>
</svelte:head>

<Card>
    <CardHeader>
        <div class="flex items-center justify-between">
            <CardTitle data-testid="campaigns-title">Campaigns</CardTitle>
            <div class="flex items-center gap-2">
                <div class="relative">
                    <Input
                        class="max-w-sm pr-8"
                        placeholder="Search campaigns..."
                        type="search"
                        bind:value={searchTerm}
                        oninput={handleSearchChange} />
                    {#if searchTerm.trim()}
                        <button
                            class="absolute top-1/2 right-2 -translate-y-1/2 rounded p-1 hover:bg-gray-100"
                            onclick={() => {
                                searchTerm = '';
                                handleSearchChange();
                            }}
                            title="Clear search">
                            <X class="h-3 w-3" />
                        </button>
                    {/if}
                </div>
                <DropdownMenu>
                    <DropdownMenuTrigger
                        class="border-input bg-background ring-offset-background placeholder:text-muted-foreground focus-visible:ring-ring flex h-10 items-center justify-center rounded-md border px-3 py-2 text-sm file:border-0 file:bg-transparent file:text-sm file:font-medium focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                        data-testid="status-filter-trigger">
                        <Funnel class="mr-2 h-4 w-4" />
                        Status
                        {#if activeFilterCount > 0}
                            <Badge
                                variant="secondary"
                                class="ml-2 h-5 w-5 rounded-full p-0 text-xs">
                                {activeFilterCount}
                            </Badge>
                        {/if}
                    </DropdownMenuTrigger>
                    <DropdownMenuContent class="w-56">
                        <DropdownMenuLabel>Filter by Status</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        {#each allStatuses as status (status)}
                            <DropdownMenuCheckboxItem
                                checked={selectedStatuses[status]}
                                onCheckedChange={(checked) =>
                                    handleStatusChange(status, checked ?? false)}>
                                {status.charAt(0).toUpperCase() + status.slice(1)}
                            </DropdownMenuCheckboxItem>
                        {/each}
                        {#if activeFilterCount > 0}
                            <DropdownMenuSeparator />
                            <Button variant="ghost" size="sm" class="w-full" onclick={clearFilters}>
                                Clear All Filters
                            </Button>
                        {/if}
                    </DropdownMenuContent>
                </DropdownMenu>
                <Button
                    data-testid="upload-campaign-button"
                    variant="outline"
                    onclick={openUploadModal}>
                    Upload & Crack
                </Button>
                <Button data-testid="create-campaign-button" onclick={openCreateModal}>
                    <Plus class="mr-2 h-4 w-4" />
                    Create Campaign
                </Button>
            </div>
        </div>
        <div class="text-muted-foreground flex items-center gap-2 text-sm">
            <span>Showing {filteredCampaigns.length} of {data.pagination.total} campaigns</span>
            {#if activeFilterCount > 0}
                <Button variant="link" size="sm" class="h-auto p-0" onclick={clearFilters}>
                    Clear filters
                </Button>
            {/if}
        </div>
    </CardHeader>
    <CardContent data-testid="campaigns-container">
        {#if filteredCampaigns.length === 0}
            <div class="py-8 text-center">
                {#if activeFilterCount > 0}
                    <p>No campaigns found matching your filters.</p>
                    <Button variant="outline" class="mt-4" onclick={clearFilters}>
                        Clear Filters
                    </Button>
                {:else}
                    <p>No campaigns found matching your criteria.</p>
                    <Button
                        data-testid="empty-state-create-button"
                        class="mt-4"
                        onclick={openCreateModal}>
                        <Plus class="mr-2 h-4 w-4" />
                        Create Your First Campaign
                    </Button>
                {/if}
            </div>
        {:else}
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead class="w-[50px]"></TableHead>
                        <TableHead>
                            <Button
                                variant="ghost"
                                class="h-auto p-0 font-semibold hover:bg-transparent"
                                onclick={() => handleSort('name')}>
                                <span>Campaign</span>
                                {@const SortIcon = getSortIcon('name')}
                                <SortIcon class="ml-1 h-4 w-4" />
                            </Button>
                        </TableHead>
                        <TableHead class="w-[120px]">
                            <Button
                                variant="ghost"
                                class="h-auto p-0 font-semibold hover:bg-transparent"
                                onclick={() => handleSort('state')}>
                                <span>Status</span>
                                {@const SortIcon = getSortIcon('state')}
                                <SortIcon class="ml-1 h-4 w-4" />
                            </Button>
                        </TableHead>
                        <TableHead class="w-[200px]">
                            <Button
                                variant="ghost"
                                class="h-auto p-0 font-semibold hover:bg-transparent"
                                onclick={() => handleSort('progress')}>
                                <span>Progress</span>
                                {@const SortIcon = getSortIcon('progress')}
                                <SortIcon class="ml-1 h-4 w-4" />
                            </Button>
                        </TableHead>
                        <TableHead>Summary</TableHead>
                        <TableHead class="w-[100px]">
                            <Button
                                variant="ghost"
                                class="h-auto p-0 font-semibold hover:bg-transparent"
                                onclick={() => handleSort('updated_at')}>
                                <span>Last Updated</span>
                                {@const SortIcon = getSortIcon('updated_at')}
                                <SortIcon class="ml-1 h-4 w-4" />
                            </Button>
                        </TableHead>
                        <TableHead class="w-[50px]"></TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {#each filteredCampaigns as campaign (campaign.id)}
                        <TableRow>
                            <TableCell>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    class="h-8 w-8"
                                    onclick={() => toggleRow(campaign.id)}>
                                    <ChevronDown
                                        class="h-4 w-4 transition-transform {expandedRows[
                                            campaign.id
                                        ]
                                            ? 'rotate-180'
                                            : ''}" />
                                </Button>
                            </TableCell>
                            <TableCell class="font-medium">
                                <a
                                    href="/campaigns/{campaign.id}"
                                    data-testid="campaign-link-{campaign.id}"
                                    class="hover:underline">
                                    {campaign.name}
                                </a>
                            </TableCell>
                            <TableCell>
                                <Badge variant={campaignStatusBadge(campaign.state).variant}>
                                    {campaignStatusBadge(campaign.state).label}
                                </Badge>
                            </TableCell>
                            <TableCell>
                                <div class="flex items-center gap-2">
                                    <Progress value={campaign.progress} class="h-2" />
                                    <span>{campaign.progress.toFixed(0)}%</span>
                                </div>
                            </TableCell>
                            <TableCell>{campaign.summary}</TableCell>
                            <TableCell class="text-muted-foreground text-sm">
                                {formatLastUpdated(campaign.updated_at)}
                            </TableCell>
                            <TableCell>
                                <Popover>
                                    <PopoverTrigger>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            class="h-8 w-8"
                                            data-testid="campaign-menu-{campaign.id}">
                                            <span class="sr-only">Open menu</span>
                                            <MoreHorizontal class="h-4 w-4" />
                                        </Button>
                                    </PopoverTrigger>
                                    <PopoverContent class="w-40 p-1">
                                        <div class="grid gap-1">
                                            <Button
                                                variant="ghost"
                                                class="w-full justify-start"
                                                onclick={() => openEditModal(campaign)}>
                                                Edit Campaign
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                class="w-full justify-start"
                                                onclick={() => openDeleteModal(campaign)}>
                                                Delete Campaign
                                            </Button>
                                        </div>
                                    </PopoverContent>
                                </Popover>
                            </TableCell>
                        </TableRow>
                        {#if expandedRows[campaign.id]}
                            <TableRow>
                                <TableCell colspan={7}>
                                    <div class="p-4">
                                        {#if campaign.attacks.length > 0}
                                            <h4 class="mb-2 font-semibold">Attacks</h4>
                                            <!-- Attack sub-table would go here -->
                                            <pre>{JSON.stringify(campaign.attacks, null, 2)}</pre>
                                        {:else}
                                            <p>No attacks configured for this campaign.</p>
                                        {/if}
                                    </div>
                                </TableCell>
                            </TableRow>
                        {/if}
                    {/each}
                </TableBody>
            </Table>
            {#if data.pagination.pages > 1}
                <div class="mt-4 flex justify-center">
                    <Pagination.Root
                        count={data.pagination.total}
                        perPage={data.pagination.size}
                        page={data.pagination.page}
                        onPageChange={handlePageChange}>
                        {#snippet children({ pages }: { pages: any[] })}
                            <Pagination.Content>
                                <Pagination.Item>
                                    <Pagination.PrevButton />
                                </Pagination.Item>
                                {#each pages as page (page.key)}
                                    {#if page.type === 'ellipsis'}
                                        <Pagination.Item>
                                            <Pagination.Ellipsis />
                                        </Pagination.Item>
                                    {:else}
                                        <Pagination.Item>
                                            <Pagination.Link
                                                page={page.value}
                                                isActive={page.isActive}>
                                                {page.value}
                                            </Pagination.Link>
                                        </Pagination.Item>
                                    {/if}
                                {/each}
                                <Pagination.Item>
                                    <Pagination.NextButton />
                                </Pagination.Item>
                            </Pagination.Content>
                        {/snippet}
                    </Pagination.Root>
                </div>
            {/if}
        {/if}
    </CardContent>
</Card>

<CrackableUploadModal bind:open={showUploadModal} />
