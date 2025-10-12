<script lang="ts">
    import LoginForm from '$lib/components/auth/login-form.svelte';
    import type { PageData } from './$types';

    export let data: PageData;
</script>

<svelte:head>
    <title>Login - Ouroboros</title>
    <meta name="description" content="Sign in to your Ouroboros account" />
</svelte:head>

<div class="bg-background flex min-h-svh flex-col items-center justify-center gap-6 p-6 md:p-10">
    <div class="flex w-full max-w-sm flex-col gap-6">
        <!-- Branding -->
        <a href="/" class="flex items-center gap-2 self-center font-medium">
            <img src="/logo.svg" alt="Ouroboros Logo" width="48" height="48" class="h-12 w-12" />
            <span class="text-xl font-semibold">Ouroboros</span>
        </a>

        <!-- Login Form -->
        <LoginForm {data} />

        <!-- Footer -->
        <div class="text-muted-foreground text-center text-sm">
            Secure password cracking management system
        </div>
    </div>
</div>
