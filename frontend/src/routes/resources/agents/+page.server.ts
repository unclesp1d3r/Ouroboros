import { error, type RequestEvent } from '@sveltejs/kit';
import { createSessionServerApi, PaginatedResponseSchema } from '$lib/server/api';
import { z } from 'zod';

// Agent schema matching the backend AgentOut schema
const AgentSchema = z.object({
    id: z.number(),
    host_name: z.string(),
    client_signature: z.string(),
    custom_label: z.string().nullable(),
    state: z.enum(['pending', 'active', 'stopped', 'error', 'offline']),
    enabled: z.boolean(),
    advanced_configuration: z.record(z.string(), z.any()).nullable(),
    devices: z.array(z.string()).nullable(),
    agent_type: z.enum(['physical', 'virtual', 'container']).nullable(),
    operating_system: z.enum(['linux', 'windows', 'macos']),
    created_at: z.string().datetime(),
    updated_at: z.string().datetime(),
    last_seen_at: z.string().datetime().nullable(),
    last_ipaddress: z.string().nullable(),
    projects: z.array(z.any()),
});

const AgentListResponseSchema = PaginatedResponseSchema(AgentSchema);

export type Agent = z.infer<typeof AgentSchema>;
export type AgentListResponse = z.infer<typeof AgentListResponseSchema>;

export const load = async ({ url, cookies }: RequestEvent) => {
    // Test environment detection with mock data fallback
    if (process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST || process.env.CI) {
        const mockAgents: Agent[] = [
            {
                id: 1,
                host_name: 'dev-agent-1',
                client_signature: 'dev-sig-1',
                custom_label: 'Dev Agent 1',
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

    // Extract query parameters for pagination and filtering
    const page = parseInt(url.searchParams.get('page') || '1', 10);
    const pageSize = parseInt(url.searchParams.get('page_size') || '20', 10);
    const search = url.searchParams.get('search') || undefined;
    const state = url.searchParams.get('state') || undefined;

    // Get session cookie for authentication
    const sessionCookie = cookies.get('access_token');
    if (!sessionCookie) {
        throw error(401, 'Authentication required');
    }

    const api = createSessionServerApi(sessionCookie);

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

        // Fetch agents from backend API
        const response = await api.get(
            `/api/v1/web/agents?${params.toString()}`,
            AgentListResponseSchema
        );

        // Transform backend response to match component interface
        return {
            agents: {
                items: response.items.map((item) => ({
                    ...item,
                    projects: item.projects || [], // Ensure projects is always an array
                })),
                page: response.page || page,
                page_size: response.page_size || pageSize,
                total: response.total,
                search: search || null,
                state: state || null,
            },
        };
    } catch (err) {
        console.error('Failed to fetch agents:', err);
        throw error(500, 'Failed to load agents');
    }
};
