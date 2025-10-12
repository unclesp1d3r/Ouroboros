# Support HashLists with Mixed Hash Types via HashItem.hash_type_id

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Support HashLists with Mixed Hash Types via HashItem.hash_type_id](#support-hashlists-with-mixed-hash-types-via-hashitemhash_type_id)
  - [Table of Contents](#table-of-contents)
  - [Intent](#intent)
  - [Boundaries](#boundaries)
  - [Phase 1: Schema + Migration](#phase-1-schema--migration)
  - [Phase 2: Crackable Upload Integration](#phase-2-crackable-upload-integration)
  - [Phase 3: Task Planner Refactor](#phase-3-task-planner-refactor)
  - [Phase 4: Agent Compatibility - Hashlist Download](#phase-4-agent-compatibility---hashlist-download)
  - [Phase 5: Tests and Validation](#phase-5-tests-and-validation)
  - [Phase 6: Optional Follow-Up (Do NOT do in this pass)](#phase-6-optional-follow-up-do-not-do-in-this-pass)

<!-- mdformat-toc end -->

---

## Intent

Ouroboros v1 (and v2 so far) assumes a single `hash_type_id` per `HashList`, which fails in real-world scenarios like shadow files containing a mixture of bcrypt, yescrypt, and sha512crypt hashes. This change introduces minimal support for mixed-type hashlists by associating the `hash_type_id` with each individual `HashItem`, while preserving the v1 Agent API contract completely.

Agents must still receive a single `Task` with:

- One `hash_mode` field
- One list of matching hashes (as plaintext strings)

This update ensures we issue one Task per hash type, while logically keeping them part of a single unified campaign/attack from the user's perspective.

## Boundaries

- Do **not** change the v1 API schema or behavior
- Do **not** remove or alter `HashList.hash_type_id` yet — it can remain for compatibility
- Do **not** expose mixed-type hashlists in the UI or control API at this stage
- Do **not** attempt to unify or deduplicate across hash types
- Do **not** support multi-mode `Task`s — each task must have exactly one hash mode

---

## Phase 1: Schema + Migration

- [ ] Add `hash_type_id: int` to the `HashItem` model
  - Required field
  - Leave `HashList.hash_type_id` untouched for now
- [ ] Create Alembic migration:
  - Add nullable `hash_type_id` column to `hash_items`
  - Backfill `hash_type_id` on each `HashItem` using its parent `HashList.hash_type_id`
  - Set `NOT NULL` constraint once backfill is complete

---

## Phase 2: Crackable Upload Integration

- [ ] Update hash extraction logic (e.g. in `crackable_upload_pipeline.py`) to:
  - Infer the hash type of each parsed line
  - Create a `HashItem` with a per-line `hash_type_id`
- [ ] If multiple hash types are found:
  - Log per-type count in `UploadResult.metadata.hash_type_breakdown`

  - Example:

    ```json
    {
      "hash_type_breakdown": {
        "1800": 728,
        "3200": 91
      }
    }
    ```

---

## Phase 3: Task Planner Refactor

- [ ] During task generation for an Attack:
  - Group `HashItems` by `hash_type_id`
  - For each group:
    - Create a separate `Task`
    - Set `task.hash_mode = group.hash_type_id`
    - Assign only the matching subset of `HashItems` to that `Task`

---

## Phase 4: Agent Compatibility - Hashlist Download

- [ ] Modify `/api/v1/client/hashlists/{id}/download`:
  - Add required query param: `?hash_mode=<int>`
  - Filter returned `HashItems` to only those with matching `hash_type_id`
  - Output format must remain: `List[str]`, one hash per line
- [ ] Raise `400 Bad Request` if `hash_mode` param is missing or unsupported
- [ ] Add test coverage for:
  - Valid filtering by mode
  - Invalid mode or missing mode param

---

## Phase 5: Tests and Validation

- [ ] Unit test: upload with single and mixed-type hashes → verify per-line `hash_type_id`
- [ ] Integration test: upload → hashlist → campaign → attack → task
  - Verify that each task created references only one `hash_mode`
  - Verify that hash list download returns filtered values
- [ ] Validate that `GET /api/v1/client/tasks/{id}` response:
  - Includes only matching-mode hashes
  - Has correct `hash_mode` field
- [ ] Validate that Agent behavior is **unchanged** (schema match + correct input)

---

## Phase 6: Optional Follow-Up (Do NOT do in this pass)

- [ ] Do not yet remove or deprecate `HashList.hash_type_id`
- [ ] Do not yet expose mixed-type awareness in frontend or control API
