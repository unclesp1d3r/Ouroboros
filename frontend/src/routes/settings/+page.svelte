<script lang="ts">
    import { page } from '$app/state';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Badge } from '$lib/components/ui/badge';
    import { Button } from '$lib/components/ui/button';
    import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';
    import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
    import { Separator } from '$lib/components/ui/separator';
    import { projectsStore } from '$lib/stores/projects.svelte';
    import { toast } from '$lib/utils/toast';
    import { onMount } from 'svelte';
    import { superForm } from 'sveltekit-superforms';
    import type { PageData } from './$types';

    let { data }: { data: PageData } = $props();

    // Extract context data from SSR
    const { user, active_project, available_projects } = data.context;

    // Hydrate store with SSR project context data
    $effect(() => {
        if (data.context) {
            projectsStore.hydrateProjectContext(active_project, available_projects, {
                id: user.id,
                email: user.email,
                name: user.name,
                role: user.role,
            });
        }
    });

    // Initialize Superforms for password change
    const {
        form: passwordForm,
        errors: passwordErrors,
        enhance: passwordEnhance,
        submitting: passwordSubmitting,
        message: passwordMessage,
    } = superForm(data.passwordForm, {
        id: 'password-form',
        resetForm: true,
        onResult: ({ result }) => {
            if (result.type === 'success' && result.data?.success) {
                toast.success(result.data.message || 'Password changed successfully');
            } else if (result.type === 'failure' && result.data?.error) {
                toast.error(result.data.error);
            }
        },
    });

    // Initialize Superforms for project switching
    const {
        form: projectForm,
        errors: projectErrors,
        enhance: projectEnhance,
        submitting: projectSubmitting,
    } = superForm(data.projectForm, {
        id: 'project-form',
        onResult: ({ result }) => {
            if (result.type === 'success') {
                // Update the store with the new active project
                const newProjectId = $projectForm.project_id;
                const newActiveProject = available_projects.find((p) => p.id === newProjectId);
                if (newActiveProject) {
                    projectsStore.setActiveProject(newActiveProject);
                }
                toast.success('Project switched successfully');
            }
        },
    });

    // Set initial project value - convert to string for Select component
    let selectedProjectId = $state(active_project?.id?.toString() || '');

    // Update form when selection changes
    $effect(() => {
        $projectForm.project_id = parseInt(selectedProjectId) || 0;
    });

    // Check for success messages from URL params
    onMount(() => {
        if (page.url.searchParams.get('switched') === 'true') {
            toast.success('Project switched successfully');
        }
    });

    function formatDate(dateString: string): string {
        return new Date(dateString).toLocaleString();
    }

    function formatRole(role: string): string {
        return role
            .split('_')
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    const selectedProject = $derived(
        available_projects.find(
            (p: { id: number; name: string }) => p.id.toString() === selectedProjectId
        )
    );
    const canSwitchProject = $derived(parseInt(selectedProjectId) !== active_project?.id);
</script>

<svelte:head>
    <title>Settings - Ouroboros</title>
</svelte:head>

<div class="container mx-auto py-6">
    <div class="mb-6">
        <h1 class="text-3xl font-bold">Settings</h1>
        <p class="text-muted-foreground">Manage your account settings and preferences.</p>
    </div>

    <div class="space-y-8">
        <!-- User Profile Section -->
        <div>
            <h2 class="mb-4 text-xl font-semibold">Profile & Security</h2>
            <div class="mx-auto max-w-2xl space-y-6">
                <!-- Profile Details Card -->
                <Card>
                    <CardHeader>
                        <CardTitle>Profile Details</CardTitle>
                    </CardHeader>
                    <CardContent class="space-y-4">
                        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
                            <div class="space-y-2">
                                <Label class="text-muted-foreground text-sm font-medium"
                                    >Name</Label>
                                <p class="text-sm">{user.name}</p>
                            </div>
                            <div class="space-y-2">
                                <Label class="text-muted-foreground text-sm font-medium"
                                    >Email</Label>
                                <p class="text-sm">{user.email}</p>
                            </div>
                            <div class="space-y-2">
                                <Label class="text-muted-foreground text-sm font-medium"
                                    >Role</Label>
                                <p class="text-sm">{formatRole(user.role)}</p>
                            </div>
                            <div class="space-y-2">
                                <Label class="text-muted-foreground text-sm font-medium"
                                    >User ID</Label>
                                <p class="font-mono text-sm text-xs">{user.id}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <!-- Password Change Card -->
                <Card>
                    <CardHeader>
                        <CardTitle>Change Password</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form
                            method="POST"
                            action="?/changePassword"
                            use:passwordEnhance
                            class="space-y-4">
                            {#if $passwordMessage}
                                <Alert variant="destructive">
                                    <AlertDescription>{$passwordMessage}</AlertDescription>
                                </Alert>
                            {/if}

                            <div class="space-y-2">
                                <Label for="old_password">Current Password</Label>
                                <Input
                                    id="old_password"
                                    name="old_password"
                                    type="password"
                                    bind:value={$passwordForm.old_password}
                                    autocomplete="current-password"
                                    required
                                    disabled={$passwordSubmitting} />
                                {#if $passwordErrors.old_password}
                                    <p class="text-destructive text-sm">
                                        {$passwordErrors.old_password}
                                    </p>
                                {/if}
                            </div>

                            <div class="space-y-2">
                                <Label for="new_password">New Password</Label>
                                <Input
                                    id="new_password"
                                    name="new_password"
                                    type="password"
                                    bind:value={$passwordForm.new_password}
                                    placeholder="Enter new password"
                                    autocomplete="new-password"
                                    minlength={10}
                                    required
                                    disabled={$passwordSubmitting} />
                                {#if $passwordErrors.new_password}
                                    <p class="text-destructive text-sm">
                                        {$passwordErrors.new_password}
                                    </p>
                                {/if}
                            </div>

                            <div class="space-y-2">
                                <Label for="new_password_confirm">Confirm New Password</Label>
                                <Input
                                    id="new_password_confirm"
                                    name="new_password_confirm"
                                    type="password"
                                    bind:value={$passwordForm.new_password_confirm}
                                    placeholder="Confirm new password"
                                    autocomplete="new-password"
                                    minlength={10}
                                    required
                                    disabled={$passwordSubmitting} />
                                {#if $passwordErrors.new_password_confirm}
                                    <p class="text-destructive text-sm">
                                        {$passwordErrors.new_password_confirm}
                                    </p>
                                {/if}
                            </div>

                            <Button type="submit" disabled={$passwordSubmitting} class="w-full">
                                {$passwordSubmitting ? 'Changing Password...' : 'Change Password'}
                            </Button>
                        </form>
                    </CardContent>
                </Card>
            </div>
        </div>

        <Separator />

        <!-- Project Context Section -->
        <div>
            <h2 class="mb-4 text-xl font-semibold">Project Context</h2>
            <Card class="mx-auto max-w-2xl">
                <CardHeader>
                    <CardTitle>Project Context</CardTitle>
                </CardHeader>
                <CardContent class="space-y-4">
                    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div class="space-y-2">
                            <Label class="text-muted-foreground text-sm font-medium">User</Label>
                            <p class="text-sm">{user.email}</p>
                        </div>
                        <div class="space-y-2">
                            <Label class="text-muted-foreground text-sm font-medium">Role</Label>
                            <Badge variant="outline">{formatRole(user.role)}</Badge>
                        </div>
                        <div class="space-y-2">
                            <Label class="text-muted-foreground text-sm font-medium"
                                >Active Project</Label>
                            <p class="text-sm">{active_project?.name || 'None'}</p>
                        </div>
                    </div>

                    {#if available_projects.length > 1}
                        <form
                            method="POST"
                            action="?/switchProject"
                            use:projectEnhance
                            class="space-y-4">
                            <div class="space-y-2">
                                <Label for="project-select">Switch Project</Label>
                                <Select type="single" bind:value={selectedProjectId}>
                                    <SelectTrigger id="project-select">
                                        <span>{selectedProject?.name || 'Select a project'}</span>
                                    </SelectTrigger>
                                    <SelectContent>
                                        {#each available_projects as project (project.id)}
                                            <SelectItem value={project.id.toString()}
                                                >{project.name}</SelectItem>
                                        {/each}
                                    </SelectContent>
                                </Select>
                                {#if $projectErrors.project_id}
                                    <p class="text-destructive text-sm">
                                        {$projectErrors.project_id}
                                    </p>
                                {/if}
                            </div>

                            <Button
                                type="submit"
                                disabled={$projectSubmitting || !canSwitchProject}
                                class="w-full">
                                {$projectSubmitting ? 'Switching...' : 'Set Active Project'}
                            </Button>
                        </form>
                    {:else if available_projects.length === 1}
                        <p class="text-muted-foreground text-sm">
                            You have access to one project only.
                        </p>
                    {:else}
                        <p class="text-muted-foreground text-sm">
                            No projects available. Contact your administrator for access.
                        </p>
                    {/if}
                </CardContent>
            </Card>
        </div>
    </div>
</div>
