<script context="module" lang="ts">
    // Define the agent type for the list - updated to match SSR schema
    export interface AgentListItem {
        id: number;
        host_name: string;
        client_signature: string;
        custom_label: string | null;
        state: string;
        enabled: boolean;
        advanced_configuration: Record<string, unknown> | null;
        devices: string[] | null;
        agent_type: string | null;
        operating_system: string;
        created_at: string;
        updated_at: string;
        last_seen_at: string | null;
        last_ipaddress: string | null;
        projects: unknown[];
    }

    export interface AgentListData {
        items: AgentListItem[];
        page: number;
        page_size: number;
        total: number;
        search: string | null;
        state: string | null;
    }
</script>

<script lang="ts">
    import { goto } from '$app/navigation';
    import { page } from '$app/state';
    import Badge from '$lib/components/ui/badge/badge.svelte';
    import { Button } from '$lib/components/ui/button/index.js';
    import {
        Content as DialogContent,
        Root as DialogRoot,
    } from '$lib/components/ui/dialog/index.js';
    import * as Pagination from '$lib/components/ui/pagination/index.js';
    import TableBody from '$lib/components/ui/table/table-body.svelte';
    import TableCell from '$lib/components/ui/table/table-cell.svelte';
    import TableHead from '$lib/components/ui/table/table-head.svelte';
    import TableHeader from '$lib/components/ui/table/table-header.svelte';
    import TableRow from '$lib/components/ui/table/table-row.svelte';
    import Table from '$lib/components/ui/table/table.svelte';
    import { CogIcon } from '@lucide/svelte';
    import { z } from 'zod';
    import type { AgentDetails } from './AgentDetailsModal.svelte';
    import AgentDetailsModal from './AgentDetailsModal.svelte';

    // Props from SSR
    export let agents: AgentListData = undefined as unknown as AgentListData;

    // Admin role stub (replace with real session store)
    const isAdmin = true;

    // Local state for modal and search
    let selectedAgent: AgentDetails | null = null;
    let dialogOpen = false;
    let searchValue = agents.search || '';

    const agentFormSchema = z.object({
        gpuEnabled: z.boolean(),
        cpuEnabled: z.boolean(),
        updateInterval: z.number().min(1, 'Must be at least 1 second').max(3600),
    });

    // Handle search with URL navigation for SSR
    function handleSearch() {
        // Update URL to trigger SSR reload with search parameter
        const url = new URL(page.url);
        if (searchValue) {
            url.searchParams.set('search', searchValue);
        } else {
            url.searchParams.delete('search');
        }
        url.searchParams.set('page', '1'); // Reset to first page on search
        goto(url.toString());
    }

    // Handle pagination with URL navigation for SSR
    function handlePageChange(newPage: number) {
        const url = new URL(page.url);
        url.searchParams.set('page', newPage.toString());
        goto(url.toString());
    }

    function openAgentModal(agent: AgentListItem) {
        selectedAgent = agent as unknown as AgentDetails;
        dialogOpen = true;
    }

    function closeAgentModal() {
        dialogOpen = false;
        selectedAgent = null;
    }

    function statusBadge(state: string): {
        label: string;
        color: 'default' | 'secondary' | 'outline' | 'destructive';
    } {
        switch (state) {
            case 'active':
                return { label: 'Online', color: 'default' };
            case 'offline':
                return { label: 'Offline', color: 'secondary' };
            case 'stopped':
                return { label: 'Stopped', color: 'outline' };
            case 'error':
                return { label: 'Error', color: 'destructive' };
            default:
                return { label: state, color: 'secondary' };
        }
    }

    // Calculate pagination info
    $: totalPages = Math.ceil(agents.total / agents.page_size);
    $: currentPage = agents.page;
</script>

<div class="flex flex-col gap-4">
    <div class="flex items-center justify-between gap-2">
        <h2 class="text-xl font-semibold">Agents</h2>
        <input
            type="text"
            class="form-input w-64 rounded border px-2 py-1"
            placeholder="Search agents..."
            on:keydown={(e) => {
                if (e.key === 'Enter') {
                    handleSearch();
                }
            }}
            bind:value={searchValue} />
    </div>

    <Table>
        <TableHeader>
            <TableRow>
                <TableHead>Agent Name + OS</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Label</TableHead>
                <TableHead>Devices</TableHead>
                <TableHead>Last Seen</TableHead>
                <TableHead>IP Address</TableHead>
                {#if isAdmin}
                    <TableHead></TableHead>
                {/if}
            </TableRow>
        </TableHeader>
        <TableBody>
            {#each agents.items as agent (agent.id)}
                <TableRow>
                    <TableCell>
                        <div class="flex flex-col">
                            <span class="font-medium">{agent.host_name}</span>
                            <span class="text-muted-foreground text-xs"
                                >{agent.operating_system}</span>
                        </div>
                    </TableCell>
                    <TableCell>
                        <Badge variant={statusBadge(agent.state).color}
                            >{statusBadge(agent.state).label}</Badge>
                    </TableCell>
                    <TableCell>{agent.custom_label ?? '—'}</TableCell>
                    <TableCell>
                        {#if agent.devices && agent.devices.length > 0}
                            <span class="text-xs">{agent.devices.join(', ')}</span>
                        {:else}
                            —
                        {/if}
                    </TableCell>
                    <TableCell>
                        {#if agent.last_seen_at}
                            <span class="text-xs"
                                >{new Date(agent.last_seen_at).toLocaleDateString()}</span>
                        {:else}
                            —
                        {/if}
                    </TableCell>
                    <TableCell>{agent.last_ipaddress ?? '—'}</TableCell>
                    {#if isAdmin}
                        <TableCell>
                            <Button
                                variant="ghost"
                                size="icon"
                                aria-label="Agent Details"
                                onclick={() => openAgentModal(agent)}>
                                <CogIcon class="size-4" />
                            </Button>
                        </TableCell>
                    {/if}
                </TableRow>
            {/each}
        </TableBody>
    </Table>

    {#if agents.total > agents.page_size}
        <div class="mt-4 flex justify-center">
            <Pagination.Root
                count={agents.total}
                perPage={agents.page_size}
                page={currentPage}
                onPageChange={handlePageChange}>
                {#snippet children({ pages })}
                    <Pagination.Content>
                        <Pagination.Item>
                            <Pagination.PrevButton />
                        </Pagination.Item>
                        {#each pages as pageItem (pageItem.key)}
                            {#if pageItem.type === 'ellipsis'}
                                <Pagination.Item>
                                    <Pagination.Ellipsis />
                                </Pagination.Item>
                            {:else}
                                <Pagination.Item>
                                    <Pagination.Link
                                        page={pageItem}
                                        isActive={currentPage === pageItem.value}>
                                        {pageItem.value}
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
</div>

<DialogRoot bind:open={dialogOpen}>
    <DialogContent role="dialog" class="w-full max-w-lg">
        <AgentDetailsModal agent={selectedAgent} on:close={() => (dialogOpen = false)} />
    </DialogContent>
</DialogRoot>
