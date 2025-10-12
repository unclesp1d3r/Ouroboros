<script lang="ts">
    import { goto } from '$app/navigation';
    import { page } from '$app/state';
    import ProjectSelector from '$lib/components/layout/ProjectSelector.svelte';
    import * as Sidebar from '$lib/components/ui/sidebar/index.js';
    import { projectsStore } from '$lib/stores/projects.svelte';
    // Import Lucide icons
    import { Bot, ChartColumn, FolderOpen, Settings, Swords, Target, Users } from '@lucide/svelte';

    // Get user context from store
    const user = $derived(projectsStore.contextUser);
    const userRole = $derived(user?.role || 'user');

    const navLinks = [
        {
            label: 'Dashboard',
            href: '/',
            icon: ChartColumn,
            roles: ['user', 'admin', 'project_admin', 'operator', 'analyst'],
        },
        {
            label: 'Campaigns',
            href: '/campaigns',
            icon: Target,
            roles: ['user', 'admin', 'project_admin', 'operator', 'analyst'],
        },
        {
            label: 'Attacks',
            href: '/attacks',
            icon: Swords,
            roles: ['user', 'admin', 'project_admin', 'operator', 'analyst'],
        },
        {
            label: 'Agents',
            href: '/agents',
            icon: Bot,
            roles: ['user', 'admin', 'project_admin', 'operator', 'analyst'],
        },
        {
            label: 'Resources',
            href: '/resources',
            icon: FolderOpen,
            roles: ['user', 'admin', 'project_admin', 'operator', 'analyst'],
        },
        {
            label: 'Users',
            href: '/users',
            icon: Users,
            roles: ['admin', 'project_admin'],
        },
        {
            label: 'Settings',
            href: '/settings',
            icon: Settings,
            roles: ['user', 'admin', 'project_admin', 'operator', 'analyst'],
        },
    ];

    // Filter navigation links based on user role
    const visibleNavLinks = $derived(navLinks.filter((link) => link.roles.includes(userRole)));

    // Check if current path matches the navigation link
    function isActive(href: string): boolean {
        if (href === '/') {
            return page.url.pathname === '/';
        }
        return page.url.pathname.startsWith(href);
    }

    // Handle navigation
    function handleNavigation(href: string) {
        goto(href);
    }
</script>

<Sidebar.Root collapsible="icon">
    <Sidebar.Header>
        <div class="flex items-center gap-2 px-4 py-2">
            <img src="/logo.svg" alt="Ouroboros Logo" class="h-8 w-8 flex-shrink-0" />
            <span class="text-lg font-semibold group-data-[collapsible=icon]:hidden"
                >Ouroboros</span>
        </div>
    </Sidebar.Header>

    <Sidebar.Content>
        <Sidebar.Group>
            <Sidebar.GroupLabel>Navigation</Sidebar.GroupLabel>
            <Sidebar.GroupContent>
                <Sidebar.Menu>
                    {#each visibleNavLinks as link (link.href)}
                        <Sidebar.MenuItem>
                            <Sidebar.MenuButton
                                isActive={isActive(link.href)}
                                onclick={() => handleNavigation(link.href)}>
                                {@const IconComponent = link.icon}
                                <IconComponent size={16} />
                                <span>{link.label}</span>
                            </Sidebar.MenuButton>
                        </Sidebar.MenuItem>
                    {/each}
                </Sidebar.Menu>
            </Sidebar.GroupContent>
        </Sidebar.Group>
    </Sidebar.Content>

    <Sidebar.Footer>
        <ProjectSelector />
    </Sidebar.Footer>
</Sidebar.Root>
