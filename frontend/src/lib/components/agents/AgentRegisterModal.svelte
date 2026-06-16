<script lang="ts">
    import { Button } from '$lib/components/ui/button';
    import * as Dialog from '$lib/components/ui/dialog';
    import * as Form from '$lib/components/ui/form';
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';
    import { writable, type Writable } from 'svelte/store';
    import { toast } from 'svelte-sonner';

    export let open: Writable<boolean> = writable(false);
    export let onSubmit: (values: { agentName?: string }) => Promise<void> = async () => {};

    let agentName = '';
    let isLoading = false;

    async function handleSubmit() {
        isLoading = true;
        try {
            await onSubmit({ agentName: agentName || undefined });
            open.set(false);
            agentName = ''; // Reset form
            toast.success('Agent registration initiated.');
        } catch (error) {
            console.error('Registration failed:', error);
            toast.error('Agent registration failed. Please try again.');
        } finally {
            isLoading = false;
        }
    }
</script>

<Dialog.Root bind:open={$open}>
    <Dialog.Content class="sm:max-w-[425px]">
        <Dialog.Header>
            <Dialog.Title>Register New Agent</Dialog.Title>
            <Dialog.Description>
                Enter a custom name for the new agent (optional). The agent will receive further
                instructions upon connection.
            </Dialog.Description>
        </Dialog.Header>
        <form on:submit|preventDefault={handleSubmit}>
            <div class="grid gap-4 py-4">
                <div class="grid grid-cols-4 items-center gap-4">
                    <Label for="agentName" class="text-right">Agent Name</Label>
                    <Input
                        id="agentName"
                        bind:value={agentName}
                        class="col-span-3"
                        placeholder="Optional custom name" />
                </div>
            </div>
            <Dialog.Footer>
                <button
                    type="button"
                    class="ring-offset-background focus-visible:ring-ring border-input bg-background hover:bg-accent hover:text-accent-foreground inline-flex h-10 items-center justify-center rounded-md border px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50"
                    on:click={() => open.set(false)}
                    disabled={isLoading}>Cancel</button>
                <button
                    type="submit"
                    class="ring-offset-background focus-visible:ring-ring bg-primary text-primary-foreground hover:bg-primary/90 inline-flex h-10 items-center justify-center rounded-md px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50"
                    disabled={isLoading}>
                    {#if isLoading}
                        <svg
                            class="mr-3 -ml-1 h-5 w-5 animate-spin text-white"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24">
                            <circle
                                class="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                stroke-width="4"></circle>
                            <path
                                class="opacity-75"
                                fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            ></path>
                        </svg>
                        Registering...
                    {:else}
                        Register Agent
                    {/if}
                </button>
            </Dialog.Footer>
        </form>
    </Dialog.Content>
</Dialog.Root>
