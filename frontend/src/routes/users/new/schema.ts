import { z } from 'zod';

export const userCreateSchema = z.object({
    name: z.string().min(1, 'Name is required').max(100, 'Name must be less than 100 characters'),
    email: z.string().email('Please enter a valid email address'),
    password: z
        .string()
        .min(8, 'Password must be at least 8 characters')
        .max(128, 'Password must be less than 128 characters'),
    role: z
        .enum(['analyst', 'operator', 'admin'])
        .refine((val) => val !== undefined, { message: 'Please select a role' }),
});

export type UserCreateForm = z.infer<typeof userCreateSchema>;
