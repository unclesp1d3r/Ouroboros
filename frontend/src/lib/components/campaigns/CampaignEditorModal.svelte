<script lang="ts">
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Button } from '$lib/components/ui/button';
    import { Checkbox } from '$lib/components/ui/checkbox';
    import * as Dialog from '$lib/components/ui/dialog';
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';
    import { Textarea } from '$lib/components/ui/textarea';
    import axios, { isAxiosError } from 'axios';
    import { createEventDispatcher } from 'svelte';

    interface Campaign {
        id: number;
        name: string;
        description?: string;
        priority: number;
        project_id: number;
        hash_list_id: number;
        is_unavailable: boolean;
        state?: string;
        created_at?: string;
        updated_at?: string;
    }

    let {
        open = $bindable(false),
        campaign = null,
        projectId = null,
        hashListId = null,
    }: {
        open?: boolean;
        campaign?: Campaign | null;
        projectId?: number | null;
        hashListId?: number | null;
    } = $props();

    const dispatch = createEventDispatcher<{
        close: void;
        success: { campaign: Campaign; isEdit: boolean };
    }>();

    // Reactive form data based on campaign prop using runes
    let formData = $state({
        name: '',
        description: '',
        priority: 0,
        project_id: 0,
        hash_list_id: 0,
        is_unavailable: false,
    });

    let loading = $state(false);
    let error = $state('');
    let validationErrors = $state<Record<string, string[]>>({});

    // Update form data when campaign prop changes using $effect
    $effect(() => {
        if (campaign) {
            // Editing existing campaign - use campaign's project_id
            formData.name = campaign.name || '';
            formData.description = campaign.description || '';
            formData.priority = campaign.priority || 0;
            formData.project_id = campaign.project_id;
            formData.hash_list_id = campaign.hash_list_id || hashListId || 0;
            formData.is_unavailable = campaign.is_unavailable || false;
        } else {
            // Creating new campaign - use projectId prop
            formData.name = '';
            formData.description = '';
            formData.priority = 0;
            formData.project_id = projectId || 0;
            formData.hash_list_id = hashListId || 0;
            formData.is_unavailable = false;
        }
    });

    function handleClose() {
        open = false;
        error = '';
        validationErrors = {};
        dispatch('close');
    }

    async function handleSubmit(event: SubmitEvent) {
        event.preventDefault();
        loading = true;
        error = '';
        validationErrors = {};

        try {
            const isEdit = !!campaign;
            const url = isEdit ? `/api/v1/web/campaigns/${campaign.id}` : '/api/v1/web/campaigns/';
            const method = isEdit ? 'patch' : 'post';

            const response = await axios[method](url, formData);
            dispatch('success', { campaign: response.data as Campaign, isEdit });
            handleClose();
        } catch (e) {
            if (isAxiosError(e) && e.response?.status === 422 && e.response?.data?.detail) {
                // Handle validation errors
                const errors: Record<string, string[]> = {};
                for (const error of e.response.data.detail) {
                    const field = error.loc[error.loc.length - 1];
                    if (!errors[field]) errors[field] = [];
                    errors[field].push(error.msg);
                }
                validationErrors = errors;
            } else {
                error = `Failed to ${campaign ? 'update' : 'create'} campaign.`;
            }
        } finally {
            loading = false;
        }
    }

    function getFieldError(field: string): string {
        return validationErrors[field]?.[0] || '';
    }
</script>

<Dialog.Root bind:open onOpenChange={handleClose}>
    <Dialog.Content class="sm:max-w-md">
        <Dialog.Header>
            <Dialog.Title data-testid="modal-title">
                {campaign ? 'Edit Campaign' : 'Create Campaign'}
            </Dialog.Title>
            <Dialog.Description>
                {campaign
                    ? 'Update campaign details'
                    : 'Create a new campaign for password cracking'}
            </Dialog.Description>
        </Dialog.Header>

        {#if error}
            <Alert variant="destructive">
                <AlertDescription data-testid="error-message">{error}</AlertDescription>
            </Alert>
        {/if}

        <form onsubmit={handleSubmit} class="space-y-4">
            <div class="space-y-2">
                <Label for="name">Name <span class="text-red-500">*</span></Label>
                <Input
                    id="name"
                    bind:value={formData.name}
                    placeholder="Campaign name"
                    required
                    data-testid="name-input"
                    class={getFieldError('name') ? 'border-red-500' : ''} />
                {#if getFieldError('name')}
                    <p class="text-sm text-red-500" data-testid="name-error">
                        {getFieldError('name')}
                    </p>
                {/if}
            </div>

            <div class="space-y-2">
                <Label for="description">Description</Label>
                <Textarea
                    id="description"
                    bind:value={formData.description}
                    placeholder="Optional campaign description"
                    rows={3}
                    data-testid="description-input"
                    class={getFieldError('description') ? 'border-red-500' : ''} />
                {#if getFieldError('description')}
                    <p class="text-sm text-red-500" data-testid="description-error">
                        {getFieldError('description')}
                    </p>
                {/if}
            </div>

            <div class="space-y-2">
                <Label for="priority">Priority</Label>
                <Input
                    id="priority"
                    type="number"
                    bind:value={formData.priority}
                    min="0"
                    placeholder="0"
                    data-testid="priority-input"
                    class={getFieldError('priority') ? 'border-red-500' : ''} />
                {#if getFieldError('priority')}
                    <p class="text-sm text-red-500" data-testid="priority-error">
                        {getFieldError('priority')}
                    </p>
                {/if}
            </div>

            <div class="flex items-center space-x-2">
                <Checkbox
                    id="unavailable"
                    bind:checked={formData.is_unavailable}
                    data-testid="unavailable-checkbox" />
                <Label for="unavailable" class="text-sm font-normal">
                    Mark as unavailable (not ready for use)
                </Label>
            </div>

            <Dialog.Footer class="flex gap-2">
                <Button
                    type="button"
                    variant="outline"
                    onclick={handleClose}
                    disabled={loading}
                    data-testid="cancel-button">
                    Cancel
                </Button>
                <Button type="submit" disabled={loading} data-testid="submit-button">
                    {#if loading}
                        Saving...
                    {:else}
                        {campaign ? 'Update' : 'Create'} Campaign
                    {/if}
                </Button>
            </Dialog.Footer>
        </form>
    </Dialog.Content>
</Dialog.Root>
