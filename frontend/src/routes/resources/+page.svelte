<script lang="ts">
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { Button } from '$lib/components/ui/button';

    import { Badge } from '$lib/components/ui/badge';
    import {
        Card,
        CardContent,
        CardDescription,
        CardHeader,
        CardTitle,
    } from '$lib/components/ui/card';
    import {
        Table,
        TableBody,
        TableCell,
        TableHead,
        TableHeader,
        TableRow,
    } from '$lib/components/ui/table';
    import { type AttackResourceType } from '$lib/schemas/base';
    import { FileText, Filter, Search, Upload } from '@lucide/svelte';
    import type { PageData } from './$types';
    // Note: Using SSR data directly, no store imports needed

    let { data }: { data: PageData } = $props();

    // Resource types for filtering
    const resourceTypes = [
        { value: '', label: 'All Types' },
        { value: 'word_list', label: 'Word List' },
        { value: 'rule_list', label: 'Rule List' },
        { value: 'mask_list', label: 'Mask List' },
        { value: 'charset', label: 'Charset' },
        { value: 'dynamic_word_list', label: 'Dynamic Word List' },
        { value: 'ephemeral_word_list', label: 'Ephemeral Word List' },
        { value: 'ephemeral_mask_list', label: 'Ephemeral Mask List' },
        { value: 'ephemeral_rule_list', label: 'Ephemeral Rule List' },
    ];

    // Hydrate store with SSR data whenever data changes
    // Note: Using SSR data directly, no store hydration needed

    // Use SSR data directly (like campaigns page)
    let resourceItems = $derived(data.resources.items);
    let totalCount = $derived(data.resources.total);
    let currentPage = $derived(data.resources.page ?? 1);
    let pageSize = $derived(data.resources.page_size ?? 25);
    let totalPages = $derived(Math.ceil(totalCount / pageSize));

    // Filter state from URL parameters with proper runes
    let searchQuery = $derived($page.url.searchParams.get('q') || '');
    let selectedResourceType = $derived($page.url.searchParams.get('resource_type') || '');
    let filterApplied = $derived(!!(searchQuery.trim() || selectedResourceType));

    // Local state for form inputs using runes
    let searchInput = $state('');
    let resourceTypeInput = $state('');

    // Update local inputs when URL changes using effect
    $effect(() => {
        searchInput = searchQuery;
        resourceTypeInput = selectedResourceType;
    });

    function updateURL() {
        const params = new URLSearchParams();

        if (searchInput.trim()) params.set('q', searchInput.trim());
        if (resourceTypeInput) params.set('resource_type', resourceTypeInput);
        if (currentPage > 1) params.set('page', currentPage.toString());
        if (pageSize !== 25) params.set('page_size', pageSize.toString());

        const newUrl = `/resources${params.toString() ? '?' + params.toString() : ''}`;
        goto(newUrl, { replaceState: true, noScroll: true });
    }

    function handleFilter() {
        // Reset to first page when filtering
        const params = new URLSearchParams();

        if (searchInput.trim()) params.set('q', searchInput.trim());
        if (resourceTypeInput) params.set('resource_type', resourceTypeInput);
        params.set('page', '1');
        if (pageSize !== 25) params.set('page_size', pageSize.toString());

        const newUrl = `/resources${params.toString() ? '?' + params.toString() : ''}`;
        goto(newUrl, { replaceState: true, noScroll: true });
    }

    function handlePageChange(newPage: number) {
        const params = new URLSearchParams($page.url.searchParams);
        params.set('page', newPage.toString());

        const newUrl = `/resources?${params.toString()}`;
        goto(newUrl, { replaceState: true, noScroll: true });
    }

    function formatResourceType(type: AttackResourceType): string {
        return type.replace('_', ' ').replaceAll(/\b\w/g, (l) => l.toUpperCase());
    }

    function formatFileSize(bytes: number | null | undefined): string {
        if (!bytes) return '0 KB';
        const kb = Math.round(bytes / 1024);
        return `${kb.toLocaleString()} KB`;
    }

    function formatDate(dateStr: string | null | undefined): string {
        if (!dateStr) return '';
        return new Date(dateStr).toLocaleDateString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        });
    }

    function getResourceTypeVariant(
        type: AttackResourceType
    ): 'default' | 'secondary' | 'destructive' | 'outline' {
        switch (type) {
            case 'mask_list':
                return 'default';
            case 'rule_list':
                return 'secondary';
            case 'word_list':
                return 'outline';
            case 'charset':
                return 'destructive';
            case 'dynamic_word_list':
                return 'secondary';
            default:
                return 'outline';
        }
    }
</script>

<svelte:head>
    <title>Resources - Ouroboros</title>
</svelte:head>

<div class="container mx-auto space-y-6 p-6">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-3xl font-bold tracking-tight">Resources</h1>
            <p class="text-muted-foreground">
                Manage wordlists, rule lists, masks, and charsets for password cracking attacks
            </p>
        </div>
        <Button class="gap-2">
            <Upload class="h-4 w-4" />
            Upload Resource
        </Button>
    </div>

    <!-- Filters -->
    <Card>
        <CardHeader>
            <CardTitle class="flex items-center gap-2">
                <Filter class="h-4 w-4" />
                Filters
            </CardTitle>
            <CardDescription>Search and filter resources by type and name</CardDescription>
        </CardHeader>
        <CardContent>
            <div class="flex flex-wrap items-end gap-4">
                <div class="min-w-[200px] flex-1">
                    <label for="search" class="mb-2 block text-sm font-medium">Search</label>
                    <div class="relative">
                        <Search
                            class="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 transform" />
                        <input
                            id="search"
                            type="text"
                            placeholder="Search resources..."
                            bind:value={searchInput}
                            class="form-input w-full rounded border px-2 py-1 pl-10"
                            onkeydown={(e) => {
                                if (e.key === 'Enter') {
                                    handleFilter();
                                }
                            }} />
                    </div>
                </div>
                <div class="min-w-[180px]">
                    <label for="resource-type" class="mb-2 block text-sm font-medium"
                        >Resource Type</label>
                    <select
                        id="resource-type"
                        bind:value={resourceTypeInput}
                        class="bg-background rounded border px-2 py-1">
                        {#each resourceTypes as type (type.value)}
                            <option value={type.value}>{type.label}</option>
                        {/each}
                    </select>
                </div>
                <Button onclick={handleFilter} class="gap-2">
                    <Search class="h-4 w-4" />
                    Filter
                </Button>
                {#if filterApplied}
                    <Button
                        variant="outline"
                        onclick={() => {
                            searchInput = '';
                            resourceTypeInput = '';
                            handleFilter();
                        }}>
                        Clear
                    </Button>
                {/if}
            </div>
        </CardContent>
    </Card>

    <!-- Results -->
    <Card>
        <CardHeader>
            <CardTitle class="flex items-center gap-2">
                <FileText class="h-4 w-4" />
                Resources
                <Badge variant="secondary" data-testid="resource-count">{totalCount}</Badge>
            </CardTitle>
        </CardHeader>
        <CardContent>
            <div class="rounded-md border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead>Size</TableHead>
                            <TableHead>Lines</TableHead>
                            <TableHead>Last Updated</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {#if resourceItems.length === 0}
                            <TableRow>
                                <TableCell
                                    colspan={5}
                                    class="text-muted-foreground py-8 text-center">
                                    No resources found.
                                    {#if filterApplied}
                                        Try adjusting your filters.
                                    {/if}
                                </TableCell>
                            </TableRow>
                        {:else}
                            {#each resourceItems as resource (resource.id)}
                                <TableRow class="hover:bg-muted/50">
                                    <TableCell class="font-mono">
                                        <a
                                            href="/resources/{resource.id}"
                                            class="text-primary hover:underline">
                                            {resource.file_name}
                                        </a>
                                        {#if resource.file_label}
                                            <div class="text-muted-foreground mt-1 text-xs">
                                                {resource.file_label}
                                            </div>
                                        {/if}
                                    </TableCell>
                                    <TableCell>
                                        <Badge
                                            variant={getResourceTypeVariant(
                                                resource.resource_type
                                            )}>
                                            {formatResourceType(resource.resource_type)}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>{formatFileSize(resource.byte_size)}</TableCell>
                                    <TableCell>
                                        {resource.line_count
                                            ? resource.line_count.toLocaleString()
                                            : '—'}
                                    </TableCell>
                                    <TableCell class="text-muted-foreground">
                                        {formatDate(resource.updated_at)}
                                    </TableCell>
                                </TableRow>
                            {/each}
                        {/if}
                    </TableBody>
                </Table>
            </div>

            <!-- Pagination -->
            {#if totalPages > 1}
                <div class="mt-4 flex items-center justify-between">
                    <div class="text-muted-foreground text-sm">
                        Showing {(currentPage - 1) * pageSize + 1} - {Math.min(
                            currentPage * pageSize,
                            totalCount
                        )} of {totalCount} resources
                    </div>
                    <div class="flex gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            disabled={currentPage <= 1}
                            onclick={() => handlePageChange(currentPage - 1)}>
                            Previous
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            disabled={currentPage >= totalPages}
                            onclick={() => handlePageChange(currentPage + 1)}>
                            Next
                        </Button>
                    </div>
                </div>
            {/if}
        </CardContent>
    </Card>
</div>
