<script lang="ts">
    import { Label } from '$lib/components/ui/label';
    import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
    import { authStore } from '$lib/stores/auth.svelte';
    import { z } from 'zod';

    // Hash list type
    const HashListSchema = z.object({
        id: z.number(),
        name: z.string(),
        description: z.string().nullable(),
        hash_count: z.number(),
        cracked_count: z.number(),
        hash_type: z.number(),
        created_at: z.string(),
    });

    // API response schema
    const HashListsResponseSchema = z.object({
        items: z.array(HashListSchema),
        total: z.number(),
        page: z.number(),
        page_size: z.number(),
    });

    type HashList = z.infer<typeof HashListSchema>;

    let {
        value = $bindable(),
        disabled = false,
        placeholder = 'Select a hash list',
        required = false,
        errors = null,
        class: className = '',
    }: {
        value?: number | undefined;
        disabled?: boolean;
        placeholder?: string;
        required?: boolean;
        errors?: string[] | null;
        class?: string;
    } = $props();

    // State
    let hashLists = $state<HashList[]>([]);
    let loading = $state(false);
    let error = $state<string | null>(null);

    // Get current project from auth store
    const currentProject = $derived(authStore.currentProject);
    const selectedHashList = $derived(value ? hashLists.find((hl) => hl.id === value) : null);

    // Fetch hash lists when component mounts or project changes
    async function fetchHashLists() {
        if (!currentProject) {
            hashLists = [];
            error = 'No active project selected';
            return;
        }

        loading = true;
        error = null;

        try {
            const response = await fetch(
                `/api/v1/web/hash_lists/?project_id=${currentProject.id}&size=100`,
                {
                    credentials: 'include',
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            const parsedData = HashListsResponseSchema.parse(data);
            hashLists = parsedData.items;

            // If there's only one hash list, auto-select it
            if (hashLists.length === 1 && !value) {
                value = hashLists[0].id;
            }
        } catch (err) {
            console.error('Failed to fetch hash lists:', err);
            error = err instanceof Error ? err.message : 'Failed to fetch hash lists';
            hashLists = [];
        } finally {
            loading = false;
        }
    }

    // Watch for project changes
    $effect(() => {
        if (currentProject) {
            fetchHashLists();
        } else {
            hashLists = [];
            error = 'No active project selected';
        }
    });

    // Handle selection change
    function handleValueChange(newValue: string) {
        const selectedId = parseInt(newValue);
        value = selectedId || undefined;
    }
</script>

<div class="space-y-2 {className}">
    <Label for="hash-list-selector">
        Hash List {#if required}<span class="text-red-500">*</span>{/if}
    </Label>

    {#if loading}
        <Select type="single" disabled>
            <SelectTrigger id="hash-list-selector">
                <span class="text-muted-foreground">Loading hash lists...</span>
            </SelectTrigger>
        </Select>
    {:else if error}
        <Select type="single" disabled>
            <SelectTrigger id="hash-list-selector" class="border-red-500">
                <span class="text-muted-foreground">{error}</span>
            </SelectTrigger>
        </Select>
    {:else if hashLists.length === 0}
        <Select type="single" disabled>
            <SelectTrigger id="hash-list-selector">
                <span class="text-muted-foreground">No hash lists available in this project</span>
            </SelectTrigger>
        </Select>
    {:else}
        <Select
            type="single"
            value={value ? value.toString() : undefined}
            onValueChange={handleValueChange}
            {disabled}>
            <SelectTrigger
                id="hash-list-selector"
                class={errors && errors.length > 0 ? 'border-red-500' : ''}>
                <span>
                    {selectedHashList
                        ? `${selectedHashList.name} (${selectedHashList.hash_count} hashes)`
                        : placeholder}
                </span>
            </SelectTrigger>
            <SelectContent>
                {#each hashLists as hashList (hashList.id)}
                    <SelectItem value={hashList.id.toString()}>
                        <div class="flex flex-col">
                            <span class="font-medium">{hashList.name}</span>
                            <span class="text-muted-foreground text-xs">
                                {hashList.hash_count} hashes
                                {#if hashList.cracked_count > 0}
                                    · {hashList.cracked_count} cracked
                                {/if}
                                {#if hashList.description}
                                    · {hashList.description}
                                {/if}
                            </span>
                        </div>
                    </SelectItem>
                {/each}
            </SelectContent>
        </Select>
    {/if}

    {#if errors && errors.length > 0}
        {#each errors as error (error)}
            <p class="text-sm text-red-500" data-testid="hash-list-error">
                {error}
            </p>
        {/each}
    {/if}
</div>
