<script lang="ts">
    import { page } from '$app/stores';
    import { enhance } from '$app/forms';
    import { onMount } from 'svelte';
    import { Button } from '$lib/components/ui/button';
    import { Tabs, TabsContent, TabsList, TabsTrigger } from '$lib/components/ui/tabs';
    import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { ArrowLeft, Download, Edit, Trash2 } from '@lucide/svelte';
    import { goto } from '$app/navigation';

    // Import our resource components
    import ResourceDetail from '$lib/components/resources/ResourceDetail.svelte';
    import ResourcePreview from '$lib/components/resources/ResourcePreview.svelte';
    import ResourceContent from '$lib/components/resources/ResourceContent.svelte';
    import ResourceLines from '$lib/components/resources/ResourceLines.svelte';

    // Import types
    import type {
        ResourceDetailResponse,
        ResourcePreviewResponse,
        ResourceContentResponse,
        ResourceLinesResponse,
    } from '$lib/schemas/resources';

    // Import resources store
    import { resourcesStore } from '$lib/stores/resources.svelte';

    // Get props using Svelte 5 runes
    let { data, form } = $props<{
        data: {
            resource: ResourceDetailResponse;
            preview: ResourcePreviewResponse;
        };
        form?: {
            content?: ResourceContentResponse;
            lines?: ResourceLinesResponse;
            success?: boolean;
            message?: string;
            error?: string;
        } | null;
    }>();

    // Reactive state using Svelte 5 runes
    let activeTab = $state('overview');
    let content = $state<ResourceContentResponse | null>(null);
    let lines = $state<ResourceLinesResponse | null>(null);
    let loading = $state(false);
    let error = $state<string | null>(null);
    let saving = $state(false);

    // Update store with resource detail data on mount
    onMount(() => {
        resourcesStore.setResourceDetail(data.resource.id, data.resource);
    });

    // Handle form results with $effect to avoid infinite loops
    $effect(() => {
        if (form?.content) {
            content = form.content;
        }
    });

    $effect(() => {
        if (form?.lines) {
            lines = form.lines;
        }
    });

    $effect(() => {
        if (form?.error) {
            error = form.error;
        } else if (form?.success && form?.message) {
            error = null;
            // Show success message briefly
            const timeoutId = setTimeout(() => {
                if (form?.message) {
                    error = null;
                }
            }, 3000);

            // Cleanup timeout if component unmounts
            return () => clearTimeout(timeoutId);
        }
    });

    function handleTabChange(value: string) {
        activeTab = value;
        error = null;

        // Load data for the active tab if not already loaded
        if (value === 'content' && !content) {
            loadContent();
        } else if (value === 'lines' && !lines) {
            loadLines();
        }
    }

    async function loadContent() {
        loading = true;
        const formData = new FormData();

        try {
            const response = await fetch(`/resources/${data.resource.id}?/loadContent`, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const result = await response.json();
                if (result.type === 'success' && result.data?.content) {
                    content = result.data.content;
                }
            }
        } catch (err) {
            console.error('Error loading content:', err);
            error = 'Failed to load content';
        } finally {
            loading = false;
        }
    }

    async function loadLines() {
        loading = true;
        const formData = new FormData();

        try {
            const response = await fetch(`/resources/${data.resource.id}?/loadLines`, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const result = await response.json();
                if (result.type === 'success' && result.data?.lines) {
                    lines = result.data.lines;
                }
            }
        } catch (err) {
            console.error('Error loading lines:', err);
            error = 'Failed to load lines';
        } finally {
            loading = false;
        }
    }

    function handleSaveContent(event: CustomEvent<{ content: string }>) {
        // This will be handled by the form action
        const form = document.getElementById('save-content-form') as HTMLFormElement;
        if (form) {
            const contentInput = form.querySelector('input[name="content"]') as HTMLInputElement;
            if (contentInput) {
                contentInput.value = event.detail.content;
                form.requestSubmit();
            }
        }
    }

    function isEditable(resource: ResourceDetailResponse): boolean {
        // Files under 1MB are editable
        return (resource.byte_size || 0) < 1024 * 1024;
    }

    function getMockLinkedAttacks() {
        // Provide mock linked attacks for test environment
        if (process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST || process.env.CI) {
            return [
                {
                    id: 1,
                    name: 'Test Attack 1',
                    attack_mode: 'dictionary' as const,
                    type_label: 'Dictionary',
                    settings_summary: 'Mock settings',
                },
                {
                    id: 2,
                    name: 'Test Attack 2',
                    attack_mode: 'mask' as const,
                    type_label: 'Mask',
                    settings_summary: 'Mock settings',
                },
            ];
        }
        return [];
    }
</script>

<svelte:head>
    <title>Resource: {data.resource.file_name} - Ouroboros</title>
</svelte:head>

<div class="container mx-auto space-y-6 p-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
            <Button variant="ghost" size="sm" onclick={() => goto('/resources')} class="gap-2">
                <ArrowLeft class="h-4 w-4" />
                Back to Resources
            </Button>
            <div>
                <h1 class="text-3xl font-bold tracking-tight">{data.resource.file_name}</h1>
                <p class="text-muted-foreground">Resource details and content management</p>
            </div>
        </div>
        <div class="flex items-center gap-2">
            <Button variant="outline" size="sm" class="gap-2">
                <Download class="h-4 w-4" />
                Download
            </Button>
            {#if isEditable(data.resource)}
                <Button variant="outline" size="sm" class="gap-2">
                    <Edit class="h-4 w-4" />
                    Edit
                </Button>
            {/if}
            <Button variant="destructive" size="sm" class="gap-2">
                <Trash2 class="h-4 w-4" />
                Delete
            </Button>
        </div>
    </div>

    {#if error}
        <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
        </Alert>
    {/if}

    {#if form?.success && form?.message}
        <Alert>
            <AlertDescription>{form.message}</AlertDescription>
        </Alert>
    {/if}

    <!-- Hidden form for content saving -->
    <form
        id="save-content-form"
        method="POST"
        action="?/saveContent"
        use:enhance={() => {
            saving = true;
            return async ({ result }) => {
                saving = false;
                if (result.type === 'success') {
                    error = null;
                }
            };
        }}
        style="display: none;">
        <input type="hidden" name="content" />
    </form>

    <!-- Main Content -->
    <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList class="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="preview">Preview</TabsTrigger>
            <TabsTrigger value="content" disabled={!isEditable(data.resource)}
                >Edit Content</TabsTrigger>
            <TabsTrigger value="lines">Lines</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" class="space-y-6">
            <ResourceDetail
                resource={data.resource}
                attacks={getMockLinkedAttacks()}
                loading={false}
                error={null} />
        </TabsContent>

        <TabsContent value="preview" class="space-y-6">
            <ResourcePreview
                resource={data.preview}
                previewLines={data.preview.preview_lines}
                loading={false} />
        </TabsContent>

        <TabsContent value="content" class="space-y-6">
            {#if isEditable(data.resource)}
                <ResourceContent
                    resource={content || data.resource}
                    content={content?.content || ''}
                    {saving}
                    loading={loading && activeTab === 'content'}
                    on:save={handleSaveContent} />
            {:else}
                <Card>
                    <CardHeader>
                        <CardTitle>Content Editing Not Available</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p class="text-muted-foreground">
                            This file is too large to edit inline. Files must be under 1MB to enable
                            editing.
                        </p>
                    </CardContent>
                </Card>
            {/if}
        </TabsContent>

        <TabsContent value="lines" class="space-y-6">
            <ResourceLines
                resource={data.resource}
                lines={lines?.lines || []}
                loading={loading && activeTab === 'lines'} />
        </TabsContent>
    </Tabs>
</div>
