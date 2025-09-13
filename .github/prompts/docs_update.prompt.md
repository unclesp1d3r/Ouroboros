---
mode: agent
---

Source files have been modified in the CipherSwarm project. Please review the changes and update the documentation accordingly:

**STRICT EDIT RESTRICTIONS (MANDATORY ENFORCEMENT):**

- **ALLOWED PATHS ONLY**: You may ONLY modify files under these specific paths:
  - `/docs/` directory and all subdirectories
  - Project-level `README.md` and `CHANGELOG.md` in root directory
  - Frontend-level `README.md` in `frontend/` directory
- **REJECTED PATHS**: Any proposed changes outside the above paths must be REJECTED
- **DOCS-ONLY FOCUS**: This hook is exclusively for documentation updates - no source code modifications
- **MKDOCS VALIDATION**: After any documentation changes, run `just docs` to validate MkDocs builds successfully
- **NO SOURCE CHANGES**: Never modify Python source files, configuration files, or any non-documentation files

**DOCUMENTATION UPDATE TASKS:**

1. Check if READMEs/CHANGELOGs need updates for new features, API changes, or installation instructions
2. Update relevant documentation in the /docs folder if there are:
   - New API endpoints or changes to existing ones
   - Changes to CLI commands or usage patterns
   - Updates to configuration or deployment procedures
   - New features or functionality
   - Changes to the data model or architecture
3. The contents of the `/docs` directory represent the user manual for the CipherSwarm platform and should be written with that focus.

**VALIDATION REQUIREMENTS:**

- Focus on keeping the documentation accurate and up-to-date with the current codebase
- Ensure that examples, code snippets, and instructions reflect the actual implementation
- Treat frontend-level documentation separately from project-level docs
- Run `just docs` to verify MkDocs builds successfully after any changes
- If MkDocs build fails, fix the documentation issues before considering the task complete
