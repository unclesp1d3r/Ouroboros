import { render, fireEvent, screen, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import { writable } from 'svelte/store';
import AgentRegisterModal from './AgentRegisterModal.svelte';

describe('AgentRegisterModal', () => {
    const mockOnSubmit = vi.fn().mockImplementation(() => Promise.resolve());

    it('renders the modal when open store is true', () => {
        const open = writable(true);
        render(AgentRegisterModal, { props: { open, onSubmit: mockOnSubmit } });
        expect(screen.getByText('Register New Agent')).toBeInTheDocument();
        expect(screen.getByLabelText('Agent Name')).toBeInTheDocument();
    });

    it('does not render the modal when open store is false', () => {
        const open = writable(false);
        render(AgentRegisterModal, { props: { open, onSubmit: mockOnSubmit } });
        expect(screen.queryByText('Register New Agent')).not.toBeInTheDocument();
    });

    it('updates agentName store on input', async () => {
        const open = writable(true);
        render(AgentRegisterModal, { props: { open, onSubmit: mockOnSubmit } });
        const input = screen.getByLabelText('Agent Name') as HTMLInputElement;
        await fireEvent.input(input, { target: { value: 'Test Agent' } });
        expect(input.value).toBe('Test Agent');
    });

    it('calls onSubmit with agentName when form is submitted', async () => {
        const open = writable(true);
        render(AgentRegisterModal, { props: { open, onSubmit: mockOnSubmit } });
        const input = screen.getByLabelText('Agent Name') as HTMLInputElement;
        await fireEvent.input(input, { target: { value: 'MyAgent' } });
        const submitButton = screen.getByText('Register Agent');
        await fireEvent.click(submitButton);
        expect(mockOnSubmit).toHaveBeenCalledWith({ agentName: 'MyAgent' });
    });

    it('calls onSubmit with undefined agentName if input is empty', async () => {
        const open = writable(true);
        render(AgentRegisterModal, { props: { open, onSubmit: mockOnSubmit } });
        const submitButton = screen.getByText('Register Agent');
        await fireEvent.click(submitButton);
        expect(mockOnSubmit).toHaveBeenCalledWith({ agentName: undefined });
    });

    it('closes the modal on successful submission', async () => {
        const open = writable(true);
        render(AgentRegisterModal, { props: { open, onSubmit: mockOnSubmit } });
        const submitButton = screen.getByText('Register Agent');
        await fireEvent.click(submitButton);
        // Wait for potential async operations in handleSubmit
        await new Promise((resolve) => setTimeout(resolve, 0));
        expect(open.subscribe((value) => expect(value).toBe(false)));
    });

    it('closes the modal when Cancel button is clicked', async () => {
        const open = writable(true);
        render(AgentRegisterModal, { props: { open, onSubmit: mockOnSubmit } });
        const cancelButton = screen.getByText('Cancel');
        await fireEvent.click(cancelButton);
        expect(open.subscribe((value) => expect(value).toBe(false)));
    });

    it('shows loading state and disables buttons during submission', async () => {
        const open = writable(true);

        // Create a deferred promise that we can resolve manually
        let resolvePromise!: (value: unknown) => void;
        const pendingPromise = new Promise((resolve) => {
            resolvePromise = resolve;
        });

        const slowSubmit = vi.fn().mockImplementation(() => pendingPromise);
        render(AgentRegisterModal, { props: { open, onSubmit: slowSubmit } });

        const submitButton = screen.getByText('Register Agent');
        const cancelButton = screen.getByText('Cancel');

        // Verify initial state
        expect(submitButton).not.toBeDisabled();
        expect(cancelButton).not.toBeDisabled();

        // Click submit to start async operation
        await fireEvent.click(submitButton);

        // Wait for loading state to be applied
        await waitFor(() => {
            expect(screen.getByText('Registering...')).toBeInTheDocument();
        });

        // Verify buttons are disabled during loading
        await waitFor(() => {
            expect(submitButton).toBeDisabled();
            expect(cancelButton).toBeDisabled();
        });

        // Resolve the promise to complete submission
        resolvePromise(undefined);

        // Wait for loading state to clear
        await waitFor(() => {
            expect(screen.queryByText('Registering...')).not.toBeInTheDocument();
        });

        // Verify buttons are re-enabled after completion
        await waitFor(() => {
            expect(submitButton).not.toBeDisabled();
            expect(cancelButton).not.toBeDisabled();
        });
    });
});
