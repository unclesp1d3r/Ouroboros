import { z } from 'zod';

export const userUpdateSchema = z.object({
    name: z.string().min(1, 'Name is required').max(100, 'Name must be less than 100 characters'),
    email: z.string().email('Please enter a valid email address'),
    role: z
        .enum(['analyst', 'operator', 'admin'])
        .refine((val) => val !== undefined, { message: 'Please select a role' }),
    is_active: z.boolean().default(true),
});

export type UserUpdateForm = z.infer<typeof userUpdateSchema>;
