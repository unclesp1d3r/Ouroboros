import type { UserSession } from '$lib/schemas/auth';

// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
    namespace App {
        // interface Error {}
        interface Locals {
            user: UserSession | null;
            session: string | null;
        }
        // interface PageData {}
        // interface PageState {}
        // interface Platform {}
    }

    // Vite-defined constants
    const __API_BASE_URL__: string;
}

export type __sveltekit_app_types = true;
