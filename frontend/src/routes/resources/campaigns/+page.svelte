<script lang="ts">
    import { Card, CardHeader, CardTitle, CardContent } from '$lib/components/ui/card';
    import {
        Accordion,
        AccordionItem,
        AccordionTrigger,
        AccordionContent,
    } from '$lib/components/ui/accordion';
    import { Progress } from '$lib/components/ui/progress';
    import { Badge } from '$lib/components/ui/badge';
    import { Tooltip, TooltipTrigger, TooltipContent } from '$lib/components/ui/tooltip';
    import {
        Table,
        TableHead,
        TableHeader,
        TableBody,
        TableRow,
        TableCell,
    } from '$lib/components/ui/table';
    import { Button } from '$lib/components/ui/button';
    import { Pagination } from '$lib/components/ui/pagination';
    import {
        DropdownMenu,
        DropdownMenuTrigger,
        DropdownMenuContent,
        DropdownMenuItem,
    } from '$lib/components/ui/dropdown-menu';
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';

    import CrackableUploadModal from '$lib/components/campaigns/CrackableUploadModal.svelte';
    import type { CampaignWithUIData } from './+page.server';

    interface PageData {
        campaigns: CampaignWithUIData[];
        pagination: {
            total: number;
            page: number;
            per_page: number;
            pages: number;
        };
        searchParams: {
            name?: string;
        };
    }

    let { data }: { data: PageData } = $props();

    // Extract data from SSR load function
    const campaigns = $derived(data.campaigns);
    const pagination = $derived(data.pagination);
    const searchParams = $derived(data.searchParams);

    // Modal state
    let showUploadModal = $state(false);

    function stateBadge(state: string) {
        switch (state) {
            case 'active':
                return { color: 'bg-purple-600', label: 'Running' }; // Test expects "Running"
            case 'completed':
                return { color: 'bg-green-600', label: 'Completed' };
            case 'error':
                return { color: 'bg-red-600', label: 'Error' };
            case 'paused':
                return { color: 'bg-gray-400', label: 'Paused' };
            case 'draft':
                return { color: 'bg-blue-400', label: 'Draft' };
            case 'archived':
                return { color: 'bg-gray-300', label: 'Archived' };
            default:
                return { color: 'bg-gray-200', label: state };
        }
    }

    // Handle pagination page changes
    function handlePageChange(newPage: number) {
        const url = new URL($page.url);
        url.searchParams.set('page', newPage.toString());
        goto(url.toString());
    }

    // Modal handlers
    function openCreateModal() {
        goto('/campaigns/new');
    }

    function openUploadModal() {
        showUploadModal = true;
    }

    function openEditModal(campaign: CampaignWithUIData) {
        goto(`/campaigns/${campaign.id}/edit`);
    }

    function openDeleteModal(campaign: CampaignWithUIData) {
        goto(`/campaigns/${campaign.id}/delete`);
    }

    function handleUploadSuccess(event: { uploadId: number }) {
        showUploadModal = false;
        // TODO: Navigate to upload status page or refresh campaigns
        console.log('Upload successful:', event.uploadId);
        // Refresh the page to get updated data
        goto($page.url.toString(), { invalidateAll: true });
    }

    function closeUploadModal() {
        showUploadModal = false;
    }

    // Convert attack complexity score to visual representation
    function getComplexityDots(complexityScore: number | null): number {
        if (complexityScore === null) return 1;
        // Map complexity score (1-10) to dots (1-5)
        return Math.min(Math.max(Math.ceil(complexityScore / 2), 1), 5);
    }
</script>

<svelte:head>
    <title>Campaigns - Ouroboros</title>
</svelte:head>

<Card class="mx-auto mt-8 w-full max-w-5xl">
    <CardHeader>
        <div class="flex items-center justify-between">
            <CardTitle data-testid="campaigns-title">Campaigns</CardTitle>
            <div class="flex gap-2">
                <Button
                    variant="outline"
                    data-testid="upload-campaign-button"
                    onclick={openUploadModal}>
                    Upload & Crack
                </Button>
                <Button data-testid="create-campaign-button" onclick={openCreateModal}>
                    Create Campaign
                </Button>
            </div>
        </div>
    </CardHeader>
    <CardContent>
        {#if campaigns.length === 0}
            <div class="py-8 text-center">
                No campaigns found. <Button
                    data-testid="empty-state-create-button"
                    onclick={openCreateModal}>Create Campaign</Button>
            </div>
        {:else}
            <Accordion type="multiple" class="w-full">
                {#each campaigns as campaign (campaign.id)}
                    <AccordionItem value={String(campaign.id)} class="border-b">
                        <AccordionTrigger class="flex w-full items-center justify-between py-4">
                            <div class="flex w-full items-center gap-4">
                                <div
                                    class="flex-1 cursor-pointer truncate text-left text-lg font-semibold transition-colors hover:text-blue-600"
                                    role="button"
                                    tabindex="0"
                                    onclick={() => goto(`/campaigns/${campaign.id}`)}
                                    onkeydown={(e) =>
                                        e.key === 'Enter' && goto(`/campaigns/${campaign.id}`)}
                                    data-testid="campaign-link-{campaign.id}">
                                    {campaign.name}
                                </div>
                                <div class="max-w-xs flex-1">
                                    <Progress value={campaign.progress} class="h-2" />
                                </div>
                                <Badge class={stateBadge(campaign.state).color}
                                    >{stateBadge(campaign.state).label}</Badge>
                                <span class="text-sm text-gray-500">{campaign.summary}</span>
                                <DropdownMenu>
                                    <DropdownMenuTrigger
                                        class="hover:bg-accent hover:text-accent-foreground focus-visible:ring-ring inline-flex h-9 w-9 items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:ring-1 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50"
                                        data-testid="campaign-menu-{campaign.id}">
                                        <svg
                                            xmlns="http://www.w3.org/2000/svg"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                            stroke-width="1.5"
                                            stroke="currentColor"
                                            class="h-5 w-5">
                                            <path
                                                stroke-linecap="round"
                                                stroke-linejoin="round"
                                                d="M6.75 12a.75.75 0 110-1.5.75.75 0 010 1.5zm5.25 0a.75.75 0 110-1.5.75.75 0 010 1.5zm5.25 0a.75.75 0 110-1.5.75.75 0 010 1.5z" />
                                        </svg>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent>
                                        <DropdownMenuItem onclick={() => openEditModal(campaign)}>
                                            Edit Campaign
                                        </DropdownMenuItem>
                                        <DropdownMenuItem
                                            onclick={() => openDeleteModal(campaign)}
                                            class="text-red-600">
                                            Delete Campaign
                                        </DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </div>
                        </AccordionTrigger>
                        <AccordionContent class="bg-muted/50">
                            <Table class="mt-2 w-full">
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Attack</TableHead>
                                        <TableHead>Type</TableHead>
                                        <TableHead>Length</TableHead>
                                        <TableHead>Settings</TableHead>
                                        <TableHead>Keyspace</TableHead>
                                        <TableHead>Complexity</TableHead>
                                        <TableHead></TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {#each campaign.attacks as attack (attack.id)}
                                        <TableRow>
                                            <TableCell>{attack.name}</TableCell>
                                            <TableCell>{attack.type_label}</TableCell>
                                            <TableCell>{attack.length || 'N/A'}</TableCell>
                                            <TableCell>
                                                <Tooltip>
                                                    <TooltipTrigger
                                                        >{attack.settings_summary}</TooltipTrigger>
                                                    <TooltipContent
                                                        >{attack.settings_summary}</TooltipContent>
                                                </Tooltip>
                                            </TableCell>
                                            <TableCell>
                                                {attack.keyspace?.toLocaleString() || 'Unknown'}
                                            </TableCell>
                                            <TableCell>
                                                <div class="flex space-x-1">
                                                    {#each Array(5) as _, i (i)}
                                                        <span
                                                            class={i <
                                                            getComplexityDots(
                                                                attack.complexity_score
                                                            )
                                                                ? 'h-2 w-2 rounded-full bg-gray-600'
                                                                : 'h-2 w-2 rounded-full bg-gray-200'}
                                                        ></span>
                                                    {/each}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <DropdownMenu>
                                                    <DropdownMenuTrigger
                                                        class="hover:bg-accent hover:text-accent-foreground focus-visible:ring-ring inline-flex h-9 w-9 items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:ring-1 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50">
                                                        <svg
                                                            xmlns="http://www.w3.org/2000/svg"
                                                            fill="none"
                                                            viewBox="0 0 24 24"
                                                            stroke-width="1.5"
                                                            stroke="currentColor"
                                                            class="h-5 w-5">
                                                            <path
                                                                stroke-linecap="round"
                                                                stroke-linejoin="round"
                                                                d="M6.75 12a.75.75 0 110-1.5.75.75 0 010 1.5zm5.25 0a.75.75 0 110-1.5.75.75 0 010 1.5zm5.25 0a.75.75 0 110-1.5.75.75 0 010 1.5z" />
                                                        </svg>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent>
                                                        <DropdownMenuItem>Edit</DropdownMenuItem>
                                                        <DropdownMenuItem
                                                            >Duplicate</DropdownMenuItem>
                                                        <DropdownMenuItem>Move Up</DropdownMenuItem>
                                                        <DropdownMenuItem
                                                            >Move Down</DropdownMenuItem>
                                                        <DropdownMenuItem class="text-red-600"
                                                            >Remove</DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </TableCell>
                                        </TableRow>
                                    {/each}
                                    {#if campaign.attacks.length === 0}
                                        <TableRow>
                                            <TableCell
                                                colspan={7}
                                                class="py-4 text-center text-gray-500">
                                                No attacks configured for this campaign
                                            </TableCell>
                                        </TableRow>
                                    {/if}
                                </TableBody>
                            </Table>
                            <div class="mt-4 flex items-center justify-between">
                                <Button variant="outline">+ Add Attack…</Button>
                                <div class="flex gap-2">
                                    <Button
                                        variant="outline"
                                        class="flex items-center gap-1 text-red-600"
                                        ><svg
                                            xmlns="http://www.w3.org/2000/svg"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                            stroke-width="1.5"
                                            stroke="currentColor"
                                            class="h-5 w-5"
                                            ><path
                                                stroke-linecap="round"
                                                stroke-linejoin="round"
                                                d="M19.5 12h-15" /></svg
                                        >All</Button>
                                    <Button variant="outline">Reset to Default</Button>
                                    <Button variant="outline">Save/Load</Button>
                                    <Button variant="outline">Sort by Duration</Button>
                                </div>
                            </div>
                        </AccordionContent>
                    </AccordionItem>
                {/each}
            </Accordion>
            {#if pagination.pages > 1}
                <div class="mt-4 flex justify-center">
                    <Pagination
                        count={pagination.pages}
                        page={pagination.page}
                        onPageChange={handlePageChange} />
                </div>
            {/if}
        {/if}
    </CardContent>
</Card>

<!-- Modals -->
<CrackableUploadModal
    bind:open={showUploadModal}
    projectId={1}
    onclose={closeUploadModal}
    onsuccess={handleUploadSuccess} />
