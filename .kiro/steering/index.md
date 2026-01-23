---

## inclusion: manual

# Ouroboros Development Rules Index

This document provides an index of all development rules and guidelines for the Ouroboros project.

## Rule Categories

### Architecture Rules

- **[core-concepts.mdc](mdc:.cursor/rules/architecture/core-concepts.mdc)**: Core architectural concepts and patterns
- **[docker-guidelines.mdc](mdc:.cursor/rules/architecture/docker-guidelines.mdc)**: Docker containerization best practices
- **[security-basics.mdc](mdc:.cursor/rules/architecture/security-basics.mdc)**: Security fundamentals and best practices

### Code Rules

- **[python-style.mdc](mdc:.cursor/rules/code/python-style.mdc)**: Python coding standards and formatting
- **[git.mdc](mdc:.cursor/rules/code/git.mdc)**: Git workflow and commit conventions
- **[github-actions.mdc](mdc:.cursor/rules/code/github-actions.mdc)**: CI/CD pipeline guidelines
- **[mkdocs.mdc](mdc:.cursor/rules/code/mkdocs.mdc)**: Documentation standards using MkDocs
- **[mypy.mdc](mdc:.cursor/rules/code/mypy.mdc)**: Type checking with MyPy
- **[pydantic.mdc](mdc:.cursor/rules/code/pydantic.mdc)**: Data validation with Pydantic
- **[sqlalchemy.mdc](mdc:.cursor/rules/code/sqlalchemy.mdc)**: Database ORM best practices
- **[css.mdc](mdc:.cursor/rules/code/css.mdc)**: CSS development guidelines
- **[ux-guidelines.mdc](mdc:.cursor/rules/code/ux-guidelines.mdc)**: SvelteKit + Shadcn-Svelte UI guidelines

### Meta Rules

- **[vibecoding-tips.mdc](mdc:.cursor/rules/meta/vibecoding-tips.mdc)**: Live coding session guidelines

## Rule Application

### Always Applied Rules

These rules are automatically applied to all development work:

- Core architectural concepts
- Python style and formatting standards
- Security fundamentals
- Git workflow conventions

### Context-Specific Rules

These rules apply when working in specific areas:

- Docker guidelines (when working with containers)
- GitHub Actions (when modifying CI/CD)
- Database rules (when working with SQLAlchemy)
- Frontend rules (when working with SvelteKit UI)

## Rule Updates

When updating rules:

1. Update the relevant `.mdc` file
2. Update this index if categories change
3. Test changes against existing codebase
4. Document breaking changes in commit messages

## Additional Resources

For implementation-specific guidance, see:

- `docs/development/` - Development setup and workflows
- `docs/architecture/` - System architecture documentation
- `docs/v2_rewrite_implementation_plan/` - Migration and implementation plans
---

> [WARN] Note: All rules should be followed consistently across the codebase. When in doubt, refer to the specific rule file for detailed guidance.
