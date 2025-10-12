<script lang="ts">
    import { page } from '$app/stores';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Button } from '$lib/components/ui/button';
    import { AlertCircle } from '@lucide/svelte';

    $: error = $page.error;
    $: statusCode = $page.status;
</script>

<svelte:head>
    <title>Error - Resources - Ouroboros</title>
</svelte:head>

<div class="container mx-auto space-y-6 p-6">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-3xl font-bold tracking-tight">Resources</h1>
            <p class="text-muted-foreground">
                Manage wordlists, rule lists, masks, and charsets for password cracking attacks
            </p>
        </div>
    </div>

    <Alert variant="destructive">
        <AlertCircle class="h-4 w-4" />
        <AlertDescription>
            Failed to load resources: {statusCode}
            {error?.message || 'Unknown error'}
        </AlertDescription>
    </Alert>

    <div class="flex justify-center">
        <Button onclick={() => window.location.reload()}>Try Again</Button>
    </div>
</div>
