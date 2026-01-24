import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

// required for svelte5 + jsdom as jsdom does not support matchMedia
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    enumerable: true,
    value: vi.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
    })),
});

// Mock localStorage for mode-watcher and other components
class LocalStorageMock implements Storage {
    private store: Map<string, string> = new Map();

    get length(): number {
        return this.store.size;
    }

    clear(): void {
        this.store.clear();
    }

    getItem(key: string): string | null {
        return this.store.get(key) ?? null;
    }

    key(index: number): string | null {
        const keys = Array.from(this.store.keys());
        return keys[index] ?? null;
    }

    removeItem(key: string): void {
        this.store.delete(key);
    }

    setItem(key: string, value: string): void {
        this.store.set(key, value);
    }

    [Symbol.iterator](): IterableIterator<[string, string]> {
        return this.store.entries();
    }
}

const localStorageMock = new LocalStorageMock();

Object.defineProperty(window, 'localStorage', {
    writable: true,
    enumerable: true,
    configurable: true,
    value: localStorageMock,
});

// TypeScript global augmentation for SvelteKit payload
declare global {
    // eslint-disable-next-line no-var -- TypeScript requires 'var' in declare global
    var __SVELTEKIT_PAYLOAD__: {
        data: Record<string, unknown>;
        status: number;
        error: unknown;
        form: unknown;
        env: Record<string, unknown>;
        assets: string;
        versions: { svelte: string };
    };
}

// Mock SvelteKit's payload for the client runtime
globalThis.__SVELTEKIT_PAYLOAD__ = {
    data: {}, // Empty data object to prevent undefined errors
    status: 200,
    error: null,
    form: null,
    env: {},
    assets: '',
    versions: { svelte: '5' },
};

// add more mocks here if you need them
