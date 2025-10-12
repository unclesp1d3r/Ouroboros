<script lang="ts">
    import { page } from '$app/stores';
    import { enhance } from '$app/forms';
    import { superForm } from 'sveltekit-superforms';
    import { zod4Client } from 'sveltekit-superforms/adapters';
    import { toast } from 'svelte-sonner';
    import { Field, Control, Label, FieldErrors, Description } from 'formsnap';
    import { Button } from '$lib/components/ui/button';
    import {
        Card,
        CardContent,
        CardDescription,
        CardHeader,
        CardTitle,
    } from '$lib/components/ui/card';
    import { Input } from '$lib/components/ui/input';
    import { Textarea } from '$lib/components/ui/textarea';
    import { Badge } from '$lib/components/ui/badge';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
    import { FileDropZone } from '$lib/components/ui/file-drop-zone';
    import { uploadSchema } from './schema';
    import type { HashGuessResults, HashTypeDropdownItem, UploadResponse } from './schema';
    import type { PageData } from './$types';

    let { data }: { data: PageData } = $props();

    // Initialize superform with proper Formsnap integration
    const form = superForm(data.form, {
        validators: zod4Client(uploadSchema),
        onUpdated: ({ form }) => {
            if (form.valid) {
                toast.success('Upload completed successfully!');
            } else {
                toast.error('Please fix the errors in the form.');
            }
        },
    });

    const { form: formData, errors, enhance: formEnhance, submitting } = form;

    // State for upload functionality
    let selectedFiles = $state<File[]>([]);
    let hashGuessResults = $state<HashGuessResults | null>(null);
    let hashTypes = $state<HashTypeDropdownItem[]>([]);
    let isValidating = $state(false);

    // Handle file selection from FileDropZone
    async function handleFilesSelected(files: File[]) {
        selectedFiles = files;
        if (files.length > 0) {
            formData.update((data) => ({
                ...data,
                uploadMode: 'file',
                fileName: files[0].name,
            }));
        }
    }

    // Handle file rejection
    function handleFileRejected({ reason, file }: { reason: string; file: File }) {
        toast.error(`File rejected: ${reason}`);
    }

    // Validate hash content
    async function validateHashes() {
        isValidating = true;
        try {
            const content =
                $formData.uploadMode === 'file'
                    ? await selectedFiles[0]?.text()
                    : $formData.textContent;

            if (!content) {
                toast.error('No content to validate');
                return;
            }

            const response = await fetch('?/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({
                    uploadMode: $formData.uploadMode,
                    textContent: content,
                    projectId: $formData.projectId.toString(),
                }),
            });

            const result = await response.json();
            if (result.type === 'success' && result.data) {
                hashGuessResults = result.data.hashGuessResults;
                hashTypes = result.data.hashTypes;
                toast.success('Hash validation completed');
            } else {
                toast.error('Validation failed');
            }
        } catch (error) {
            toast.error('Validation error occurred');
        } finally {
            isValidating = false;
        }
    }

    // Handle upload mode change
    function handleUploadModeChange() {
        // Reset file selection when switching modes
        if ($formData.uploadMode === 'text') {
            selectedFiles = [];
        }
        // Reset hash validation results
        hashGuessResults = null;
        hashTypes = [];
    }

    // Reactive effect for upload mode changes
    $effect(() => {
        handleUploadModeChange();
    });
</script>

<svelte:head>
    <title>Upload Resource - Ouroboros</title>
</svelte:head>

<div class="container mx-auto py-8">
    <div class="mx-auto max-w-4xl">
        <div class="mb-8">
            <h1 class="text-3xl font-bold">Upload Resource</h1>
            <p class="text-muted-foreground">
                Upload hash lists, wordlists, rules, or other resources for use in attacks.
            </p>
        </div>

        <form method="POST" action="?/upload" use:formEnhance class="space-y-6">
            <!-- Project Selection -->
            <Card>
                <CardHeader>
                    <CardTitle>Project</CardTitle>
                    <CardDescription>Select the project for this resource</CardDescription>
                </CardHeader>
                <CardContent>
                    <Field {form} name="projectId">
                        <Control>
                            {#snippet children({ props })}
                                <Label>Project</Label>
                                <Input
                                    {...props}
                                    type="number"
                                    bind:value={$formData.projectId}
                                    placeholder="Enter project ID" />
                            {/snippet}
                        </Control>
                        <FieldErrors />
                    </Field>
                </CardContent>
            </Card>

            <!-- Upload Mode Selection -->
            <Card>
                <CardHeader>
                    <CardTitle>Upload Method</CardTitle>
                    <CardDescription>Choose how to provide your content</CardDescription>
                </CardHeader>
                <CardContent>
                    <Field {form} name="uploadMode">
                        <Control>
                            {#snippet children({ props })}
                                <Label>Upload Mode</Label>
                                <div class="flex gap-4">
                                    <label class="flex items-center gap-2">
                                        <input
                                            {...props}
                                            type="radio"
                                            value="text"
                                            bind:group={$formData.uploadMode} />
                                        <span>Paste Text</span>
                                    </label>
                                    <label class="flex items-center gap-2">
                                        <input
                                            {...props}
                                            type="radio"
                                            value="file"
                                            bind:group={$formData.uploadMode} />
                                        <span>Upload File</span>
                                    </label>
                                </div>
                            {/snippet}
                        </Control>
                        <FieldErrors />
                    </Field>
                </CardContent>
            </Card>

            <!-- Content Input -->
            <Card>
                <CardHeader>
                    <CardTitle>Content</CardTitle>
                    <CardDescription>
                        {$formData.uploadMode === 'file'
                            ? 'Drop files here or click to select'
                            : 'Paste your content below'}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {#if $formData.uploadMode === 'text'}
                        <Field {form} name="textContent">
                            <Control>
                                {#snippet children({ props })}
                                    <Label>Content</Label>
                                    <Textarea
                                        {...props}
                                        bind:value={$formData.textContent}
                                        placeholder="Paste your hashes, wordlist, or rules here..."
                                        rows={10}
                                        class="font-mono" />
                                {/snippet}
                            </Control>
                            <Description>Paste the content you want to upload</Description>
                            <FieldErrors />
                        </Field>
                    {:else}
                        <FileDropZone
                            accept=".txt,.lst,.dict,.rule"
                            maxFiles={1}
                            onUpload={handleFilesSelected}
                            onFileRejected={handleFileRejected}
                            class="min-h-32">
                            <div class="text-center">
                                <p class="text-lg font-medium">Drop files here</p>
                                <p class="text-muted-foreground text-sm">
                                    or click to select files
                                </p>
                                <p class="text-muted-foreground mt-2 text-xs">
                                    Supported: .txt, .lst, .dict, .rule files
                                </p>
                            </div>
                        </FileDropZone>

                        {#if selectedFiles.length > 0}
                            <div class="mt-4">
                                <h4 class="font-medium">Selected Files:</h4>
                                <ul class="mt-2 space-y-1">
                                    {#each selectedFiles as file (file.name)}
                                        <li class="flex items-center gap-2 text-sm">
                                            <Badge variant="outline">{file.name}</Badge>
                                            <span class="text-muted-foreground">
                                                ({(file.size / 1024).toFixed(1)} KB)
                                            </span>
                                        </li>
                                    {/each}
                                </ul>
                            </div>
                        {/if}

                        <Field {form} name="fileName">
                            <Control>
                                {#snippet children({ props })}
                                    <Label>File Name (optional)</Label>
                                    <Input
                                        {...props}
                                        bind:value={$formData.fileName}
                                        placeholder="Override filename..." />
                                {/snippet}
                            </Control>
                            <Description>Leave blank to use original filename</Description>
                            <FieldErrors />
                        </Field>
                    {/if}
                </CardContent>
            </Card>

            <!-- Hash Type Detection -->
            {#if ($formData.uploadMode === 'text' && $formData.textContent) || ($formData.uploadMode === 'file' && selectedFiles.length > 0)}
                <Card>
                    <CardHeader>
                        <CardTitle>Hash Type Detection</CardTitle>
                        <CardDescription
                            >Validate and detect hash types in your content</CardDescription>
                    </CardHeader>
                    <CardContent class="space-y-4">
                        <Button
                            type="button"
                            variant="outline"
                            onclick={validateHashes}
                            disabled={isValidating}>
                            {isValidating ? 'Validating...' : 'Validate Hashes'}
                        </Button>

                        {#if hashGuessResults}
                            <div class="space-y-4">
                                <div>
                                    <h4 class="font-medium">Detected Hash Types:</h4>
                                    <div class="mt-2 flex flex-wrap gap-2">
                                        {#each hashGuessResults.candidates as candidate (candidate.name)}
                                            <Badge variant="outline">
                                                {candidate.name}
                                                <span class="ml-1 text-xs">
                                                    ({(candidate.confidence * 100).toFixed(1)}%)
                                                </span>
                                            </Badge>
                                        {/each}
                                    </div>
                                </div>

                                <Field {form} name="selectedHashTypeId">
                                    <Control>
                                        {#snippet children({ props })}
                                            <Label>Select Hash Type</Label>
                                            <Select
                                                type="single"
                                                bind:value={$formData.selectedHashTypeId}>
                                                <SelectTrigger>
                                                    {hashTypes.find(
                                                        (ht) =>
                                                            ht.mode.toString() ===
                                                            $formData.selectedHashTypeId
                                                    )?.name || 'Select hash type...'}
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {#each hashTypes as hashType (hashType.mode)}
                                                        <SelectItem
                                                            value={hashType.mode.toString()}>
                                                            <div
                                                                class="flex w-full items-center justify-between">
                                                                <span>{hashType.name}</span>
                                                                {#if hashType.confidence}
                                                                    <Badge
                                                                        variant="outline"
                                                                        class="ml-2">
                                                                        {(
                                                                            hashType.confidence *
                                                                            100
                                                                        ).toFixed(1)}%
                                                                    </Badge>
                                                                {/if}
                                                            </div>
                                                        </SelectItem>
                                                    {/each}
                                                </SelectContent>
                                            </Select>
                                        {/snippet}
                                    </Control>
                                    <Description
                                        >Choose the hash type for this resource</Description>
                                    <FieldErrors />
                                </Field>
                            </div>
                        {/if}
                    </CardContent>
                </Card>
            {/if}

            <!-- Resource Metadata -->
            <Card>
                <CardHeader>
                    <CardTitle>Resource Details</CardTitle>
                    <CardDescription>Additional information about this resource</CardDescription>
                </CardHeader>
                <CardContent>
                    <Field {form} name="fileLabel">
                        <Control>
                            {#snippet children({ props })}
                                <Label>Label</Label>
                                <Input
                                    {...props}
                                    bind:value={$formData.fileLabel}
                                    placeholder="Descriptive label for this resource..." />
                            {/snippet}
                        </Control>
                        <Description>A descriptive name for this resource</Description>
                        <FieldErrors />
                    </Field>
                </CardContent>
            </Card>

            <!-- Submit Actions -->
            <div class="flex justify-end gap-4">
                <Button type="button" variant="outline" onclick={() => history.back()}>
                    Cancel
                </Button>
                <Button type="submit" disabled={$submitting}>
                    {$submitting ? 'Uploading...' : 'Upload Resource'}
                </Button>
            </div>
        </form>
    </div>
</div>
