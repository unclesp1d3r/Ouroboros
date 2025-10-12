/**
 * Agent schemas for Ouroboros
 * Used by /api/v1/web/agents/* endpoints
 * Based on authoritative backend API schema
 */

import { z } from 'zod';
import { AgentState, AgentType, OperatingSystemEnum } from './base';

// Core agent schemas
/**
 * Agent output schema
 * Complete agent information including configuration and status
 */
export const AgentOut = z.object({
    id: z.number().int().describe('Agent ID'),
    host_name: z.string().describe('Agent hostname'),
    client_signature: z.string().describe('Client signature for identification'),
    custom_label: z.string().nullish().describe('Custom label for the agent'),
    token: z.string().describe('Agent authentication token'),
    state: AgentState.describe('Current agent state'),
    enabled: z.boolean().describe('Whether the agent is enabled'),
    advanced_configuration: z
        .union([z.record(z.unknown()), z.null()])
        .nullish()
        .describe('Advanced configuration settings'),
    devices: z
        .union([z.array(z.string()), z.null()])
        .nullish()
        .describe('Available compute devices'),
    agent_type: AgentType.nullish().describe('Agent type'),
    operating_system: OperatingSystemEnum.describe('Operating system'),
    created_at: z.string().datetime().describe('Creation timestamp'),
    updated_at: z.string().datetime().describe('Last update timestamp'),
    last_seen_at: z
        .union([z.string().datetime(), z.null()])
        .nullish()
        .describe('Last seen timestamp'),
    last_ipaddress: z.string().nullish().describe('Last IP address'),
    projects: z.array(z.unknown()).default([]).describe('Projects associated with the agent'),
});
export type AgentOut = z.infer<typeof AgentOut>;

/**
 * Agent list output schema
 * Paginated list of agents with search and filtering
 */
export const AgentListOut = z.object({
    items: z.array(AgentOut).describe('List of agents'),
    total: z.number().int().describe('Total number of agents'),
    page: z.number().int().min(1).max(100).default(1).describe('Current page number'),
    page_size: z.number().int().min(1).max(100).default(20).describe('Number of items per page'),
    search: z.string().nullish().describe('Search query'),
    state: z.string().nullish().describe('Filter by agent state'),
});
export type AgentListOut = z.infer<typeof AgentListOut>;

/**
 * Agent dropdown item schema
 * Minimal agent information for dropdown selections
 */
export const AgentDropdownItem = z.object({
    id: z.number().int().describe('Agent ID'),
    display_name: z
        .string()
        .describe(
            'Agent display name, either custom_label or host_name if custom_label is not set'
        ),
    state: AgentState.describe('Agent state, either active, stopped, error, or offline'),
});
export type AgentDropdownItem = z.infer<typeof AgentDropdownItem>;

// Agent configuration schemas
/**
 * Advanced agent configuration schema
 * Detailed configuration options for agent behavior and performance
 */
export const AdvancedAgentConfiguration = z.object({
    agent_update_interval: z
        .number()
        .int()
        .nullish()
        .describe('The interval in seconds to check for agent updates'),
    use_native_hashcat: z
        .boolean()
        .nullish()
        .describe('Use the hashcat binary already installed on the client system'),
    backend_device: z
        .string()
        .nullish()
        .describe('The device to use for hashcat, separated by commas'),
    opencl_devices: z
        .string()
        .nullish()
        .describe('The OpenCL device types to use for hashcat, separated by commas'),
    enable_additional_hash_types: z
        .boolean()
        .describe('Causes hashcat to perform benchmark-all, rather than just benchmark'),
    hwmon_temp_abort: z
        .number()
        .int()
        .nullish()
        .describe('Temperature abort threshold in Celsius for hashcat (--hwmon-temp-abort)'),
    backend_ignore_cuda: z
        .boolean()
        .nullish()
        .describe('Ignore CUDA backend (--backend-ignore-cuda)'),
    backend_ignore_opencl: z
        .boolean()
        .nullish()
        .describe('Ignore OpenCL backend (--backend-ignore-opencl)'),
    backend_ignore_hip: z.boolean().nullish().describe('Ignore HIP backend (--backend-ignore-hip)'),
    backend_ignore_metal: z
        .boolean()
        .nullish()
        .describe('Ignore Metal backend (--backend-ignore-metal)'),
});
export type AdvancedAgentConfiguration = z.infer<typeof AdvancedAgentConfiguration>;

// Agent health and monitoring
/**
 * Agent health summary schema
 * Health status and metrics for the agent system
 */
export const AgentHealthSummary = z.object({
    total_agents: z.number().int().describe('Total number of agents'),
    online_agents: z.number().int().describe('Number of agents online (last seen <2min)'),
    total_campaigns: z.number().int().describe('Total number of campaigns'),
    total_tasks: z.number().int().describe('Total number of tasks'),
    total_hashlists: z.number().int().describe('Total number of hash lists'),
});
export type AgentHealthSummary = z.infer<typeof AgentHealthSummary>;

/**
 * Agent error log output schema
 * Error log entries for agent troubleshooting
 */
export const AgentErrorLogOut = z.object({
    errors: z.array(z.unknown()).describe('List of error entries'),
});
export type AgentErrorLogOut = z.infer<typeof AgentErrorLogOut>;

// Performance monitoring
/**
 * Device performance point schema
 * Single performance measurement point
 */
export const DevicePerformancePoint = z.object({
    timestamp: z.string().datetime().describe('Measurement timestamp'),
    value: z.number().describe('Performance value'),
});
export type DevicePerformancePoint = z.infer<typeof DevicePerformancePoint>;

/**
 * Device performance series schema
 * Time series performance data for a device
 */
export const DevicePerformanceSeries = z.object({
    device_name: z.string().describe('Device name'),
    data: z.array(DevicePerformancePoint).describe('Performance data points'),
});
export type DevicePerformanceSeries = z.infer<typeof DevicePerformanceSeries>;

/**
 * Agent performance series output schema
 * Performance time series data for an agent
 */
export const AgentPerformanceSeriesOut = z.object({
    series: z.array(DevicePerformanceSeries).describe('Performance series for each device'),
});
export type AgentPerformanceSeriesOut = z.infer<typeof AgentPerformanceSeriesOut>;

// Agent testing and validation
/**
 * Agent presigned URL test request schema
 * Request to test agent access to presigned URLs
 */
export const AgentPresignedUrlTestRequest = z.object({
    url: z.string().url().min(1).describe('The presigned S3/MinIO URL to test'),
});
export type AgentPresignedUrlTestRequest = z.infer<typeof AgentPresignedUrlTestRequest>;

/**
 * Agent presigned URL test response schema
 * Result of presigned URL test
 */
export const AgentPresignedUrlTestResponse = z.object({
    valid: z.boolean().describe('Whether the URL is valid and accessible'),
});
export type AgentPresignedUrlTestResponse = z.infer<typeof AgentPresignedUrlTestResponse>;

// Agent registration
/**
 * Agent register modal context schema
 * Context information for agent registration modal
 */
export const AgentRegisterModalContext = z.object({
    agent: AgentOut.describe('Registered agent information'),
    token: z.string().describe('Agent authentication token'),
});
export type AgentRegisterModalContext = z.infer<typeof AgentRegisterModalContext>;

// Agent update operations
/**
 * Agent toggle enabled output schema
 * Response for toggling agent enabled state
 */
export const AgentToggleEnabledOut = z.object({
    success: z.boolean().describe('Whether the operation was successful'),
    enabled: z.boolean().describe('New enabled state'),
});
export type AgentToggleEnabledOut = z.infer<typeof AgentToggleEnabledOut>;

/**
 * Agent update config output schema
 * Response for updating agent configuration
 */
export const AgentUpdateConfigOut = z.object({
    success: z.boolean().describe('Whether the operation was successful'),
    config: AdvancedAgentConfiguration.describe('Updated configuration'),
});
export type AgentUpdateConfigOut = z.infer<typeof AgentUpdateConfigOut>;

/**
 * Agent update devices output schema
 * Response for updating agent devices
 */
export const AgentUpdateDevicesOut = z.object({
    success: z.boolean().describe('Whether the operation was successful'),
    devices: z.array(z.string()).describe('Updated device list'),
});
export type AgentUpdateDevicesOut = z.infer<typeof AgentUpdateDevicesOut>;

/**
 * Agent update hardware output schema
 * Response for updating agent hardware information
 */
export const AgentUpdateHardwareOut = z.object({
    success: z.boolean().describe('Whether the operation was successful'),
    hardware: z.record(z.unknown()).describe('Updated hardware information'),
});
export type AgentUpdateHardwareOut = z.infer<typeof AgentUpdateHardwareOut>;

// Request body schemas for API endpoints
/**
 * Register agent request body schema
 * Body for POST /api/v1/web/agents
 */
export const Body_register_agent_api_v1_web_agents_post = z.object({
    host_name: z.string().describe('Agent hostname'),
    custom_label: z.string().nullish().describe('Custom label for the agent'),
});
export type Body_register_agent_api_v1_web_agents_post = z.infer<
    typeof Body_register_agent_api_v1_web_agents_post
>;

/**
 * Test agent presigned URL request body schema
 * Body for POST /api/v1/web/agents/{agent_id}/test_presigned
 */
export const Body_test_agent_presigned_url_api_v1_web_agents__agent_id__test_presigned_post =
    AgentPresignedUrlTestRequest;
export type Body_test_agent_presigned_url_api_v1_web_agents__agent_id__test_presigned_post =
    z.infer<typeof Body_test_agent_presigned_url_api_v1_web_agents__agent_id__test_presigned_post>;

/**
 * Toggle agent devices request body schema
 * Body for PATCH /api/v1/web/agents/{agent_id}/devices
 */
export const Body_toggle_agent_devices_api_v1_web_agents__agent_id__devices_patch = z.object({
    devices: z.array(z.string()).describe('List of device identifiers'),
});
export type Body_toggle_agent_devices_api_v1_web_agents__agent_id__devices_patch = z.infer<
    typeof Body_toggle_agent_devices_api_v1_web_agents__agent_id__devices_patch
>;

/**
 * Update agent config request body schema
 * Body for PATCH /api/v1/web/agents/{agent_id}/config
 */
export const Body_update_agent_config_api_v1_web_agents__agent_id__config_patch = z.object({
    config: AdvancedAgentConfiguration.describe('Updated agent configuration'),
});
export type Body_update_agent_config_api_v1_web_agents__agent_id__config_patch = z.infer<
    typeof Body_update_agent_config_api_v1_web_agents__agent_id__config_patch
>;

/**
 * Update agent hardware request body schema
 * Body for PATCH /api/v1/web/agents/{agent_id}/hardware
 */
export const Body_update_agent_hardware_api_v1_web_agents__agent_id__hardware_patch = z.object({
    hardware: z.record(z.unknown()).describe('Hardware information'),
});
export type Body_update_agent_hardware_api_v1_web_agents__agent_id__hardware_patch = z.infer<
    typeof Body_update_agent_hardware_api_v1_web_agents__agent_id__hardware_patch
>;
