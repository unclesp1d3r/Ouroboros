<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import axios from 'axios';
    import { Dialog, DialogContent, DialogHeader, DialogTitle } from '$lib/components/ui/dialog';
    import { Button } from '$lib/components/ui/button';
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';
    import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
    import type { UserCreate } from '$lib/types/user';

    export let onClose: () => void = () => {};
    export let onUserCreated: () => void = () => {};

    const dispatch = createEventDispatcher();

    let formData: UserCreate = {
        email: '',
        name: '',
        password: '',
    };
    let role = 'analyst';
    let loading = false;
    let error = '';

    async function handleSubmit() {
        loading = true;
        error = '';

        try {
            await axios.post('/api/v1/web/users', {
                ...formData,
                role,
            });
            onUserCreated();
        } catch (e: unknown) {
            error =
                (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
                'Failed to create user';
        } finally {
            loading = false;
        }
    }

    function handleKeydown(event: KeyboardEvent) {
        if (event.key === 'Escape') {
            onClose();
        }
    }
</script>

<Dialog open={true} onOpenChange={onClose}>
    <DialogContent class="sm:max-w-md" data-testid="user-create-modal">
        <DialogHeader>
            <DialogTitle>Create New User</DialogTitle>
        </DialogHeader>

        <form on:submit|preventDefault={handleSubmit} class="space-y-4">
            <div class="space-y-2">
                <Label for="name">Name</Label>
                <Input
                    id="name"
                    type="text"
                    bind:value={formData.name}
                    required
                    data-testid="name-input" />
            </div>

            <div class="space-y-2">
                <Label for="email">Email</Label>
                <Input
                    id="email"
                    type="email"
                    bind:value={formData.email}
                    required
                    data-testid="email-input" />
            </div>

            <div class="space-y-2">
                <Label for="password">Password</Label>
                <Input
                    id="password"
                    type="password"
                    bind:value={formData.password}
                    required
                    data-testid="password-input" />
            </div>

            <div class="space-y-2">
                <Label for="role">Role</Label>
                <Select type="single" bind:value={role}>
                    <SelectTrigger data-testid="role-select">
                        {role || 'Select role'}
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
                    onclick={onClose}
                    data-testid="cancel-button">
                    Cancel
                </Button>
                <Button type="submit" disabled={loading} data-testid="submit-button">
                    {loading ? 'Creating...' : 'Create User'}
                </Button>
            </div>
        </form>
    </DialogContent>
</Dialog>
