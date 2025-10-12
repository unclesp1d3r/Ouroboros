import { toast } from 'svelte-sonner';

// Re-export the toast function for direct use
export { toast };

export interface ToastOptions {
    duration?: number;
    description?: string;
    action?: {
        label: string;
        onClick: () => void;
    };
}

/**
 * Show a success toast notification
 */
export function showSuccess(message: string, options?: ToastOptions) {
    return toast.success(message, {
        duration: options?.duration ?? 5000,
        description: options?.description,
        action: options?.action,
    });
}

/**
 * Show an error toast notification
 */
export function showError(message: string, options?: ToastOptions) {
    return toast.error(message, {
        duration: options?.duration ?? 8000, // Longer duration for errors
        description: options?.description,
        action: options?.action,
    });
}

/**
 * Show an info toast notification
 */
export function showInfo(message: string, options?: ToastOptions) {
    return toast.info(message, {
        duration: options?.duration ?? 5000,
        description: options?.description,
        action: options?.action,
    });
}

/**
 * Show a warning toast notification
 */
export function showWarning(message: string, options?: ToastOptions) {
    return toast.warning(message, {
        duration: options?.duration ?? 6000,
        description: options?.description,
        action: options?.action,
    });
}

/**
 * Show a hash cracking notification (specialized for Ouroboros)
 */
export function showHashCracked(
    count: number,
    hashlistName: string,
    attackName: string,
    options?: Omit<ToastOptions, 'description'>
) {
    const message = count === 1 ? 'Hash cracked!' : `${count} hashes cracked!`;
    const description = `${hashlistName} • ${attackName}`;

    return showSuccess(message, {
        ...options,
        description,
        duration: options?.duration ?? 8000, // Longer for important events
    });
}

/**
 * Show a batch hash cracking notification
 */
export function showBatchHashesCracked(
    count: number,
    hashlistName: string,
    options?: Omit<ToastOptions, 'description'>
) {
    const message = `${count} new hashes cracked!`;
    const description = `View results in ${hashlistName}`;

    return showSuccess(message, {
        ...options,
        description,
        duration: options?.duration ?? 10000,
    });
}

/**
 * Show an agent status notification
 */
export function showAgentStatus(
    agentName: string,
    status: 'online' | 'offline' | 'error',
    options?: ToastOptions
) {
    const messages = {
        online: `Agent ${agentName} is now online`,
        offline: `Agent ${agentName} went offline`,
        error: `Agent ${agentName} encountered an error`,
    };

    const message = messages[status];

    switch (status) {
        case 'online':
            return showSuccess(message, options);
        case 'offline':
            return showWarning(message, options);
        case 'error':
            return showError(message, options);
    }
}

/**
 * Show a campaign status notification
 */
export function showCampaignStatus(
    campaignName: string,
    status: 'started' | 'completed' | 'paused' | 'error',
    options?: ToastOptions
) {
    const messages = {
        started: `Campaign "${campaignName}" started`,
        completed: `Campaign "${campaignName}" completed`,
        paused: `Campaign "${campaignName}" paused`,
        error: `Campaign "${campaignName}" encountered an error`,
    };

    const message = messages[status];

    switch (status) {
        case 'started':
            return showInfo(message, options);
        case 'completed':
            return showSuccess(message, options);
        case 'paused':
            return showWarning(message, options);
        case 'error':
            return showError(message, options);
    }
}
