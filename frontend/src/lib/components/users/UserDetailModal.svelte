<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import axios from 'axios';
    import { Dialog, DialogContent, DialogHeader, DialogTitle } from '$lib/components/ui/dialog';
    import { Button } from '$lib/components/ui/button';
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';
    import { Badge } from '$lib/components/ui/badge';
    import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
    import type { User, UserUpdate } from '$lib/types/user';

    export let user: User = undefined as unknown as User;
    export let onClose: () => void = () => {};
    export let onUserUpdated: () => void = () => {};

    const dispatch = createEventDispatcher();

    let editing = false;
    let formData: UserUpdate = {
        email: user.email,
        name: user.name,
        role: user.role || undefined, // Convert null to undefined for Select component
    };
    let loading = false;
    let error = '';

    // Local role variable for Select component binding
    let selectedRole: string | undefined = user.role || undefined;

    async function handleSubmit() {
        loading = true;
        error = '';

        try {
            // Update formData with selectedRole before submission
            formData.role = selectedRole;
            await axios.patch(`/api/v1/web/users/${user.id}`, formData);
            editing = false;
            onUserUpdated();
        } catch (e: unknown) {
            error =
                (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
                'Failed to update user';
        } finally {
            loading = false;
        }
    }

    function startEditing() {
        editing = true;
        formData = {
            email: user.email,
            name: user.name,
            role: user.role,
        };
        selectedRole = user.role || undefined;
    }

    function cancelEditing() {
        editing = false;
        error = '';
    }

    function formatDate(dateStr: string): string {
        return new Date(dateStr).toLocaleString();
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
</script>

<Dialog open={true} onOpenChange={onClose}>
    <DialogContent class="sm:max-w-md" data-testid="user-detail-modal">
        <DialogHeader>
            <DialogTitle>User Details</DialogTitle>
        </DialogHeader>

        {#if editing}
            <form on:submit|preventDefault={handleSubmit} class="space-y-4">
                <div class="space-y-2">
                    <Label for="edit-name">Name</Label>
                    <Input
                        id="edit-name"
                        type="text"
                        bind:value={formData.name}
                        required
                        data-testid="edit-name-input" />
                </div>

                <div class="space-y-2">
                    <Label for="edit-email">Email</Label>
                    <Input
                        id="edit-email"
                        type="email"
                        bind:value={formData.email}
                        required
                        data-testid="edit-email-input" />
                </div>

                <div class="space-y-2">
                    <Label for="edit-role">Role</Label>
                    <Select type="single" bind:value={selectedRole}>
                        <SelectTrigger data-testid="edit-role-select">
                            {selectedRole || 'Select role'}
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="analyst">Analyst</SelectItem>
                            <SelectItem value="operator">Operator</SelectItem>
                            <SelectItem value="admin">Admin</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                {#if error}
                    <div class="text-sm text-red-600" data-testid="error-message">{error}</div>
                {/if}

                <div class="flex justify-end gap-2">
                    <Button
                        type="button"
                        variant="outline"
                        onclick={cancelEditing}
                        data-testid="cancel-edit-button">
                        Cancel
                    </Button>
                    <Button type="submit" disabled={loading} data-testid="save-button">
                        {loading ? 'Saving...' : 'Save Changes'}
                    </Button>
                </div>
            </form>
        {:else}
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <Label class="text-sm font-medium text-gray-500">Name</Label>
                        <p class="text-sm">{user.name}</p>
                    </div>
                    <div>
                        <Label class="text-sm font-medium text-gray-500">Email</Label>
                        <p class="text-sm">{user.email}</p>
                    </div>
                </div>

                <div class="grid grid-cols-1 gap-4">
                    <div>
                        <Label class="text-sm font-medium text-gray-500">Active</Label>
                        <div class="mt-1">
                            <Badge
                                class={user.is_active
                                    ? 'border-green-200 bg-green-100 text-green-800'
                                    : 'border-red-200 bg-red-100 text-red-800'}>
                                {user.is_active ? 'Yes' : 'No'}
                            </Badge>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <Label class="text-sm font-medium text-gray-500">Role</Label>
                        <div class="mt-1">
                            <Badge class={getRoleBadgeColor(user.role)}>
                                {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                            </Badge>
                        </div>
                    </div>
                    <div>
                        <Label class="text-sm font-medium text-gray-500">Superuser</Label>
                        <div class="mt-1">
                            <Badge
                                class={user.is_superuser
                                    ? 'border-purple-200 bg-purple-100 text-purple-800'
                                    : 'border-gray-200 bg-gray-100 text-gray-800'}>
                                {user.is_superuser ? 'Yes' : 'No'}
                            </Badge>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 gap-4">
                    <div>
                        <Label class="text-sm font-medium text-gray-500">Created</Label>
                        <p class="text-sm">{formatDate(user.created_at)}</p>
                    </div>
                    <div>
                        <Label class="text-sm font-medium text-gray-500">Last Updated</Label>
                        <p class="text-sm">{formatDate(user.updated_at)}</p>
                    </div>
                </div>

                <div class="flex justify-end gap-2">
                    <Button variant="outline" onclick={onClose} data-testid="close-button">
                        Close
                    </Button>
                    <Button onclick={startEditing} data-testid="edit-button">Edit User</Button>
                </div>
            </div>
        {/if}
    </DialogContent>
</Dialog>
