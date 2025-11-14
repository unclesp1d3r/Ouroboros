import { z } from 'zod';

// Base attack schema with common fields
const baseAttackSchema = z.object({
    name: z.string().min(1, 'Attack name is required').max(255, 'Attack name too long'),
    comment: z.string().nullish(),
    attack_mode: z
        .enum(['dictionary', 'mask', 'brute_force'])
        .refine((val) => val !== undefined, { message: 'Attack mode is required' }),
});

// Dictionary attack specific schema
const dictionaryAttackSchema = baseAttackSchema.extend({
    attack_mode: z.literal('dictionary'),
    min_length: z.number().int().min(1).max(128).default(1),
    max_length: z.number().int().min(1).max(128).default(32),
    wordlist_source: z.enum(['existing', 'previous_passwords']).default('existing'),
    word_list_id: z.string().nullish(),
    rule_list_id: z.string().nullish(),
    modifiers: z.array(z.string()).default([]),
    wordlist_inline: z.array(z.string()).default([]),
    use_previous_passwords: z.boolean().nullish(),
    // Wizard-specific fields for multiple resource selection
    wordlists: z.array(z.string()).default([]),
    rulelists: z.array(z.string()).default([]),
});

// Mask attack specific schema
const maskAttackSchema = baseAttackSchema.extend({
    attack_mode: z.literal('mask'),
    mask: z.string().nullish(),
    language: z.string().default('english'),
    masks_inline: z.array(z.string()).default([]),
    custom_charset_1: z.string().nullish(),
    custom_charset_2: z.string().nullish(),
    custom_charset_3: z.string().nullish(),
    custom_charset_4: z.string().nullish(),
    // Wizard-specific fields
    mask_patterns: z.array(z.string()).default([]),
    custom_charsets: z.array(z.string()).default([]),
    mask_language: z.string().default('en'),
});

// Brute force attack specific schema
const bruteForceAttackSchema = baseAttackSchema.extend({
    attack_mode: z.literal('brute_force'),
    increment_minimum: z.number().int().min(1).max(64).default(1),
    increment_maximum: z.number().int().min(1).max(64).default(8),
    charset_lowercase: z.boolean().default(true),
    charset_uppercase: z.boolean().default(true),
    charset_digits: z.boolean().default(true),
    charset_special: z.boolean().default(true),
    increment_mode: z.boolean().default(true),
    // Wizard-specific fields
    character_sets: z.array(z.string()).default([]),
    increment_min: z.number().int().min(1).max(64).default(1),
    increment_max: z.number().int().min(1).max(64).default(8),
});

// Union schema for all attack types
export const attackSchema = z.discriminatedUnion('attack_mode', [
    dictionaryAttackSchema,
    maskAttackSchema,
    bruteForceAttackSchema,
]);

// Individual schemas for type-specific validation
export const dictionarySchema = dictionaryAttackSchema;
export const maskSchema = maskAttackSchema;
export const bruteForceSchema = bruteForceAttackSchema;

// Type exports
export type AttackFormData = z.infer<typeof attackSchema>;
export type DictionaryAttackData = z.infer<typeof dictionarySchema>;
export type MaskAttackData = z.infer<typeof maskSchema>;
export type BruteForceAttackData = z.infer<typeof bruteForceSchema>;

// Helper function to get schema for specific attack mode
export function getAttackSchemaForMode(mode: string) {
    switch (mode) {
        case 'dictionary':
            return dictionarySchema;
        case 'mask':
            return maskSchema;
        case 'brute_force':
            return bruteForceSchema;
        default:
            return attackSchema;
    }
}

// Helper function to convert form data to API format
export function convertAttackDataToApi(data: AttackFormData) {
    const baseData = {
        name: data.name,
        comment: data.comment,
        attack_mode: data.attack_mode,
        attack_mode_hashcat: getHashcatMode(data.attack_mode),
    };

    if (data.attack_mode === 'dictionary') {
        return {
            ...baseData,
            min_length: data.min_length,
            max_length: data.max_length,
            ...(data.wordlist_source === 'existing' &&
                data.word_list_id && { word_list_id: data.word_list_id }),
            ...(data.wordlist_source === 'previous_passwords' && { use_previous_passwords: true }),
            ...(data.wordlist_inline.filter((w) => w.trim()).length > 0 && {
                wordlist_inline: data.wordlist_inline.filter((w) => w.trim()),
            }),
            ...(data.rule_list_id && { rule_list_id: data.rule_list_id }),
            ...(data.modifiers.length > 0 && { modifiers: data.modifiers }),
        };
    } else if (data.attack_mode === 'mask') {
        return {
            ...baseData,
            ...(data.mask && { mask: data.mask }),
            language: data.language,
            ...(data.masks_inline.filter((m) => m.trim()).length > 0 && {
                masks_inline: data.masks_inline.filter((m) => m.trim()),
            }),
            ...(data.custom_charset_1 && { custom_charset_1: data.custom_charset_1 }),
            ...(data.custom_charset_2 && { custom_charset_2: data.custom_charset_2 }),
            ...(data.custom_charset_3 && { custom_charset_3: data.custom_charset_3 }),
            ...(data.custom_charset_4 && { custom_charset_4: data.custom_charset_4 }),
        };
    } else if (data.attack_mode === 'brute_force') {
        const charset = buildCharset(
            data.charset_lowercase,
            data.charset_uppercase,
            data.charset_digits,
            data.charset_special
        );
        const mask = '?1'.repeat(data.increment_maximum);

        return {
            ...baseData,
            increment_mode: true,
            increment_minimum: data.increment_minimum,
            increment_maximum: data.increment_maximum,
            mask,
            custom_charset_1: charset,
        };
    }

    return baseData;
}

// Helper function to get hashcat mode number
function getHashcatMode(attackMode: string): number {
    switch (attackMode) {
        case 'dictionary':
            return 0;
        case 'mask':
        case 'brute_force':
            return 3;
        default:
            return 0;
    }
}

// Helper function to build charset for brute force
function buildCharset(
    lowercase: boolean,
    uppercase: boolean,
    digits: boolean,
    special: boolean
): string {
    let charset = '';
    if (lowercase) charset += '?l';
    if (uppercase) charset += '?u';
    if (digits) charset += '?d';
    if (special) charset += '?s';
    return charset;
}
