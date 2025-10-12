# Resource Management Guide

This guide covers the management of attack resources in Ouroboros v2, including wordlists, rule files, mask patterns, and custom charsets.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Resource Management Guide](#resource-management-guide)
  - [Table of Contents](#table-of-contents)
  - [Resource Types Overview](#resource-types-overview)
  - [Resource Browser](#resource-browser)
  - [Uploading Resources](#uploading-resources)
  - [Line-Level Editing](#line-level-editing)
  - [Ephemeral Resources](#ephemeral-resources)
  - [Dynamic Wordlists](#dynamic-wordlists)
  - [Storage and Performance](#storage-and-performance)
  - [Resource Metadata](#resource-metadata)
  - [Security and Access Control](#security-and-access-control)
  - [Best Practices](#best-practices)
  - [Troubleshooting](#troubleshooting)
  - [Integration with Attacks](#integration-with-attacks)

<!-- mdformat-toc end -->

---

## Resource Types Overview

Ouroboros v2 supports multiple resource types with enhanced management capabilities:

### 1. Resource Categories

- **Wordlists**: Dictionary files for password attacks
- **Rule Lists**: Hashcat rule files for password transformations
- **Mask Lists**: Collections of mask patterns for structured attacks
- **Charsets**: Custom character set definitions
- **Dynamic Wordlists**: Auto-generated from cracked passwords (read-only)

### 2. Resource Sources

- **Uploaded**: Files uploaded via web interface
- **Generated**: System-generated resources (e.g., dynamic wordlists)
- **Ephemeral**: Temporary resources created within attacks

## Resource Browser

### 1. Accessing Resources

Navigate to the Resource Browser via:

- Main navigation → "Resources"
- Attack editor → Resource selection dropdowns
- Campaign configuration → Resource assignment

### 2. Resource List View

The resource browser displays:

```html
<div class="resource-list">
 <div class="resource-item">
  <div class="resource-info">
   <h3>
    rockyou.txt
   </h3>
   <span class="resource-type">
    Word List
   </span>
   <span class="resource-size">
    14,344,391 lines (133 MB)
   </span>
  </div>
  <div class="resource-actions">
   <button class="edit-btn">
    Edit
   </button>
   <button class="download-btn">
    Download
   </button>
   <button class="delete-btn">
    Delete
   </button>
  </div>
 </div>
</div>
```

### 3. Filtering and Search

- **Type Filter**: Filter by resource type (wordlist, rules, masks, charsets)
- **Project Filter**: Show project-specific or global resources
- **Search**: Find resources by name or description
- **Sort Options**: Name, size, last modified, usage count

## Uploading Resources

### 1. Upload Process

1. **Navigate to Upload**

   - Click "Upload Resource" in resource browser
   - Or use drag-and-drop interface

2. **Select File and Type**

   ```yaml
   File: rockyou.txt
   Resource Type: Word List  # Auto-detected
   Name: RockYou Wordlist
   Description: Common passwords wordlist
   Project Scope: Current Project  # or Global
   ```

3. **Upload Validation**

   - File format validation
   - Size limit checking
   - Content preview
   - Duplicate detection

### 2. Supported Formats

#### Wordlists

- **Extensions**: `.txt`, `.lst`, `.dict`
- **Encoding**: UTF-8, ASCII
- **Format**: One word per line
- **Size Limit**: 1GB (configurable)

#### Rule Lists

- **Extensions**: `.rule`, `.rules`
- **Encoding**: ASCII only
- **Format**: Hashcat rule syntax
- **Validation**: Real-time syntax checking

#### Mask Lists

- **Extensions**: `.mask`, `.masks`
- **Encoding**: ASCII only
- **Format**: One mask per line
- **Validation**: Hashcat mask syntax

#### Charsets

- **Extensions**: `.charset`, `.hchr`
- **Encoding**: ASCII only
- **Format**: Custom charset definitions
- **Example**: `?1 = abcdefghijklmnopqrstuvwxyz`

### 3. Project Scoping

Resources can be scoped to projects:

- **Project-Specific**: Only accessible within assigned projects
- **Global**: Available to all projects (admin only)
- **Automatic Assignment**: Based on user's current project context

## Line-Level Editing

### 1. Inline Editor

For smaller resources (under configured limits), Ouroboros v2 provides inline editing:

```html
<div class="line-editor">
 <div class="line-item">
  <span class="line-number">
   1
  </span>
  <input class="line-content" type="text" value="password123"/>
  <button class="validate-line">
   ✓
  </button>
  <button class="delete-line">
   ×
  </button>
 </div>
 <div class="line-item">
  <span class="line-number">
   2
  </span>
  <input class="line-content" type="text" value="admin"/>
  <button class="validate-line">
   ✓
  </button>
  <button class="delete-line">
   ×
  </button>
 </div>
 <button class="add-line">
  + Add Line
 </button>
</div>
```

### 2. Edit Limitations

- **Size Threshold**: Resources over 5MB or 10,000 lines require download/reupload
- **Resource Types**: Only text-based resources support inline editing
- **Validation**: Real-time syntax checking for rules and masks
- **Permissions**: Edit access based on project membership

### 3. Validation Features

#### Rule Validation

```text
Line 3: "+rfoo" ❌
Error: Unknown rule operator 'f'

Line 7: "?u?d?l?l" ❌
Error: Duplicate character class at position 3
```

#### Mask Validation

```text
Line 2: "?d?d?d?d" ✅
Valid: 4-digit numeric mask

Line 5: "?x?d?d" ❌
Error: Invalid character class '?x'
```

## Ephemeral Resources

### 1. Attack-Local Resources

Ouroboros v2 supports ephemeral resources created within attacks:

- **Lifecycle**: Created with attack, deleted when attack is removed
- **Storage**: Stored in database, not in MinIO
- **Usage**: Single-attack only, not reusable
- **Export**: Included inline when exporting attacks

### 2. Creating Ephemeral Resources

#### Ephemeral Wordlists

```html
<div class="ephemeral-wordlist">
 <h4>
  Custom Words
 </h4>
 <div class="word-input">
  <input placeholder="Enter word" type="text"/>
  <button class="add-word">
   +
  </button>
 </div>
 <div class="word-tags">
  <span class="word-tag">
   password123
   <button>
    ×
   </button>
  </span>
  <span class="word-tag">
   admin
   <button>
    ×
   </button>
  </span>
  <span class="word-tag">
   company2024
   <button>
    ×
   </button>
  </span>
 </div>
</div>
```

#### Ephemeral Masks

```html
<div class="ephemeral-masks">
 <h4>
  Custom Masks
 </h4>
 <div class="mask-list">
  <input placeholder="Enter mask" type="text" value="?d?d?d?d"/>
  <button class="validate-mask">
   ✓
  </button>
  <button class="delete-mask">
   ×
  </button>
 </div>
 <button class="add-mask">
  + Add Mask
 </button>
</div>
```

### 3. Use Cases

- **Target-Specific Words**: Company names, locations, dates
- **Custom Patterns**: Specific mask patterns for known formats
- **One-Time Lists**: Temporary wordlists for specific campaigns
- **Testing**: Quick resource creation for attack testing

## Dynamic Wordlists

### 1. Previous Passwords

Ouroboros v2 automatically generates dynamic wordlists from cracked passwords:

- **Source**: Previously cracked passwords within the project
- **Updates**: Automatically updated as new passwords are cracked
- **Scope**: Project-specific, never shared across projects
- **Usage**: Available in dictionary attack configuration

### 2. Configuration

```yaml
attack_config:
  use_previous_passwords: true
    # Wordlist dropdown hidden when this is enabled
    # Ephemeral wordlist option also hidden
```

### 3. Benefits

- **Targeted Attacks**: Use organization-specific passwords
- **Pattern Recognition**: Leverage discovered password patterns
- **Efficiency**: Focus on likely candidates first
- **Automation**: No manual wordlist management required

## Storage and Performance

### 1. MinIO Integration

Ouroboros v2 uses MinIO for scalable resource storage:

#### Storage Structure

```text
buckets/
├── wordlists/
│   ├── uuid1.txt
│   └── uuid2.txt
├── rules/
│   ├── uuid3.rule
│   └── uuid4.rule
├── masks/
│   └── uuid5.mask
└── charsets/
    └── uuid6.charset
```

#### Benefits

- **Scalability**: Handle large resource collections
- **Performance**: Distributed storage and caching
- **Reliability**: Built-in redundancy and backup
- **Security**: Presigned URLs for secure access

### 2. Caching Strategy

- **Agent Caching**: Resources cached locally on agents
- **CDN Integration**: Optional CDN for global distribution
- **Intelligent Prefetch**: Commonly used resources pre-cached
- **Cache Invalidation**: Automatic updates when resources change

### 3. Performance Optimization

#### Upload Optimization

- **Chunked Uploads**: Large files uploaded in chunks
- **Progress Tracking**: Real-time upload progress
- **Resume Support**: Resume interrupted uploads
- **Compression**: Automatic compression for text files

#### Download Optimization

- **Presigned URLs**: Direct agent downloads from MinIO
- **Parallel Downloads**: Multiple concurrent downloads
- **Bandwidth Limiting**: Configurable download limits
- **Retry Logic**: Automatic retry on failures

## Resource Metadata

### 1. Tracked Information

Ouroboros tracks comprehensive metadata for each resource:

```yaml
resource_metadata:
  id: uuid
  name: RockYou Wordlist
  resource_type: word_list
  file_size: 139921507    # bytes
  line_count: 14344391
  encoding: utf-8
  checksum: sha256:abc123...

    # Usage tracking
  used_in_attacks: 15
  last_used: '2024-01-15T10:30:00Z'
  success_rate: 0.23    # percentage of successful attacks
    # Project information
  project_id: 123
  is_global: false
  created_by: admin@example.com
  created_at: '2024-01-01T00:00:00Z'
  modified_at: '2024-01-15T10:30:00Z'
```

### 2. Usage Analytics

- **Attack Success Rate**: Percentage of successful attacks using this resource
- **Performance Metrics**: Average time to first crack
- **Popularity**: Usage frequency across campaigns
- **Effectiveness**: Crack rate per resource type

## Security and Access Control

### 1. Project Isolation

- **Strict Boundaries**: Resources never leak between projects
- **Access Control**: Users only see resources from assigned projects
- **Admin Override**: Administrators can access all resources
- **Audit Trail**: All resource access logged

### 2. Permission Model

```yaml
permissions:
  view: [user, power_user, admin]
  upload: [power_user, admin]
  edit: [power_user, admin]
  delete: [admin]
  global_access: [admin]
```

### 3. Security Features

- **Virus Scanning**: Uploaded files scanned for malware
- **Content Validation**: File format and content validation
- **Size Limits**: Configurable upload size limits
- **Rate Limiting**: Upload frequency limits per user
- **Encryption**: Resources encrypted at rest and in transit

## Best Practices

### 1. Resource Organization

- **Naming Convention**: Use descriptive, consistent names
- **Categorization**: Organize by purpose, source, or target
- **Documentation**: Include descriptions and usage notes
- **Versioning**: Maintain multiple versions of evolving resources

### 2. Performance Optimization

- **Size Management**: Keep resources appropriately sized
- **Deduplication**: Remove duplicate entries
- **Compression**: Use compressed formats when possible
- **Cleanup**: Regularly remove unused resources

### 3. Security Considerations

- **Source Verification**: Verify resource sources and integrity
- **Content Review**: Review uploaded content for sensitive data
- **Access Auditing**: Monitor resource access patterns
- **Regular Updates**: Keep resources current and relevant

## Troubleshooting

### 1. Upload Issues

**Problem**: Upload fails or times out

```bash
# Check file size and format
ls -lh wordlist.txt
file wordlist.txt

# Verify network connectivity
curl -I https://ouroboros.example.com/api/v1/web/resources/

# Check browser console for errors
```

**Solution**:

- Verify file size is under limit
- Check network connectivity
- Try uploading smaller chunks
- Contact administrator for limit increases

### 2. Edit Restrictions

**Problem**: Cannot edit resource inline

- **Cause**: Resource exceeds size threshold
- **Solution**: Download, edit offline, and reupload
- **Alternative**: Use line-by-line editing for smaller changes

### 3. Access Denied

**Problem**: Cannot access certain resources

- **Cause**: Project access restrictions
- **Solution**: Contact administrator for project assignment
- **Check**: Verify current project context in header

### 4. Performance Issues

**Problem**: Slow resource downloads

```bash
# Test download speed
curl -w "@curl-format.txt" -o /dev/null -s "https://resource-url"

# Check agent cache
ouroboros-agent cache status
```

**Solution**:

- Clear agent cache and retry
- Check network bandwidth
- Contact administrator about CDN configuration

## Integration with Attacks

### 1. Resource Selection

Resources are selected during attack configuration:

```yaml
dictionary_attack:
  wordlist: rockyou.txt      # From resource browser
  rules: best64.rule         # Optional rule file
  min_length: 8
  max_length: 16

mask_attack:
  masks: common-patterns.mask      # Mask list resource
  custom_charset_1: ?l?d           # Or custom charset file

hybrid_attack:
  wordlist: names.txt
  mask: ?d?d?d
```

### 2. Resource Validation

Before attacks start, resources are validated:

- **Existence**: Verify resource exists and is accessible
- **Compatibility**: Check resource type matches attack mode
- **Integrity**: Verify checksums and file integrity
- **Permissions**: Ensure user has access to resource

### 3. Dynamic Updates

- **Live Updates**: Resources can be updated while attacks are running
- **Automatic Restart**: Attacks restart when linked resources change
- **Version Control**: Track which resource version was used
- **Rollback**: Ability to revert to previous resource versions

For additional information:

- [Attack Configuration Guide](attack-configuration.md) - Using resources in attacks
- [Web Interface Guide](web-interface.md) - Resource management UI
- [Troubleshooting Guide](troubleshooting.md) - Common resource issues
