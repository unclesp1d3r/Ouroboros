import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock svelte-sonner before importing the module
vi.mock('svelte-sonner', () => ({
    toast: {
        success: vi.fn(),
        error: vi.fn(),
        warning: vi.fn(),
        info: vi.fn(),
    },
}));

// Import after mocking
import {
    showSuccess,
    showError,
    showInfo,
    showWarning,
    showHashCracked,
    showBatchHashesCracked,
    showAgentStatus,
    showCampaignStatus,
} from './toast';
import { toast } from 'svelte-sonner';

describe('Toast Utilities', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('Basic toast functions', () => {
        it('showSuccess calls toast.success with correct parameters', () => {
            showSuccess('Success message');

            expect(toast.success).toHaveBeenCalledWith('Success message', {
                duration: 5000,
                description: undefined,
                action: undefined,
            });
        });

        it('showError calls toast.error with longer duration', () => {
            showError('Error message');

            expect(toast.error).toHaveBeenCalledWith('Error message', {
                duration: 8000,
                description: undefined,
                action: undefined,
            });
        });

        it('showInfo calls toast.info with correct parameters', () => {
            showInfo('Info message');

            expect(toast.info).toHaveBeenCalledWith('Info message', {
                duration: 5000,
                description: undefined,
                action: undefined,
            });
        });

        it('showWarning calls toast.warning with correct parameters', () => {
            showWarning('Warning message');

            expect(toast.warning).toHaveBeenCalledWith('Warning message', {
                duration: 6000,
                description: undefined,
                action: undefined,
            });
        });

        it('accepts custom options', () => {
            const options = {
                duration: 10000,
                description: 'Custom description',
                action: {
                    label: 'Action',
                    onClick: vi.fn(),
                },
            };

            showSuccess('Message with options', options);

            expect(toast.success).toHaveBeenCalledWith('Message with options', options);
        });
    });

    describe('Ouroboros-specific toast functions', () => {
        it('showHashCracked handles single hash', () => {
            showHashCracked(1, 'test-hashlist', 'dictionary-attack');

            expect(toast.success).toHaveBeenCalledWith('Hash cracked!', {
                description: 'test-hashlist • dictionary-attack',
                duration: 8000,
            });
        });

        it('showHashCracked handles multiple hashes', () => {
            showHashCracked(5, 'test-hashlist', 'mask-attack');

            expect(toast.success).toHaveBeenCalledWith('5 hashes cracked!', {
                description: 'test-hashlist • mask-attack',
                duration: 8000,
            });
        });

        it('showBatchHashesCracked formats message correctly', () => {
            showBatchHashesCracked(25, 'large-hashlist');

            expect(toast.success).toHaveBeenCalledWith('25 new hashes cracked!', {
                description: 'View results in large-hashlist',
                duration: 10000,
            });
        });

        it('showAgentStatus handles online status', () => {
            showAgentStatus('agent-001', 'online');

            expect(toast.success).toHaveBeenCalledWith('Agent agent-001 is now online', {
                duration: 5000,
                description: undefined,
                action: undefined,
            });
        });

        it('showAgentStatus handles offline status', () => {
            showAgentStatus('agent-002', 'offline');

            expect(toast.warning).toHaveBeenCalledWith('Agent agent-002 went offline', {
                duration: 6000,
                description: undefined,
                action: undefined,
            });
        });

        it('showAgentStatus handles error status', () => {
            showAgentStatus('agent-003', 'error');

            expect(toast.error).toHaveBeenCalledWith('Agent agent-003 encountered an error', {
                duration: 8000,
                description: undefined,
                action: undefined,
            });
        });

        it('showCampaignStatus handles started status', () => {
            showCampaignStatus('test-campaign', 'started');

            expect(toast.info).toHaveBeenCalledWith('Campaign "test-campaign" started', {
                duration: 5000,
                description: undefined,
                action: undefined,
            });
        });

        it('showCampaignStatus handles completed status', () => {
            showCampaignStatus('test-campaign', 'completed');

            expect(toast.success).toHaveBeenCalledWith('Campaign "test-campaign" completed', {
                duration: 5000,
                description: undefined,
                action: undefined,
            });
        });

        it('showCampaignStatus handles paused status', () => {
            showCampaignStatus('test-campaign', 'paused');

            expect(toast.warning).toHaveBeenCalledWith('Campaign "test-campaign" paused', {
                duration: 6000,
                description: undefined,
                action: undefined,
            });
        });

        it('showCampaignStatus handles error status', () => {
            showCampaignStatus('test-campaign', 'error');

            expect(toast.error).toHaveBeenCalledWith(
                'Campaign "test-campaign" encountered an error',
                {
                    duration: 8000,
                    description: undefined,
                    action: undefined,
                }
            );
        });

        it('accepts custom options for specialized functions', () => {
            const customOptions = {
                duration: 15000,
                action: {
                    label: 'View Details',
                    onClick: vi.fn(),
                },
            };

            showHashCracked(3, 'test-list', 'test-attack', customOptions);

            expect(toast.success).toHaveBeenCalledWith('3 hashes cracked!', {
                description: 'test-list • test-attack',
                duration: 15000,
                action: customOptions.action,
            });
        });
    });
});
