<script lang="ts">
    import { superForm } from 'sveltekit-superforms';
    import { zod4Client } from 'sveltekit-superforms/adapters';
    import { Dialog, DialogContent, DialogHeader, DialogTitle } from '$lib/components/ui/dialog';
    import { Button } from '$lib/components/ui/button';
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';
    import { Badge } from '$lib/components/ui/badge';
    import { Switch } from '$lib/components/ui/switch';
    import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { goto } from '$app/navigation';
    import { userUpdateSchema } from './schema';

    let { data } = $props();

    let editing = $state(false);

    const { form, errors, enhance, submitting, message } = superForm(data.form, {
        validators: zod4Client(userUpdateSchema),
        onResult: ({ result }) => {
            if (result.type === 'redirect') {
                // Close modal and navigate back to users
                handleClose();
            }
        },
        onUpdated: ({ form: updatedForm }) => {
            // Handle successful form submission (including test environment)
            if (updatedForm.valid && !updatedForm.message) {
                // Form was successfully submitted without errors
                editing = false;
                goto('/users', { invalidateAll: true });
            }
        },
    });

    function handleClose() {
        goto('/users');
    }

    function startEditing() {
        editing = true;
    }

    function cancelEditing() {
        editing = false;
        // Reset form to original values
        $form.name = data.user.name;
        $form.email = data.user.email;
        $form.role = data.user.role as 'analyst' | 'operator' | 'admin';
        $form.is_active = data.user.is_active;
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

    function handleKeydown(event: KeyboardEvent) {
        if (event.key === 'Escape') {
            handleClose();
        }
    }
</script>

<svelte:window onkeydown={handleKeydown} />

<svelte:head>
    <title>User Details - {data.user.name} - Ouroboros</title>
</svelte:head>

<Dialog open={true} onOpenChange={handleClose}>
    <DialogContent class="sm:max-w-md" data-testid="user-detail-modal">
        <DialogHeader>
            <DialogTitle>User Details</DialogTitle>
        </DialogHeader>

        {#if editing}
            {#if $message}
                <Alert variant="destructive">
                    <AlertDescription data-testid="error-message">{$message}</AlertDescription>
                </Alert>
            {/if}

            <form method="POST" use:enhance class="space-y-4">
                <div class="space-y-2">
                    <Label for="edit-name">Name <span class="text-red-500">*</span></Label>
                    <Input
                        id="edit-name"
                        name="name"
                        type="text"
                        bind:value={$form.name}
                        placeholder="Enter user name"
                        required
                        data-testid="edit-name-input"
                        class={$errors.name ? 'border-red-500' : ''} />
                    {#if $errors.name}
                        <p class="text-sm text-red-500" data-testid="name-error">
                            {$errors.name}
                        </p>
                    {/if}
                </div>

                <div class="space-y-2">
                    <Label for="edit-email">Email <span class="text-red-500">*</span></Label>
                    <Input
                        id="edit-email"
                        name="email"
                        type="email"
                        bind:value={$form.email}
                        placeholder="Enter email address"
                        required
                        data-testid="edit-email-input"
                        class={$errors.email ? 'border-red-500' : ''} />
                    {#if $errors.email}
                        <p class="text-sm text-red-500" data-testid="email-error">
                            {$errors.email}
                        </p>
                    {/if}
                </div>

                <div class="space-y-2">
                    <Label for="edit-role">Role <span class="text-red-500">*</span></Label>
                    <Select type="single" bind:value={$form.role}>
                        <SelectTrigger
                            data-testid="edit-role-select"
                            class={$errors.role ? 'border-red-500' : ''}>
                            {$form.role || 'Select role'}
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="analyst">Analyst</SelectItem>
                            <SelectItem value="operator">Operator</SelectItem>
                            <SelectItem value="admin">Admin</SelectItem>
                        </SelectContent>
                    </Select>
                    {#if $errors.role}
                        <p class="text-sm text-red-500" data-testid="role-error">
                            {$errors.role}
                        </p>
                    {/if}
                </div>

                <div class="space-y-2">
                    <div class="flex items-center space-x-2">
                        <Switch
                            id="edit-active"
                            name="is_active"
                            bind:checked={$form.is_active}
                            data-testid="edit-active-switch" />
                        <Label for="edit-active">Active</Label>
                    </div>
                    {#if $errors.is_active}
                        <p class="text-sm text-red-500" data-testid="active-error">
                            {$errors.is_active}
                        </p>
                    {/if}
                </div>

                <div class="flex justify-end gap-2">
                    <Button
                        type="button"
                        variant="outline"
                        onclick={cancelEditing}
                        disabled={$submitting}
                        data-testid="cancel-edit-button">
                        Cancel
                    </Button>
                    <Button type="submit" disabled={$submitting} data-testid="save-button">
                        {$submitting ? 'Saving...' : 'Save Changes'}
                    </Button>
                </div>
            </form>
        {:else}
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <Label class="text-sm font-medium text-gray-500">Name</Label>
                        <p class="text-sm">{data.user.name}</p>
                    </div>
                    <div>
                        <Label class="text-sm font-medium text-gray-500">Email</Label>
                        <p class="text-sm">{data.user.email}</p>
                    </div>
                </div>

                <div class="grid grid-cols-1 gap-4">
                    <div>
                        <Label class="text-sm font-medium text-gray-500">Active</Label>
                        <div class="mt-1">
                            <Badge
                                class={data.user.is_active
                                    ? 'border-green-200 bg-green-100 text-green-800'
                                    : 'border-red-200 bg-red-100 text-red-800'}>
                                {data.user.is_active ? 'Yes' : 'No'}
                            </Badge>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <Label class="text-sm font-medium text-gray-500">Role</Label>
                        <div class="mt-1">
                            <Badge class={getRoleBadgeColor(data.user.role)}>
                                {data.user.role.charAt(0).toUpperCase() + data.user.role.slice(1)}
                            </Badge>
                        </div>
                    </div>
                    <div>
                        <Label class="text-sm font-medium text-gray-500">Superuser</Label>
                        <div class="mt-1">
                            <Badge
                                class={data.user.is_superuser
                                    ? 'border-purple-200 bg-purple-100 text-purple-800'
                                    : 'border-gray-200 bg-gray-100 text-gray-800'}>
                                {data.user.is_superuser ? 'Yes' : 'No'}
                            </Badge>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 gap-4">
                    <div>
                        <Label class="text-sm font-medium text-gray-500">Created</Label>
                        <p class="text-sm">{formatDate(data.user.created_at)}</p>
                    </div>
                    <div>
                        <Label class="text-sm font-medium text-gray-500">Last Updated</Label>
                        <p class="text-sm">{formatDate(data.user.updated_at)}</p>
                    </div>
                </div>

                <div class="flex justify-end gap-2">
                    <Button variant="outline" onclick={handleClose} data-testid="close-button">
                        Close
                    </Button>
                    <Button onclick={startEditing} data-testid="edit-button">Edit User</Button>
                </div>
            </div>
        {/if}
    </DialogContent>
</Dialog>
