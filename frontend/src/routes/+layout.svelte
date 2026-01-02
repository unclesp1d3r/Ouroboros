<script lang="ts">
    import { page } from '$app/state';
    import AppSidebar from '$lib/components/layout/AppSidebar.svelte';
    import Breadcrumbs from '$lib/components/layout/Breadcrumbs.svelte';
    import NightModeToggleButton from '$lib/components/layout/NightModeToggleButton.svelte';
    import Toast from '$lib/components/layout/Toast.svelte';
    import UserMenu from '$lib/components/layout/UserMenu.svelte';
    import * as Sidebar from '$lib/components/ui/sidebar/index.js';
    import { ModeWatcher } from 'mode-watcher';
    import '../app.css';

    let { children } = $props();

    // Show sidebar only for protected routes (not login/logout)
    const showSidebar = $derived(
        !page.route.id?.includes('login') && !page.route.id?.includes('logout')
    );
</script>

<svelte:head>
    <title>Ouroboros</title>
</svelte:head>

{#if showSidebar}
    <Sidebar.Provider>
        <AppSidebar />
        <Sidebar.Inset>
            <header class="flex h-16 shrink-0 items-center gap-2 border-b px-4">
                <Sidebar.Trigger class="ml-1" />
                <div class="flex flex-1 items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="text-lg font-semibold">Ouroboros</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <NightModeToggleButton />
                        <UserMenu />
                    </div>
                </div>
            </header>
            <div class="flex-1 overflow-auto p-4">
                <Breadcrumbs />
                {@render children?.()}
            </div>
        </Sidebar.Inset>
        <ModeWatcher />
    </Sidebar.Provider>
{:else}
    <ModeWatcher />
    {@render children?.()}
{/if}
<Toast />
