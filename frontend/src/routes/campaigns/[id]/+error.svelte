<script lang="ts">
    import { page } from '$app/stores';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Button } from '$lib/components/ui/button';
    import { goto } from '$app/navigation';

    $: error = $page.error;
    $: statusCode = $page.status;
</script>

<svelte:head>
    <title>Error - Ouroboros</title>
</svelte:head>

<div class="container mx-auto max-w-7xl p-6">
    <div class="flex items-center justify-center py-8">
        <div class="text-center">
            {#if statusCode === 404}
                <div class="mb-4 text-6xl font-bold text-gray-400">404</div>
                <Alert class="mb-4" variant="destructive">
                    <AlertDescription data-testid="not-found">Campaign not found.</AlertDescription>
                </Alert>
            {:else}
                <div class="mb-4 text-6xl font-bold text-gray-400">{statusCode || 500}</div>
                <Alert class="mb-4" variant="destructive">
                    <AlertDescription data-testid="error"
                        >Failed to load campaign details.</AlertDescription>
                </Alert>
            {/if}

            <div class="mt-6">
                <Button onclick={() => goto('/campaigns')} variant="outline">
                    ← Back to Campaigns
                </Button>
            </div>
        </div>
    </div>
</div>
