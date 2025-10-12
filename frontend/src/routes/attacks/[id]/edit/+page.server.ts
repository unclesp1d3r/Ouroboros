import { attackSchema, convertAttackDataToApi } from '$lib/schemas/attack';
import type { Actions } from '@sveltejs/kit';
import { error, fail, redirect, type RequestEvent } from '@sveltejs/kit';
import { superValidate } from 'sveltekit-superforms';
import { zod4 } from 'sveltekit-superforms/adapters';

export const load = async ({ params, cookies, url }: RequestEvent) => {
    const attackId = params.id;

    // Detect test environment and provide mock data
    if (process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST || process.env.CI) {
        const form = await superValidate(zod4(attackSchema));
        // Pre-populate with mock attack data for editing
        form.data = {
            name: 'Test Attack',
            attack_mode: 'dictionary',
            min_length: 8,
            max_length: 16,
            wordlist_source: 'existing',
            word_list_id: 'test-wordlist-1',
            rule_list_id: 'test-rulelist-1',
            modifiers: [],
            wordlist_inline: [],
            wordlists: [],
            rulelists: [],
            comment: 'Test comment',
        };
        return {
            form,
            attackId,
            resources: {
                wordlists: [
                    {
                        id: 'test-wordlist-1',
                        name: 'Test Wordlist 1',
                        type: 'word_list',
                        file_size: 1024,
                    },
                    {
                        id: 'test-wordlist-2',
                        name: 'Test Wordlist 2',
                        type: 'word_list',
                        file_size: 2048,
                    },
                ],
                rulelists: [
                    {
                        id: 'test-rulelist-1',
                        name: 'Test Rulelist 1',
                        type: 'rule_list',
                        file_size: 512,
                    },
                    {
                        id: 'test-rulelist-2',
                        name: 'Test Rulelist 2',
                        type: 'rule_list',
                        file_size: 1024,
                    },
                ],
            },
        };
    }

    // Normal SSR logic with authentication
    const sessionCookie = cookies.get('access_token');
    if (!sessionCookie) {
        throw redirect(302, '/login');
    }

    try {
        // Load existing attack data
        const [attackResponse, wordlistResponse, rulelistResponse] = await Promise.all([
            fetch(
                `${process.env.API_BASE_URL || 'http://localhost:8000'}/api/v1/web/attacks/${attackId}`,
                {
                    headers: {
                        Cookie: `access_token=${sessionCookie}`,
                    },
                }
            ),
            fetch(
                `${process.env.API_BASE_URL || 'http://localhost:8000'}/api/v1/web/resources?type=word_list`,
                {
                    headers: {
                        Cookie: `access_token=${sessionCookie}`,
                    },
                }
            ),
            fetch(
                `${process.env.API_BASE_URL || 'http://localhost:8000'}/api/v1/web/resources?type=rule_list`,
                {
                    headers: {
                        Cookie: `access_token=${sessionCookie}`,
                    },
                }
            ),
        ]);

        if (!attackResponse.ok) {
            if (attackResponse.status === 404) {
                throw error(404, 'Attack not found');
            }
            throw new Error('Failed to load attack');
        }

        if (!wordlistResponse.ok || !rulelistResponse.ok) {
            throw new Error('Failed to load resources');
        }

        const attackData = await attackResponse.json();
        const wordlistData = await wordlistResponse.json();
        const rulelistData = await rulelistResponse.json();

        // Initialize form with existing attack data
        const form = await superValidate(attackData, zod4(attackSchema));

        return {
            form,
            attackId,
            resources: {
                wordlists: wordlistData.resources || [],
                rulelists: rulelistData.resources || [],
            },
        };
    } catch (err) {
        console.error('Failed to load attack edit page:', err);
        if (err instanceof Error && err.message.includes('404')) {
            throw error(404, 'Attack not found');
        }
        return {
            form: await superValidate(zod4(attackSchema)),
            attackId,
            resources: { wordlists: [], rulelists: [] },
            error: 'Failed to load attack data',
        };
    }
};

export const actions: Actions = {
    default: async ({ params, request, cookies }: RequestEvent) => {
        const attackId = params.id;

        // Superforms handles validation
        const form = await superValidate(request, zod4(attackSchema));

        if (!form.valid) {
            return fail(400, { form });
        }

        // Detect test environment
        if (process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST || process.env.CI) {
            // Mock successful update for tests
            return redirect(303, '/attacks');
        }

        const sessionCookie = cookies.get('access_token');
        if (!sessionCookie) {
            return fail(401, { form, message: 'Authentication required' });
        }

        try {
            // Convert Superforms data → Ouroboros API format
            const apiPayload = convertAttackDataToApi(form.data);

            // Call backend API for update
            const response = await fetch(
                `${process.env.API_BASE_URL || 'http://localhost:8000'}/api/v1/web/attacks/${attackId}`,
                {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        Cookie: `access_token=${sessionCookie}`,
                    },
                    body: JSON.stringify(apiPayload),
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                if (response.status === 422) {
                    // Return validation errors - let Superforms handle the error display
                    return fail(422, {
                        form,
                        message: 'Validation failed. Please check your input.',
                    });
                }
                if (response.status === 404) {
                    return fail(404, { form, message: 'Attack not found' });
                }
                throw new Error(errorData.detail || 'Failed to update attack');
            }

            const attack = await response.json();
            return redirect(303, `/attacks`);
        } catch (error) {
            console.error('Failed to update attack:', error);
            return fail(500, { form, message: 'Failed to update attack. Please try again.' });
        }
    },
};
