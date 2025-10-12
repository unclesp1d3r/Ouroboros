# Phase 2b: Resource Management

This phase introduces full support for file-based resources within Ouroboros. These include wordlists, rule files, masks, and other artifacts required for hashcat operations. All uploads are stored in MinIO using presigned URLs, with metadata tracked in the database.

This phase was previously Phase 4 but has been moved up to Phase 2b to enable Web UI support in Phase 3.

See [Phase 2 - Part 2](phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md) for UI endpoint scaffolding. This document defines the backend service implementation.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Phase 2b: Resource Management](#phase-2b-resource-management)
  - [Table of Contents](#table-of-contents)
  - [Goals](#goals)
  - [Required Endpoints (Web UI)](#required-endpoints-web-ui)
  - [Access Control](#access-control)
  - [Validation & Deduplication](#validation--deduplication)
  - [Resource Lifecycle](#resource-lifecycle)
  - [Notes](#notes)
  - [Test Cases](#test-cases)
  - [Implementation Tasks](#implementation-tasks)

<!-- mdformat-toc end -->

---

## Goals

- Integrate MinIO object storage for resource file handling
- Store file metadata (size, line count, hash, type, etc.) in the DB
- Issue presigned upload and download URLs to users and agents
- Detect duplicates using content hashing
- Support access control, sensitivity tagging, and validation
- Allow inline editing of small text-based files (e.g. masks, rules)
- Allow linking resources to attacks with GUID references
- Ensure uploaded resources never orphan or bypass backend registration

---

## Required Endpoints (Web UI)

| Method | Path                                          | Description                               |
| ------ | --------------------------------------------- | ----------------------------------------- |
| POST   | `/api/v1/web/resources/`                      | Register upload, return presigned PUT URL |
| GET    | `/api/v1/web/resources/`                      | List resources by type/project/visibility |
| GET    | `/api/v1/web/resources/{id}`                  | Get metadata                              |
| GET    | `/api/v1/web/resources/{id}/preview`          | First few lines of file                   |
| PATCH  | `/api/v1/web/resources/{id}`                  | Update metadata (name, tags, visibility)  |
| DELETE | `/api/v1/web/resources/{id}`                  | Delete resource if unlinked               |
| GET    | `/api/v1/web/resources/{id}/content`          | Get raw text (editable files only)        |
| PATCH  | `/api/v1/web/resources/{id}/content`          | Save updated content                      |
| POST   | `/api/v1/web/resources/{id}/refresh_metadata` | Revalidate size/checksum                  |

---

## Access Control

| Role       | Permissions                                                                   |
| ---------- | ----------------------------------------------------------------------------- |
| Admin      | Full read/write/delete on all resources                                       |
| Power User | Can upload, view, edit, delete project-assigned resources                     |
| User       | Can view only non-sensitive resources or those explicitly assigned to project |

---

## Validation & Deduplication

- Use MD5 or SHA-256 hash to detect duplicates (stored in DB)
- Prevent multiple uploads of identical files
- Raise error if file is already linked to an active attack or campaign - Allow user to link to the existing resource rather than reuploading

---

## Resource Lifecycle

1. **Upload Registration**

   - Client posts metadata (`name`, `resource_type`, `project_id`, etc.)
   - Server returns presigned URL for upload
   - DB record created with `status = pending`

2. **Client Uploads File**

   - PUT request directly to MinIO using presigned URL

3. **Metadata Refresh**

   - Client triggers `POST /refresh_metadata`
   - Server:
     - Downloads file in thread
     - Computes hash, byte size, line count
     - Marks `status = active`

4. **Validation (Optional)**

   - Client may preview or validate lines via `GET /lines`

5. **Link to Attack**

   - Attack refers to resource by DB `id`

---

## Notes

- Presigned URLs should expire after 15 minutes
- Validate that uploaded files match declared `resource_type`
- If the resource does not successfully upload, the resource should be deleted from the database.
- Inline editing should only be allowed if:
  - Size < 1MB
  - Line count < 5,000 (configurable)
- Deletion must only be allowed if resource is not referenced by any attack

---

## Test Cases

- Upload a valid rule file and validate it line by line
- Upload a duplicate wordlist and reject it
- Upload large file and verify preview/edit is disabled
- Attempt to delete linked resource → should fail
- Upload, then link to attack, then unlink, then delete → should succeed

---

## Implementation Tasks

- [x] **Use `minio-py`** for all MinIO access (lightweight and sufficient for presigned flow) `task_id:minio.minio_py_support`
  - All blocking operations must use `asyncio.to_thread(...)` inside FastAPI
- [x] Add `MinioContainer` from `testcontainers.minio` support to enable integration tests for MinIO-based services `task_id:testcontainers.minio_support` (see [Testcontainers MinIO Support](notes/specific_tasks/testcontainers_minio_support.md)) - This is partially implemented in `tests/conftest.py`, but needs to be fully implemented and should be tested.
- [x] Create `StorageService` class `task_id:minio.storage_service` - This is now fully implemented and tested in `app/core/services/storage_service.py`.
  - [x] Stub out the class and functions and add tests for them. `test_id:minio.storage_service_stub` - Fully implemented and tested.
  - [x] `presign_upload(bucket, key)`
  - [x] `presign_download(bucket, key)`
  - [x] `get_file_stats(bucket, key)` → byte size, line count, checksum
- [x] Create Pydantic + SQLAlchemy models for `AttackResourceFile` `task_id:minio.attack_resource_file_model`
  - Fields: `name`, `resource_type`, `guid`, `bucket`, `key`, `size_bytes`, `line_count`, `checksum`, `sensitivity`, `project_id`
  - Enum: `resource_type: [word_list, rule_list, mask_list, charset, dynamic_word_list]`
- [x] Add upload registration endpoint: `task_id:minio.upload_registration_endpoint` - This is partially implemented (see `app/api/v1/endpoints/web/resources.py` as `upload_resource_metadata(...)`), it needs to be wired to use the `StorageService`, and needs to be fully tested. The upload registration endpoint is used to register a new resource with the database and return a presigned URL for the client to upload the file to. A background task should be created to verify the file was uploaded successfully after a configurable amount of time (default 15 minutes, set in `app/core/config.py`, tests should override this to a very short value) or delete the resource if it is not uploaded after that time, unless the client notifies the server that the file was uploaded successfully via the upload verification endpoint.
  - `POST /api/v1/web/resources/` returns:
    - DB record ID
    - presigned PUT URL
    - file key format: `resources/{resource_id}/{filename}`
  - Ensure that appropriate tests are added to `tests/integration/web/test_web_resources_storage.py` to test the upload registration endpoint, with one success and two failure tests.
- [x] Add a new field to the `AttackResourceFile` model: `is_uploaded: bool` - This field should be set to `True` when the file is uploaded successfully and `False` by default. If the field is true, the `verify_upload_and_cleanup(...)` task should log that the file was uploaded successfully and exit without deleting the resource.
- [x] Add upload verification endpoint: `task_id:minio.upload_verification_endpoint` - The upload verification endpoint allows the client to notify the server that the file was uploaded successfully. This is used to update the resource metadata and set the `is_uploaded` field to True.
  - `POST /resources/{id}/uploaded` re-fetches size/lines/checksum and updates the resource metadata.
  - Ensure that appropriate tests are added to `tests/integration/web/test_web_resources_storage.py` to test the upload verification endpoint, with one success and two failure tests.
- [x] Add metadata refresh: `task_id:minio.metadata_refresh`
  - `POST /resources/{id}/refresh_metadata` re-fetches size/lines/checksum
  - Run in thread-safe context
  - Ensure that appropriate tests are added to `tests/integration/web/test_web_resources_storage.py` to test the metadata refresh endpoint, with one success and two failure tests.
- [x] Audit `app/api/v1/endpoints/web/resources.py` to ensure that all endpoints that interact with file-backed resources are using the `StorageService` to access the file content.
  - Ensure that appropriate tests are added to `tests/integration/web/test_web_resources_storage.py` to test the content validation endpoint, with one success and two failure tests.
  - Many endpoints currently have tests in `tests/integration/web/test_web_resources.py` and should rely on the web-based endpoints to test the content validation endpoint.
  - The `resource_service` should be updated to use the `StorageService` if it is not already.
  - Check the following endpoints:
    - [x] `get_resource_content(...)` - `task_id:minio.get_resource_content_endpoint`
    - [x] `list_wordlists(...)` - `task_id:minio.list_wordlists_endpoint`
    - [x] `list_rulelists(...)` - `task_id:minio.list_rulelists_endpoint`
    - [x] `list_resource_lines(...)` - `task_id:minio.list_resource_lines_endpoint`
    - [x] `add_resource_line(...)` - `task_id:minio.add_resource_line_endpoint`
    - [x] `update_resource_line(...)` - `task_id:minio.update_resource_line_endpoint`
    - [x] `delete_resource_line(...)` - `task_id:minio.delete_resource_line_endpoint`
    - [x] `get_resource_preview(...)` - `task_id:minio.get_resource_preview_endpoint`
    - [x] `list_resources(...)` - `task_id:minio.list_resources_endpoint`
    - [x] `upload_resource_metadata(...)` - `task_id:minio.upload_resource_metadata_endpoint`
    - [x] `audit_orphan_resources(...)` - `task_id:minio.audit_orphan_resources_endpoint`
    - [x] `get_resource_detail(...)` - `task_id:minio.get_resource_detail_endpoint`
    - [x] `upload_resource_content_chunk_complete(...)` - `task_id:minio.upload_resource_content_chunk_complete_endpoint`
- [x] Add orphan audit: `task_id:minio.orphan_audit` - This is partially implemented (see `app/api/v1/endpoints/web/resources.py` as `audit_orphan_resources(...)`), it needs to be wired to use the `StorageService`, and needs to be fully tested. The orphan audit is used to ensure that no MinIO objects exist without matching DB rows.
  - Ensure no MinIO objects exist without matching DB rows
