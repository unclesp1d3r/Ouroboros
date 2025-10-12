<script lang="ts">
    import { page } from '$app/stores';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Button } from '$lib/components/ui/button';
    import { AlertCircle, Lock } from '@lucide/svelte';

    $: error = $page.error;
    $: statusCode = $page.status;
</script>

<svelte:head>
    <title>Error - Projects - Ouroboros</title>
</svelte:head>

<div class="container mx-auto space-y-6 p-6">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-3xl font-bold tracking-tight">Project Management</h1>
            <p class="text-muted-foreground">Manage and organize your password cracking projects</p>
        </div>
    </div>

    {#if statusCode === 403}
        <Alert variant="destructive" data-testid="error-403">
            <Lock class="h-4 w-4" />
            <AlertDescription>
                Access denied. You must be an administrator to view projects.
            </AlertDescription>
        </Alert>
    {:else}
        <Alert variant="destructive" data-testid="error-general">
            <AlertCircle class="h-4 w-4" />
            <AlertDescription>
                Failed to load projects: {statusCode}
                {error?.message || 'Unknown error'}
            </AlertDescription>
        </Alert>
    {/if}

    <div class="flex justify-center">
        <Button onclick={() => window.location.reload()} data-testid="retry-button"
            >Try Again</Button>
    </div>
</div>
