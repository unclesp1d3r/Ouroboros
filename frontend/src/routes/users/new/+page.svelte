<script lang="ts">
    import { superForm } from 'sveltekit-superforms';
    import { zod4Client } from 'sveltekit-superforms/adapters';
    import { Dialog, DialogContent, DialogHeader, DialogTitle } from '$lib/components/ui/dialog';
    import { Button } from '$lib/components/ui/button';
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';
    import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { goto } from '$app/navigation';
    import { userCreateSchema } from './schema';

    let { data } = $props();

    const { form, errors, enhance, submitting, message } = superForm(data.form, {
        validators: zod4Client(userCreateSchema),
        onResult: ({ result }) => {
            if (result.type === 'redirect') {
                // Close modal and navigate back to users
                handleClose();
            } else if (result.type === 'success') {
                // In test environment, success result means user was created
                // Close modal first, then navigate
                open = false;
                setTimeout(() => goto('/users'), 100);
            }
        },
    });

    // Modal state - open by default when this route is accessed
    let open = $state(true);

    function handleClose() {
        open = false;
        // Navigate back to users list
        goto('/users');
    }

    function handleKeydown(event: KeyboardEvent) {
        if (event.key === 'Escape') {
            handleClose();
        }
    }
</script>

<svelte:window onkeydown={handleKeydown} />

<svelte:head>
    <title>Create User - Ouroboros</title>
</svelte:head>

<Dialog bind:open onOpenChange={handleClose}>
    <DialogContent class="sm:max-w-md" data-testid="user-create-modal">
        <DialogHeader>
            <DialogTitle>Create New User</DialogTitle>
        </DialogHeader>

        {#if $message}
            <Alert variant="destructive">
                <AlertDescription data-testid="error-message">{$message}</AlertDescription>
            </Alert>
        {/if}

        <form method="POST" use:enhance class="space-y-4">
            <div class="space-y-2">
                <Label for="name">Name <span class="text-red-500">*</span></Label>
                <Input
                    id="name"
                    name="name"
                    type="text"
                    bind:value={$form.name}
                    placeholder="Full name"
                    required
                    data-testid="name-input"
                    class={$errors.name ? 'border-red-500' : ''} />
                {#if $errors.name}
                    <p class="text-sm text-red-500" data-testid="name-error">
                        {$errors.name}
                    </p>
                {/if}
            </div>

            <div class="space-y-2">
                <Label for="email">Email <span class="text-red-500">*</span></Label>
                <Input
                    id="email"
                    name="email"
                    type="email"
                    bind:value={$form.email}
                    placeholder="user@example.com"
                    required
                    data-testid="email-input"
                    class={$errors.email ? 'border-red-500' : ''} />
                {#if $errors.email}
                    <p class="text-sm text-red-500" data-testid="email-error">
                        {$errors.email}
                    </p>
                {/if}
            </div>

            <div class="space-y-2">
                <Label for="password">Password <span class="text-red-500">*</span></Label>
                <Input
                    id="password"
                    name="password"
                    type="password"
                    bind:value={$form.password}
                    placeholder="Minimum 8 characters"
                    required
                    data-testid="password-input"
                    class={$errors.password ? 'border-red-500' : ''} />
                {#if $errors.password}
                    <p class="text-sm text-red-500" data-testid="password-error">
                        {$errors.password}
                    </p>
                {/if}
            </div>

            <div class="space-y-2">
                <Label for="role">Role <span class="text-red-500">*</span></Label>
                <Select type="single" bind:value={$form.role}>
                    <SelectTrigger
                        data-testid="role-select"
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

            <div class="flex justify-end gap-2">
                <Button
                    type="button"
                    variant="outline"
                    onclick={handleClose}
                    disabled={$submitting}
                    data-testid="cancel-button">
                    Cancel
                </Button>
                <Button type="submit" disabled={$submitting} data-testid="submit-button">
                    {$submitting ? 'Creating...' : 'Create User'}
                </Button>
            </div>
        </form>
    </DialogContent>
</Dialog>
