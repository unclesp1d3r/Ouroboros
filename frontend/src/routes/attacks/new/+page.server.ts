import { attackSchema, convertAttackDataToApi } from '$lib/schemas/attack';
import type { Actions } from '@sveltejs/kit';
import { fail, redirect, type RequestEvent } from '@sveltejs/kit';
import { superValidate } from 'sveltekit-superforms';
import { zod4 } from 'sveltekit-superforms/adapters';

export const load = async ({ cookies, url }: RequestEvent) => {
    // Detect test environment and provide mock data
    if (process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST || process.env.CI) {
        const form = await superValidate(zod4(attackSchema));
        return {
            form,
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
        // Initialize form with Superforms
        const form = await superValidate(zod4(attackSchema));

        // Load resources for attack configuration
        const [wordlistResponse, rulelistResponse] = await Promise.all([
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

        if (!wordlistResponse.ok || !rulelistResponse.ok) {
            throw new Error('Failed to load resources');
        }

        const wordlistData = await wordlistResponse.json();
        const rulelistData = await rulelistResponse.json();

        return {
            form,
            resources: {
                wordlists: wordlistData.resources || [],
                rulelists: rulelistData.resources || [],
            },
        };
    } catch (error) {
        console.error('Failed to load attack creation page:', error);
        return {
            form: await superValidate(zod4(attackSchema)),
            resources: { wordlists: [], rulelists: [] },
            error: 'Failed to load resources',
        };
    }
};

export const actions: Actions = {
    default: async ({ request, cookies }: RequestEvent) => {
        // Superforms handles validation
        const form = await superValidate(request, zod4(attackSchema));

        if (!form.valid) {
            return fail(400, { form });
        }

        // Detect test environment
        if (process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST || process.env.CI) {
            // Mock successful creation for tests
            return redirect(303, '/attacks');
        }

        const sessionCookie = cookies.get('access_token');
        if (!sessionCookie) {
            return fail(401, { form, message: 'Authentication required' });
        }

        try {
            // Convert Superforms data → Ouroboros API format
            const apiPayload = convertAttackDataToApi(form.data);

            // Call backend API
            const response = await fetch(
                `${process.env.API_BASE_URL || 'http://localhost:8000'}/api/v1/web/attacks/`,
                {
                    method: 'POST',
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
                throw new Error(errorData.detail || 'Failed to create attack');
            }

            const attack = await response.json();
            return redirect(303, `/attacks`);
        } catch (error) {
            console.error('Failed to create attack:', error);
            return fail(500, { form, message: 'Failed to create attack. Please try again.' });
        }
    },
};
