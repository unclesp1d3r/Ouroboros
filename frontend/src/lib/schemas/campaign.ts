import { z } from 'zod';

export const campaignFormSchema = z.object({
    name: z.string().min(1, 'Campaign name is required').max(255, 'Campaign name is too long'),
    description: z.string().nullish(),
    project_id: z.number().int().positive('Project is required'),
    priority: z.number().int().min(0, 'Priority must be non-negative').default(0),
    hash_list_id: z.number().int().positive('Hash list is required'),
    is_unavailable: z.boolean().default(false),
});

export type CampaignFormData = z.infer<typeof campaignFormSchema>;
