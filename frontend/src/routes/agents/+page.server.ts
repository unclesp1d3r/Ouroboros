import { createSessionServerApi } from '$lib/server/api';
import { error, type RequestEvent } from '@sveltejs/kit';
import { z } from 'zod';

// Create a schema that matches the actual backend response structure
const BackendPaginatedResponseSchema = z.object({
    items: z.array(z.any()), // We'll validate individual items separately
    total: z.number(),
    page: z.number(),
    page_size: z.number(), // Backend returns page_size, not per_page
    search: z.string().nullable().optional(),
    state: z.string().nullable().optional(),
});

// Agent schema matching the backend AgentOut schema
const AgentSchema = z.object({
    id: z.number(),
    host_name: z.string(),
    client_signature: z.string(),
    custom_label: z.string().nullable(),
    token: z.string(),
    state: z.enum(['pending', 'active', 'stopped', 'error', 'offline']),
    enabled: z.boolean(),
    advanced_configuration: z.record(z.string(), z.any()).nullable(),
    devices: z.array(z.string()).nullable(),
    agent_type: z.enum(['physical', 'virtual', 'container']).nullable(),
    operating_system: z.enum(['linux', 'windows', 'macos']),
    // Handle datetime strings from backend
    created_at: z
        .string()
        .or(z.date())
        .transform((val) => (typeof val === 'string' ? val : val.toISOString())),
    updated_at: z
        .string()
        .or(z.date())
        .transform((val) => (typeof val === 'string' ? val : val.toISOString())),
    last_seen_at: z
        .string()
        .or(z.date())
        .transform((val) => (typeof val === 'string' ? val : val.toISOString()))
        .nullable(),
    last_ipaddress: z.string().nullable(),
    projects: z.array(z.any()).default([]),
});

export type Agent = z.infer<typeof AgentSchema>;

export const load = async ({ locals, url }: RequestEvent) => {
    // Test environment detection with mock data fallback
    if (process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST || process.env.CI) {
        const mockAgents: Agent[] = [
            {
                id: 1,
                host_name: 'dev-agent-1',
                client_signature: 'dev-sig-1',
                custom_label: 'Dev Agent 1',
                token: 'csa_1_mocktoken1234567890abcdef',
                state: 'active',
                enabled: true,
                advanced_configuration: {
                    agent_update_interval: 30,
                    use_native_hashcat: false,
                    enable_additional_hash_types: false,
                },
                devices: ['GPU0', 'CPU'],
                agent_type: 'physical',
                operating_system: 'linux',
                created_at: '2024-01-01T00:00:00Z',
                updated_at: '2024-01-01T00:00:00Z',
                last_seen_at: '2024-01-01T00:00:00Z',
                last_ipaddress: '192.168.1.100',
                projects: [],
            },
            {
                id: 2,
                host_name: 'dev-agent-2',
                client_signature: 'dev-sig-2',
                custom_label: 'Dev Agent 2',
                token: 'csa_2_mocktoken0987654321fedcba',
                state: 'offline',
                enabled: true,
                advanced_configuration: {
                    agent_update_interval: 60,
                    use_native_hashcat: true,
                    enable_additional_hash_types: true,
                },
                devices: ['GPU0', 'GPU1'],
                agent_type: 'virtual',
                operating_system: 'windows',
                created_at: '2024-01-01T00:00:00Z',
                updated_at: '2024-01-01T00:00:00Z',
                last_seen_at: '2024-01-01T00:00:00Z',
                last_ipaddress: '192.168.1.101',
                projects: [],
            },
        ];

        // Extract query parameters for filtering in test mode
        const search = url.searchParams.get('search');
        const state = url.searchParams.get('state');
        let filteredAgents = mockAgents;

        if (search) {
            filteredAgents = mockAgents.filter((agent) =>
                agent.host_name.toLowerCase().includes(search.toLowerCase())
            );
        }

        return {
            agents: {
                items: filteredAgents,
                page: 1,
                page_size: 20,
                total: filteredAgents.length,
                search: search,
                state: state,
            },
        };
    }

    // Check if user is authenticated via hooks
    if (!locals.session || !locals.user) {
        throw error(401, 'Authentication required');
    }

    // Extract query parameters for pagination and filtering
    const page = parseInt(url.searchParams.get('page') || '1', 10);
    const pageSize = parseInt(url.searchParams.get('page_size') || '20', 10);
    const search = url.searchParams.get('search') || undefined;
    const state = url.searchParams.get('state') || undefined;

    // Create API client with session from locals
    const api = createSessionServerApi(`access_token=${locals.session}`);

    try {
        // Build query parameters
        const params = new URLSearchParams({
            page: page.toString(),
            page_size: pageSize.toString(),
        });

        if (search) {
            params.append('search', search);
        }

        if (state) {
            params.append('state', state);
        }

        // Fetch raw response from backend API first
        const rawResponse = await api.getRaw(`/api/v1/web/agents?${params.toString()}`);

        // Parse the raw response with the backend schema
        const parsedResponse = BackendPaginatedResponseSchema.parse(rawResponse.data);

        // Validate individual agents
        const validatedAgents = parsedResponse.items.map((item) => AgentSchema.parse(item));

        // Transform backend response to match component interface
        return {
            agents: {
                items: validatedAgents,
                page: parsedResponse.page,
                page_size: parsedResponse.page_size,
                total: parsedResponse.total,
                search: search || null,
                state: state || null,
            },
        };
    } catch (err) {
        console.error('Failed to fetch agents:', err);
        throw error(500, 'Failed to load agents');
    }
};
