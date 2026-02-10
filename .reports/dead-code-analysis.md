# Dead Code Analysis Report

**Generated**: 2026-02-09 **Branch**: control_api_completion

## Summary

| Category                | Count | Severity |
| ----------------------- | ----- | -------- |
| Unused Frontend Files   | 156   | CAUTION  |
| Unused Frontend Exports | 43    | SAFE     |
| Unused Frontend Types   | 51    | SAFE     |
| Unused Dev Dependencies | 21    | CAUTION  |
| Duplicate Exports       | 2     | SAFE     |
| Python Unused Imports   | 0     | -        |
| Python Unused Variables | 0     | -        |

## Backend (Python)

**Status**: Clean

Ruff analysis (F401, F841, F811) found no unused imports or variables in `app/` or `tests/`.

## Frontend (TypeScript/Svelte)

### Unused Files (156 files) - CAUTION

Many are Shadcn-UI components that may be used in the future. Categories:

#### UI Component Libraries (NOT recommended to delete)

These are standard Shadcn-UI components - keep for future use:

| Directory             | Files | Status               |
| --------------------- | ----- | -------------------- |
| `ui/calendar/`        | 17    | KEEP - May be needed |
| `ui/carousel/`        | 7     | KEEP - May be needed |
| `ui/collapsible/`     | 4     | KEEP - May be needed |
| `ui/command/`         | 11    | KEEP - May be needed |
| `ui/context-menu/`    | 13    | KEEP - May be needed |
| `ui/data-table/`      | 4     | KEEP - May be needed |
| `ui/drawer/`          | 10    | KEEP - May be needed |
| `ui/hover-card/`      | 3     | KEEP - May be needed |
| `ui/input-otp/`       | 5     | KEEP - May be needed |
| `ui/menubar/`         | 12    | KEEP - May be needed |
| `ui/navigation-menu/` | ~10   | KEEP - May be needed |
| `ui/pagination/`      | ~5    | KEEP - May be needed |
| `ui/popover/`         | ~3    | KEEP - May be needed |
| `ui/resizable/`       | ~4    | KEEP - May be needed |
| `ui/scroll-area/`     | ~3    | KEEP - May be needed |
| `ui/select/`          | ~10   | KEEP - May be needed |
| `ui/sheet/`           | ~8    | KEEP - May be needed |
| `ui/slider/`          | ~2    | KEEP - May be needed |
| `ui/sonner/`          | ~2    | KEEP - May be needed |
| `ui/toggle-group/`    | ~3    | KEEP - May be needed |

#### Potentially Removable Files - SAFE

| File                                                      | Reason                  | Recommendation       |
| --------------------------------------------------------- | ----------------------- | -------------------- |
| `.eslintrc.local.js`                                      | Local config not in use | SAFE to delete       |
| `playwright.config.e2e.ts`                                | Duplicate config?       | Verify before delete |
| `src/lib/components/campaigns/CampaignDeleteModal.svelte` | Unused component        | Verify usage         |
| `src/lib/components/campaigns/CampaignEditorModal.svelte` | Unused component        | Verify usage         |
| `src/lib/components/resources/RulelistDropdown.svelte`    | Unused component        | Verify usage         |
| `src/lib/components/resources/WordlistDropdown.svelte`    | Unused component        | Verify usage         |

### Unused Exports (43 functions) - SAFE

Store getter functions that may be used dynamically:

```
getAttacks, getWordlists, getRulelists, getResourcesLoading (attacks.svelte.ts)
getCampaigns, getCampaignsLoading, getCampaignsError, getTotalPages, getCurrentPage, getPageSize, getTotal (campaigns.svelte.ts)
getProjects, getProjectsLoading, getProjectsError, getProjectsPagination, getActiveProject, getAvailableProjects, getContextUser, getContextLoading, getContextError (projects.svelte.ts)
getResources, getResourcesLoading, getResourcesError, getResourcesPagination, getWordlists, getRulelists, getMasklists, getCharsets, getDynamicWordlists (resources.svelte.ts)
getUsers, getUsersLoading, getUsersError, getUsersPagination (users.svelte.ts)
```

**Recommendation**: Keep - these are likely accessed via Svelte reactive statements or templates.

### Unused Types (51 types) - SAFE

These are type definitions that may be used for documentation or future features:

- Schema types: `DictionaryAttackData`, `MaskAttackData`, `BruteForceAttackData`
- Response types: `PaginationRequest`, `PaginationResponse`, `SuccessResponse`, `ErrorResponse`
- Form types: `CampaignFormData`, `ProjectFormData`, `LoginSchema`
- Entity types: `AttackRead`, `CampaignRead`, `ProjectRead`, `UserProfile`

**Recommendation**: Keep - type definitions don't affect bundle size and serve as documentation.

### Unused Dev Dependencies (21) - CAUTION

| Package                       | Used By           | Recommendation                       |
| ----------------------------- | ----------------- | ------------------------------------ |
| `@lucide/svelte`              | Icons             | VERIFY - may be imported dynamically |
| `@tailwindcss/forms`          | Tailwind plugin   | KEEP - used in tailwind.config       |
| `@tailwindcss/typography`     | Tailwind plugin   | KEEP - used in tailwind.config       |
| `@types/d3-scale`             | D3 types          | VERIFY - check chart components      |
| `@types/d3-shape`             | D3 types          | VERIFY - check chart components      |
| `@zxcvbn-ts/core`             | Password strength | VERIFY - check auth forms            |
| `@zxcvbn-ts/language-common`  | Password strength | VERIFY - check auth forms            |
| `@zxcvbn-ts/language-en`      | Password strength | VERIFY - check auth forms            |
| `d3-scale`                    | Charts            | VERIFY - check chart components      |
| `d3-shape`                    | Charts            | VERIFY - check chart components      |
| `human-format`                | Formatting        | VERIFY - check utilities             |
| `mode-watcher`                | Theme switching   | VERIFY - check theme logic           |
| `prettier-plugin-svelte`      | Dev tooling       | KEEP - used by prettier              |
| `prettier-plugin-tailwindcss` | Dev tooling       | KEEP - used by prettier              |
| `rollup-plugin-visualizer`    | Build analysis    | KEEP - dev tool                      |
| `runed`                       | Svelte utilities  | VERIFY - check usage                 |
| `svelte-toolbelt`             | Svelte utilities  | VERIFY - check usage                 |
| `tailwind-variants`           | Styling           | VERIFY - check component styles      |
| `tailwindcss`                 | CSS framework     | KEEP - core dependency               |
| `tw-animate-css`              | Animations        | VERIFY - check animations            |
| `yeezy-dates`                 | Date utilities    | VERIFY - check date formatting       |

### Duplicate Exports (2) - SAFE

| Export                                   | File                          | Recommendation     |
| ---------------------------------------- | ----------------------------- | ------------------ |
| `ContextResponse\|contextResponseSchema` | `src/lib/schemas/auth.ts`     | Clean up duplicate |
| `ProjectRead\|ProjectReadType`           | `src/lib/schemas/projects.ts` | Clean up duplicate |

## Recommendations

### Immediate Actions (SAFE)

1. **Delete `.eslintrc.local.js`** - Local config file not in use
2. **Clean up duplicate exports** - Minor refactoring in `auth.ts` and `projects.ts`

### Requires Verification (CAUTION)

1. **Campaign/Resource modals** - Verify if used in routes before deletion
2. **Dev dependencies** - Run `pnpm why <package>` to verify usage
3. **Playwright config** - Check if `playwright.config.e2e.ts` duplicates main config

### Keep (UI Library)

All Shadcn-UI component directories should be kept. They are standard UI primitives that:

- Don't significantly impact bundle size (tree-shaking)
- May be needed for future features
- Are easy to add back but tedious to regenerate

## Test Verification Required

Before any deletions, run:

```bash
# Backend tests
just test-backend

# Frontend tests
cd frontend && pnpm test

# E2E tests (if available)
just test-e2e
```

## Next Steps

1. Run tests to establish baseline
2. Delete SAFE items one at a time
3. Re-run tests after each deletion
4. Commit after verified deletions
