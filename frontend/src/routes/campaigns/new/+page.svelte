<script lang="ts">
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Button } from '$lib/components/ui/button';
    import {
        Card,
        CardContent,
        CardHeader,
        CardTitle,
        CardDescription,
    } from '$lib/components/ui/card';
    import { Checkbox } from '$lib/components/ui/checkbox';
    import HashListSelector from '$lib/components/ui/hash-list-selector.svelte';
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';
    import { Textarea } from '$lib/components/ui/textarea';
    import { campaignFormSchema } from '$lib/schemas/campaign';
    import { authStore } from '$lib/stores/auth.svelte';
    import { superForm } from 'sveltekit-superforms';
    import { zod4Client } from 'sveltekit-superforms/adapters';
    import { ArrowLeft } from '@lucide/svelte';

    let { data } = $props();

    // Initialize Superforms
    const superform = superForm(data.form, {
        validators: zod4Client(campaignFormSchema),
        onResult: ({ result }) => {
            if (result.type === 'redirect') {
                // Navigate back to campaigns
                goto('/campaigns');
            }
        },
    });

    const { form, errors, enhance, submitting, message } = superform;

    // Get current project from auth store
    const currentProject = $derived(authStore.currentProject);

    function handleCancel() {
        // Navigate back to campaigns list
        goto('/campaigns');
    }

    // Get URL parameters for default values
    const hashListId = $page.url.searchParams.get('hash_list_id');

    // Set default values reactively
    $effect(() => {
        // Set hash_list_id if provided via URL params
        if (hashListId && $form.hash_list_id == null) {
            $form.hash_list_id = parseInt(hashListId, 10);
        }

        // Set project_id from current project
        if (currentProject && $form.project_id == null) {
            $form.project_id = currentProject.id;
        }
    });
</script>

<svelte:head>
    <title>Create Campaign - Ouroboros</title>
</svelte:head>

<!-- Back button -->
<div class="mb-4">
    <Button variant="ghost" onclick={handleCancel} class="h-auto p-0">
        <ArrowLeft class="mr-2 h-4 w-4" />
        Back to Campaigns
    </Button>
</div>

<Card class="mx-auto max-w-2xl">
    <CardHeader>
        <CardTitle data-testid="page-title">Create Campaign</CardTitle>
        <CardDescription>
            Create a new campaign for password cracking in project:
            <strong>{currentProject?.name || 'No project selected'}</strong>
        </CardDescription>
    </CardHeader>

    <CardContent>
        {#if $message}
            <Alert variant="destructive" class="mb-6">
                <AlertDescription data-testid="error-message">{$message}</AlertDescription>
            </Alert>
        {/if}

        {#if !currentProject}
            <Alert variant="destructive" class="mb-6">
                <AlertDescription>
                    No active project selected. Please select a project before creating a campaign.
                </AlertDescription>
            </Alert>
        {:else}
            <form method="POST" use:enhance class="space-y-6">
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

                <HashListSelector
                    bind:value={$form.hash_list_id}
                    required
                    errors={$errors.hash_list_id} />

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

                <div class="flex justify-end gap-4 border-t pt-4">
                    <Button
                        type="button"
                        variant="outline"
                        onclick={handleCancel}
                        disabled={$submitting}
                        data-testid="cancel-button">
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        disabled={$submitting || !currentProject}
                        data-testid="submit-button">
                        {#if $submitting}
                            Creating...
                        {:else}
                            Create Campaign
                        {/if}
                    </Button>
                </div>
            </form>
        {/if}
    </CardContent>
</Card>
