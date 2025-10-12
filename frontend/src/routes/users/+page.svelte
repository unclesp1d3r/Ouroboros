<script lang="ts">
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
    import {
        Table,
        TableBody,
        TableCell,
        TableHead,
        TableHeader,
        TableRow,
    } from '$lib/components/ui/table';

    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { usersStore } from '$lib/stores/users.svelte';
    import type { User } from './+page.server';

    interface PageData {
        users: User[];
        pagination: {
            total: number;
            page: number;
            page_size: number;
            pages: number;
        };
        searchParams: {
            search?: string;
        };
    }

    let { data }: { data: PageData } = $props();

    // Hydrate store with SSR data
    $effect(() => {
        if (data.users) {
            // Transform server response to match store expected format
            const transformedData = {
                items: data.users,
                total: data.pagination.total,
                page: data.pagination.page,
                page_size: data.pagination.page_size,
                search: data.searchParams.search || null,
            };
            usersStore.hydrateUsers(transformedData);
        }
    });

    // Use SSR data directly for initial render, store for reactive updates
    const users = $derived(data.users);
    const pagination = $derived(data.pagination);
    const searchParams = $derived(data.searchParams);

    // Local state for search input - initialized from SSR data
    let searchInput = $state(data.searchParams.search || '');

    // Modal state - only needed for detail modal now
    // Delete modal is now handled by dedicated route

    function handleSearch() {
        const url = new URL($page.url);
        if (searchInput.trim()) {
            url.searchParams.set('search', searchInput.trim());
        } else {
            url.searchParams.delete('search');
        }
        url.searchParams.set('page', '1'); // Reset to first page
        goto(url.toString());
    }

    function handleKeyDown(event: KeyboardEvent) {
        if (event.key === 'Enter') {
            handleSearch();
        }
    }

    function handlePageChange(newPage: number) {
        const url = new URL($page.url);
        url.searchParams.set('page', newPage.toString());
        goto(url.toString());
    }

    function openCreateModal() {
        goto('/users/new');
    }

    function openDetailModal(user: User) {
        goto(`/users/${user.id}`);
    }

    function openDeleteModal(user: User) {
        goto(`/users/${user.id}/delete`);
    }

    function formatDate(dateStr: string): string {
        return new Date(dateStr).toLocaleDateString();
    }

    function getRoleBadgeColor(role: string): string {
        switch (role.toLowerCase()) {
            case 'admin':
                return 'bg-red-100 text-red-800 border-red-200';
            case 'analyst':
                return 'bg-blue-100 text-blue-800 border-blue-200';
            case 'operator':
                return 'bg-green-100 text-green-800 border-green-200';
            default:
                return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    }

    // Pagination calculations
    const totalPages = $derived(pagination.pages);
    const startIndex = $derived((pagination.page - 1) * pagination.page_size + 1);
    const endIndex = $derived(Math.min(pagination.page * pagination.page_size, pagination.total));
</script>

<svelte:head>
    <title>Users - Ouroboros</title>
</svelte:head>

<div class="container mx-auto p-6">
    <Card>
        <CardHeader>
            <div class="flex items-center justify-between">
                <CardTitle data-testid="users-title">User Management</CardTitle>
                <Button data-testid="create-user-button" onclick={openCreateModal}>
                    Create User
                </Button>
            </div>
        </CardHeader>
        <CardContent>
            <!-- Search -->
            <div class="mb-6 flex gap-2">
                <Input
                    type="text"
                    placeholder="Search users by name or email..."
                    bind:value={searchInput}
                    onkeydown={handleKeyDown}
                    class="max-w-md"
                    data-testid="search-input" />
                <Button onclick={handleSearch} data-testid="search-button">Search</Button>
            </div>

            {#if users.length === 0}
                <div class="py-8 text-center" data-testid="empty-state">
                    {#if searchParams.search}
                        No users found matching "{searchParams.search}".
                    {:else}
                        No users found. <Button
                            data-testid="empty-state-create-button"
                            onclick={openCreateModal}>Create User</Button>
                    {/if}
                </div>
            {:else}
                <!-- Users Table -->
                <div class="rounded-md border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Name</TableHead>
                                <TableHead>Email</TableHead>
                                <TableHead>Active</TableHead>
                                <TableHead>Role</TableHead>
                                <TableHead>Created</TableHead>
                                <TableHead class="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {#each users as user (user.id)}
                                <TableRow data-testid="user-row-{user.id}">
                                    <TableCell class="font-medium">{user.name}</TableCell>
                                    <TableCell>{user.email}</TableCell>
                                    <TableCell>
                                        <Badge
                                            class={user.is_active
                                                ? 'border-green-200 bg-green-100 text-green-800'
                                                : 'border-red-200 bg-red-100 text-red-800'}>
                                            {user.is_active ? 'Yes' : 'No'}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Badge class={getRoleBadgeColor(user.role)}>
                                            {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>{formatDate(user.created_at)}</TableCell>
                                    <TableCell class="text-right">
                                        <DropdownMenu>
                                            <DropdownMenuTrigger>
                                                <Button
                                                    size="sm"
                                                    variant="ghost"
                                                    data-testid="user-menu-{user.id}">
                                                    <svg
                                                        xmlns="http://www.w3.org/2000/svg"
                                                        width="16"
                                                        height="16"
                                                        viewBox="0 0 24 24"
                                                        fill="none"
                                                        stroke="currentColor"
                                                        stroke-width="2"
                                                        stroke-linecap="round"
                                                        stroke-linejoin="round">
                                                        <circle cx="12" cy="12" r="1"></circle>
                                                        <circle cx="12" cy="5" r="1"></circle>
                                                        <circle cx="12" cy="19" r="1"></circle>
                                                    </svg>
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent>
                                                <DropdownMenuItem
                                                    onclick={() => openDetailModal(user)}
                                                    data-testid="view-user-{user.id}">
                                                    View Details
                                                </DropdownMenuItem>
                                                <DropdownMenuItem
                                                    onclick={() => openDeleteModal(user)}
                                                    data-testid="delete-user-{user.id}"
                                                    class="text-red-600">
                                                    Deactivate
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </TableCell>
                                </TableRow>
                            {/each}
                        </TableBody>
                    </Table>
                </div>

                <!-- Pagination -->
                <div class="mt-6 flex items-center justify-between">
                    <div class="text-sm text-gray-700" data-testid="pagination-info">
                        Showing {startIndex}-{endIndex} of {pagination.total} users
                    </div>
                    <div class="flex gap-2">
                        <Button
                            size="sm"
                            variant="outline"
                            onclick={() => handlePageChange(1)}
                            disabled={pagination.page === 1}
                            data-testid="first-page-button">
                            First
                        </Button>
                        <Button
                            size="sm"
                            variant="outline"
                            onclick={() => handlePageChange(pagination.page - 1)}
                            disabled={pagination.page === 1}
                            data-testid="prev-page-button">
                            Previous
                        </Button>
                        <span class="flex items-center px-3 text-sm">
                            Page {pagination.page} of {totalPages}
                        </span>
                        <Button
                            size="sm"
                            variant="outline"
                            onclick={() => handlePageChange(pagination.page + 1)}
                            disabled={pagination.page >= totalPages}
                            data-testid="next-page-button">
                            Next
                        </Button>
                        <Button
                            size="sm"
                            variant="outline"
                            onclick={() => handlePageChange(totalPages)}
                            disabled={pagination.page >= totalPages}
                            data-testid="last-page-button">
                            Last
                        </Button>
                    </div>
                </div>
            {/if}
        </CardContent>
    </Card>
</div>

<!-- Modals are now handled by dedicated routes -->
