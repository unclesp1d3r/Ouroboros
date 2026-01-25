import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import UserProfile from './UserProfile.svelte';
import type { User } from '$lib/types/user';

// Mock the toast utility
vi.mock('$lib/utils/toast', () => ({
    toast: {
        success: vi.fn(),
        error: vi.fn(),
    },
}));

const mockUser: User = {
    id: '1',
    email: 'test@example.com',
    name: 'Test User',
    is_active: true,
    is_superuser: false,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-02T00:00:00Z',
    role: 'user',
};

describe('UserProfile', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        global.fetch = vi.fn();
    });

    it('renders user profile information', () => {
        render(UserProfile, { props: { user: mockUser } });

        expect(screen.getByText('Profile Details')).toBeInTheDocument();
        expect(screen.getByText('test@example.com')).toBeInTheDocument();
        expect(screen.getByText('Test User')).toBeInTheDocument();
        expect(screen.getByText('Active')).toBeInTheDocument();
        expect(screen.getByText('user')).toBeInTheDocument();
    });

    it('displays superuser badge when user is superuser', () => {
        const superUser = { ...mockUser, is_superuser: true };
        render(UserProfile, { props: { user: superUser } });

        expect(screen.getByText('Superuser')).toBeInTheDocument();
    });

    it('displays inactive status when user is not active', () => {
        const inactiveUser = { ...mockUser, is_active: false };
        render(UserProfile, { props: { user: inactiveUser } });

        expect(screen.getByText('Inactive')).toBeInTheDocument();
    });

    it('renders password change form', () => {
        render(UserProfile, { props: { user: mockUser } });

        // Look for the card title instead of a heading
        expect(screen.getAllByText('Change Password')).toHaveLength(2); // Title and button
        expect(screen.getByLabelText('Current Password')).toBeInTheDocument();
        expect(screen.getByLabelText('New Password')).toBeInTheDocument();
        expect(screen.getByLabelText('Confirm New Password')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Change Password' })).toBeInTheDocument();
    });

    it('validates password confirmation match', async () => {
        render(UserProfile, { props: { user: mockUser } });

        const oldPasswordInput = screen.getByLabelText('Current Password');
        const newPasswordInput = screen.getByLabelText('New Password');
        const confirmPasswordInput = screen.getByLabelText('Confirm New Password');
        const submitButton = screen.getByRole('button', { name: 'Change Password' });

        await fireEvent.input(oldPasswordInput, { target: { value: 'oldpassword' } });
        await fireEvent.input(newPasswordInput, { target: { value: 'newpassword123' } });
        await fireEvent.input(confirmPasswordInput, { target: { value: 'differentpassword' } });
        await fireEvent.click(submitButton);

        expect(screen.getByText('New passwords do not match')).toBeInTheDocument();
    });

    it('validates minimum password length', async () => {
        render(UserProfile, { props: { user: mockUser } });

        const oldPasswordInput = screen.getByLabelText('Current Password');
        const newPasswordInput = screen.getByLabelText('New Password');
        const confirmPasswordInput = screen.getByLabelText('Confirm New Password');
        const submitButton = screen.getByRole('button', { name: 'Change Password' });

        await fireEvent.input(oldPasswordInput, { target: { value: 'oldpassword' } });
        await fireEvent.input(newPasswordInput, { target: { value: 'short' } });
        await fireEvent.input(confirmPasswordInput, { target: { value: 'short' } });
        await fireEvent.click(submitButton);

        expect(
            screen.getByText('New password must be at least 10 characters long')
        ).toBeInTheDocument();
    });

    it('handles successful password change', async () => {
        const mockFetch = vi.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({}),
        });
        global.fetch = mockFetch;

        render(UserProfile, { props: { user: mockUser } });

        const oldPasswordInput = screen.getByLabelText('Current Password');
        const newPasswordInput = screen.getByLabelText('New Password');
        const confirmPasswordInput = screen.getByLabelText('Confirm New Password');
        const submitButton = screen.getByRole('button', { name: 'Change Password' });

        await fireEvent.input(oldPasswordInput, { target: { value: 'oldpassword' } });
        await fireEvent.input(newPasswordInput, { target: { value: 'newpassword123' } });
        await fireEvent.input(confirmPasswordInput, { target: { value: 'newpassword123' } });
        await fireEvent.click(submitButton);

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/v1/web/auth/change_password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    old_password: 'oldpassword',
                    new_password: 'newpassword123',
                    new_password_confirm: 'newpassword123',
                }),
            });
        });
    });

    it('formats dates correctly', () => {
        render(UserProfile, { props: { user: mockUser } });

        // Check that dates are displayed (exact format may vary by locale)
        // Both created_at and updated_at contain 2023, so we expect multiple elements
        const dateElements = screen.getAllByText(/2023/);
        expect(dateElements.length).toBeGreaterThanOrEqual(1);
    });
});
