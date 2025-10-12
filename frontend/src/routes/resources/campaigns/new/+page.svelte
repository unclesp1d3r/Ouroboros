<script lang="ts">
    import { superForm } from 'sveltekit-superforms';
    import { zod4Client } from 'sveltekit-superforms/adapters';
    import { Button } from '$lib/components/ui/button';
    import { Input } from '$lib/components/ui/input';
    import { Textarea } from '$lib/components/ui/textarea';
    import { Checkbox } from '$lib/components/ui/checkbox';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Label } from '$lib/components/ui/label';
    import * as Dialog from '$lib/components/ui/dialog';
    import { campaignFormSchema } from '$lib/schemas/campaign';
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';

    let { data } = $props();

    // Initialize Superforms
    const superform = superForm(data.form, {
        validators: zod4Client(campaignFormSchema),
        onResult: ({ result }) => {
            if (result.type === 'redirect') {
                // Close modal and navigate back to campaigns
                handleClose();
            }
        },
    });

    const { form, errors, enhance, submitting, message } = superform;

    // Modal state - open by default when this route is accessed
    let open = $state(true);

    function handleClose() {
        open = false;
        // Navigate back to campaigns list
        goto('/campaigns');
    }

    // Get URL parameters for default values
    const projectId = $page.url.searchParams.get('project_id');
    const hashListId = $page.url.searchParams.get('hash_list_id');

    // Set default values if provided via URL params
    if (projectId && !$form.project_id) {
        $form.project_id = parseInt(projectId, 10);
    }
    if (hashListId && !$form.hash_list_id) {
        $form.hash_list_id = parseInt(hashListId, 10);
    }
</script>

<svelte:head>
    <title>Create Campaign - Ouroboros</title>
</svelte:head>

<Dialog.Root bind:open onOpenChange={handleClose}>
    <Dialog.Content class="sm:max-w-md">
        <Dialog.Header>
            <Dialog.Title data-testid="modal-title">Create Campaign</Dialog.Title>
            <Dialog.Description>Create a new campaign for password cracking</Dialog.Description>
        </Dialog.Header>

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
                    bind:value={$form.name}
                    placeholder="Campaign name"
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
                <Label for="description">Description</Label>
                <Textarea
                    id="description"
                    name="description"
                    bind:value={$form.description}
                    placeholder="Optional campaign description"
                    rows={3}
                    data-testid="description-input"
                    class={$errors.description ? 'border-red-500' : ''} />
                {#if $errors.description}
                    <p class="text-sm text-red-500" data-testid="description-error">
                        {$errors.description}
                    </p>
                {/if}
            </div>

            <div class="space-y-2">
                <Label for="priority">Priority</Label>
                <Input
                    id="priority"
                    name="priority"
                    type="number"
                    bind:value={$form.priority}
                    min="0"
                    placeholder="0"
                    data-testid="priority-input"
                    class={$errors.priority ? 'border-red-500' : ''} />
                {#if $errors.priority}
                    <p class="text-sm text-red-500" data-testid="priority-error">
                        {$errors.priority}
                    </p>
                {/if}
            </div>

            <div class="space-y-2">
                <Label for="project_id">Project ID <span class="text-red-500">*</span></Label>
                <Input
                    id="project_id"
                    name="project_id"
                    type="number"
                    bind:value={$form.project_id}
                    min="1"
                    placeholder="Project ID"
                    required
                    data-testid="project-id-input"
                    class={$errors.project_id ? 'border-red-500' : ''} />
                {#if $errors.project_id}
                    <p class="text-sm text-red-500" data-testid="project-id-error">
                        {$errors.project_id}
                    </p>
                {/if}
            </div>

            <div class="space-y-2">
                <Label for="hash_list_id">Hash List ID <span class="text-red-500">*</span></Label>
                <Input
                    id="hash_list_id"
                    name="hash_list_id"
                    type="number"
                    bind:value={$form.hash_list_id}
                    min="1"
                    placeholder="Hash List ID"
                    required
                    data-testid="hash-list-id-input"
                    class={$errors.hash_list_id ? 'border-red-500' : ''} />
                {#if $errors.hash_list_id}
                    <p class="text-sm text-red-500" data-testid="hash-list-id-error">
                        {$errors.hash_list_id}
                    </p>
                {/if}
            </div>

            <div class="flex items-center space-x-2">
                <Checkbox
                    id="is_unavailable"
                    name="is_unavailable"
                    bind:checked={$form.is_unavailable}
                    data-testid="unavailable-checkbox" />
                <Label for="is_unavailable" class="text-sm font-normal">
                    Mark as unavailable (not ready for use)
                </Label>
            </div>

            <Dialog.Footer class="flex gap-2">
                <Button
                    type="button"
                    variant="outline"
                    onclick={handleClose}
                    disabled={$submitting}
                    data-testid="cancel-button">
                    Cancel
                </Button>
                <Button type="submit" disabled={$submitting} data-testid="submit-button">
                    {#if $submitting}
                        Creating...
                    {:else}
                        Create Campaign
                    {/if}
                </Button>
            </Dialog.Footer>
        </form>
    </Dialog.Content>
</Dialog.Root>
