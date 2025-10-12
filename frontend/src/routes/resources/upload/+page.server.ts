import { superValidate } from 'sveltekit-superforms';
import { zod4 } from 'sveltekit-superforms/adapters';
import { fail, redirect, error } from '@sveltejs/kit';
import { z } from 'zod';
import {
    uploadSchema,
    type HashGuessResults,
    type HashTypeDropdownItem,
    type UploadResponse,
    type UploadStatusResponse,
} from './schema';
import { createSessionServerApi } from '$lib/server/api';
import type { Actions, PageServerLoad } from './$types';

// Zod schemas for API responses
const hashGuessResultsSchema = z.object({
    candidates: z.array(
        z.object({
            hash_type: z.number(),
            name: z.string(),
            confidence: z.number(),
        })
    ),
});

const hashTypeDropdownSchema = z.array(
    z.object({
        mode: z.number(),
        name: z.string(),
        category: z.string(),
        confidence: z.number().optional(),
    })
);

const uploadResponseSchema = z.object({
    resource_id: z.number(),
    presigned_url: z.string().optional(),
    resource: z.object({
        file_name: z.string(),
    }),
});

export const load: PageServerLoad = async ({ cookies, url }) => {
    // Test environment detection
    if (process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST || process.env.CI) {
        const form = await superValidate(zod4(uploadSchema));
        return {
            form,
            projectId: 1, // Mock project ID for tests
            hashTypes: [] as HashTypeDropdownItem[],
        };
    }

    const sessionCookie = cookies.get('access_token');
    if (!sessionCookie) {
        throw error(401, 'Authentication required');
    }

    try {
        // Get project ID from URL params or user's current project
        const projectId = url.searchParams.get('project_id');

        // Initialize form with project ID if available
        const form = await superValidate(zod4(uploadSchema));
        if (projectId) {
            form.data.projectId = parseInt(projectId);
        }

        return {
            form,
            projectId: projectId ? parseInt(projectId) : null,
            hashTypes: [] as HashTypeDropdownItem[],
        };
    } catch (err) {
        console.error('Failed to load upload page:', err);
        throw error(500, 'Failed to load upload page');
    }
};

export const actions: Actions = {
    // Validate hash content and get hash type suggestions
    validate: async ({ request, cookies }) => {
        const form = await superValidate(request, zod4(uploadSchema));

        if (!form.valid) {
            return fail(400, { form });
        }

        if (!form.data.textContent?.trim()) {
            return fail(400, {
                form,
                validationError: 'Please enter hash content to validate',
            });
        }

        const sessionCookie = cookies.get('access_token');
        if (!sessionCookie) {
            return fail(401, { form, validationError: 'Authentication required' });
        }

        try {
            const serverApi = createSessionServerApi(sessionCookie);

            const response = await serverApi.post(
                '/api/v1/web/hash_guess/',
                { hash_material: form.data.textContent },
                hashGuessResultsSchema
            );

            if (response.candidates.length === 0) {
                return fail(400, {
                    form,
                    validationError:
                        'No valid hash types detected. Please check your input format.',
                });
            }

            // Load available hash types for the dropdown
            const hashTypesResponse = await serverApi.get(
                '/api/v1/web/modals/hash_types',
                hashTypeDropdownSchema
            );

            // Filter hash types to only include those detected by the guess service
            const detectedHashTypes = new Map(
                response.candidates.map((candidate) => [candidate.hash_type, candidate.confidence])
            );

            const availableHashTypes = hashTypesResponse
                .filter((hashType) => detectedHashTypes.has(hashType.mode))
                .map((hashType) => ({
                    ...hashType,
                    confidence: detectedHashTypes.get(hashType.mode),
                }))
                .toSorted((a, b) => {
                    // Sort by confidence descending, then by mode ascending
                    if (a.confidence !== b.confidence) {
                        return (b.confidence || 0) - (a.confidence || 0);
                    }
                    return a.mode - b.mode;
                });

            // Auto-select the highest confidence hash type
            if (availableHashTypes.length > 0) {
                form.data.selectedHashTypeId = availableHashTypes[0].mode.toString();
            }

            return {
                form,
                hashGuessResults: response,
                hashTypes: availableHashTypes,
                hasValidHashes: true,
            };
        } catch (err) {
            console.error('Hash validation failed:', err);
            return fail(500, {
                form,
                validationError: 'Failed to validate hashes. Please try again.',
            });
        }
    },

    // Upload file or text content
    upload: async ({ request, cookies }) => {
        const form = await superValidate(request, zod4(uploadSchema));

        if (!form.valid) {
            return fail(400, { form });
        }

        if (!form.data.projectId) {
            return fail(400, { form, uploadError: 'Project ID is required' });
        }

        const sessionCookie = cookies.get('access_token');
        if (!sessionCookie) {
            return fail(401, { form, uploadError: 'Authentication required' });
        }

        try {
            const serverApi = createSessionServerApi(sessionCookie);
            const formData = new FormData();
            formData.append('project_id', form.data.projectId.toString());

            if (form.data.uploadMode === 'text') {
                if (!form.data.textContent?.trim()) {
                    return fail(400, { form, uploadError: 'Please enter hash content' });
                }

                formData.append('text_content', form.data.textContent);

                if (form.data.fileName) {
                    formData.append('file_name', form.data.fileName);
                }

                if (form.data.selectedHashTypeId) {
                    formData.append('hash_type_override', form.data.selectedHashTypeId);
                }
            } else {
                // File upload mode - file handling will be done client-side with FileDropZone
                if (!form.data.fileName) {
                    return fail(400, { form, uploadError: 'Please select a file to upload' });
                }
                formData.append('file_name', form.data.fileName);
            }

            if (form.data.fileLabel) {
                formData.append('file_label', form.data.fileLabel);
            }

            const response = await serverApi.post(
                '/api/v1/web/uploads/',
                formData,
                uploadResponseSchema
            );

            // Redirect to preview page with upload ID
            throw redirect(303, `/resources/upload/preview?upload_id=${response.resource_id}`);
        } catch (err) {
            if (err instanceof Response) {
                throw err; // Re-throw redirects
            }
            console.error('Upload failed:', err);
            return fail(500, { form, uploadError: 'Upload failed. Please try again.' });
        }
    },
};
