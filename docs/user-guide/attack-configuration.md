# Attack Configuration Guide

This guide covers the configuration of different attack types in Ouroboros v2, including the new attack editors, ephemeral resources, and real-time estimation features.

---

## Table of Contents

<!-- mdformat-toc start --slug=gitlab --no-anchors --maxlevel=3 --minlevel=1 -->

- [Attack Configuration Guide](#attack-configuration-guide)
  - [Table of Contents](#table-of-contents)
  - [Attack Types Overview](#attack-types-overview)
  - [Attack Editor Features](#attack-editor-features)
    - [Real-time Estimation](#real-time-estimation)
    - [Attack Lifecycle Management](#attack-lifecycle-management)
    - [Export/Import](#exportimport)
  - [Dictionary Attacks](#dictionary-attacks)
    - [Modern Dictionary Editor](#modern-dictionary-editor)
    - [Example Dictionary Attack Configurations](#example-dictionary-attack-configurations)
  - [Mask Attacks](#mask-attacks)
    - [Enhanced Mask Editor](#enhanced-mask-editor)
    - [Example Mask Configurations](#example-mask-configurations)
  - [Brute Force Attacks](#brute-force-attacks)
    - [Simplified Brute Force Interface](#simplified-brute-force-interface)
    - [Example Brute Force Configuration](#example-brute-force-configuration)
  - [Hybrid Attacks](#hybrid-attacks)
    - [Combination Approaches](#combination-approaches)
  - [Performance Optimization](#performance-optimization)
    - [Resource Allocation](#resource-allocation)
    - [Distribution Settings](#distribution-settings)
    - [Complexity Scoring](#complexity-scoring)
  - [Hash Type Support](#hash-type-support)
    - [Common Hash Types](#common-hash-types)
    - [Hash Type Detection](#hash-type-detection)
  - [Attack Validation](#attack-validation)
    - [Pre-execution Validation](#pre-execution-validation)
    - [Error Handling](#error-handling)
  - [Best Practices](#best-practices)
    - [Attack Planning](#attack-planning)
    - [Performance Tips](#performance-tips)
    - [Security Considerations](#security-considerations)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
    - [Performance Monitoring](#performance-monitoring)

<!-- mdformat-toc end -->

---

## Attack Types Overview

Ouroboros v2 supports multiple attack types with enhanced configuration and user-friendly interfaces:

1. **Dictionary Attack**

   - Uses wordlists with optional rule modifications
   - Supports ephemeral wordlists and modifiers
   - Real-time keyspace estimation

2. **Mask Attack**

   - Custom character sets and patterns
   - Inline mask editing with validation
   - Ephemeral mask lists

3. **Brute Force Attack**

   - Simplified charset selection interface
   - Automatic mask generation
   - Length range configuration

4. **Hybrid Attack**

   - Combines dictionary and mask approaches
   - Left-side or right-side combinations

## Attack Editor Features

### Real-time Estimation

All attack editors provide live feedback:

- **Keyspace Calculation**: Updates as you configure the attack
- **Complexity Score**: 1-5 scale indicating attack difficulty
- **Time Estimates**: Projected completion time based on agent performance
- **Password Count**: Total passwords to be tested

### Attack Lifecycle Management

- **Edit Protection**: Warnings when modifying running or completed attacks
- **State Reset**: Editing resets attack to pending state for reprocessing
- **Progress Tracking**: Real-time updates via Server-Sent Events (SSE)

### Export/Import

- **JSON Export**: Save attack configurations for reuse
- **Template Sharing**: Share attack configurations between campaigns
- **Validation**: Imported configurations are validated before use

## Dictionary Attacks

### Modern Dictionary Editor

The dictionary attack editor provides an intuitive interface for configuring wordlist-based attacks:

#### Basic Configuration

```yaml
name: Common Passwords Dictionary
attack_mode: dictionary
config:
  wordlist: rockyou.txt
  min_length: 8
  max_length: 16
  hash_type: 1000    # NTLM
```

#### Wordlist Selection

- **Searchable Dropdown**: Find wordlists by name
- **Entry Counts**: Shows number of words in each list
- **Sort by Modified**: Most recently updated lists first
- **Project Scoping**: Only shows accessible wordlists

#### Length Constraints

Set minimum and maximum password lengths to filter wordlist entries:

```html
<div class="length-controls">
 <input max="128" min="1" name="min_length" type="number" value="1"/>
 <input max="128" min="1" name="max_length" type="number" value="32"/>
</div>
```

#### Modifiers (User-Friendly Rules)

Instead of complex hashcat rules, use simple modifier buttons:

##### Change Case Modifiers

- **Uppercase**: Convert all characters to uppercase (`u` rule)
- **Lowercase**: Convert all characters to lowercase (`l` rule)
- **Capitalize**: Capitalize first letter (`c` rule)
- **Toggle Case**: Invert case of all characters (`t` rule)

##### Change Order Modifiers

- **Duplicate**: Duplicate the entire word (`d` rule)
- **Reverse**: Reverse the word (`r` rule)

##### Substitute Characters

- **Leetspeak**: Common character substitutions (e.g., a→@, e→3)
- **Combinator**: Advanced character substitution rules

```html
<div class="modifiers">
 <button class="modifier-btn" data-type="case">
  + Change Case
 </button>
 <button class="modifier-btn" data-type="order">
  + Change Order
 </button>
 <button class="modifier-btn" data-type="substitute">
  + Substitute Characters
 </button>
</div>
```

#### Advanced Options

##### Previous Passwords

Use cracked passwords from previous campaigns as a dynamic wordlist:

- **Auto-generation**: Creates wordlist from project's crack results
- **Project-scoped**: Only includes passwords from accessible projects
- **Dynamic**: Updates as new passwords are cracked

##### Ephemeral Wordlists

Add custom words directly in the attack editor:

```html
<div class="ephemeral-wordlist">
 <div class="word-entry">
  <input placeholder="Enter word" type="text"/>
  <button class="add-word">
   +
  </button>
 </div>
 <div class="word-list">
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
 </div>
</div>
```

##### Expert Mode: Rule Lists

For advanced users, select specific hashcat rule files:

```yaml
config:
  wordlist: rockyou.txt
  rule_list: best64.rule
    # OR use modifiers (mutually exclusive)
  modifiers: [uppercase, leetspeak]
```

### Example Dictionary Attack Configurations

#### Basic Dictionary

```yaml
name: Simple Dictionary
attack_mode: dictionary
config:
  wordlist: common-passwords.txt
  min_length: 6
  max_length: 20
  hash_type: 0    # MD5
```

#### Dictionary with Modifiers

```yaml
name: Dictionary with Case Changes
attack_mode: dictionary
config:
  wordlist: rockyou.txt
  modifiers: [uppercase, capitalize, leetspeak]
  min_length: 8
  max_length: 16
  hash_type: 1000    # NTLM
```

#### Previous Passwords Attack

```yaml
name: Previous Cracks
attack_mode: dictionary
config:
  use_previous_passwords: true
  modifiers: [reverse, duplicate]
  hash_type: 1800    # SHA512crypt
```

## Mask Attacks

### Enhanced Mask Editor

The mask attack editor provides inline editing with real-time validation:

#### Basic Mask Configuration

```yaml
name: 8-Digit PIN
attack_mode: mask
config:
  mask: ?d?d?d?d?d?d?d?d
  hash_type: 0
  increment: false
```

#### Inline Mask Editing

Add and edit mask patterns directly in the interface:

```html
<div class="mask-editor">
 <div class="mask-line">
  <input placeholder="Enter mask pattern" type="text" value="?d?d?d?d"/>
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

#### Real-time Validation

Mask syntax is validated as you type:

- **Valid Syntax**: Green checkmark indicator
- **Invalid Syntax**: Red error with explanation
- **Character Classes**: Tooltips showing available classes (?l, ?u, ?d, ?s, etc.)

#### Custom Character Sets

Define custom character sets for mask tokens:

```yaml
config:
  mask: ?1?1?1?1?2?2
  custom_charset_1: abcdefghijklmnopqrstuvwxyz      # ?1
  custom_charset_2: '0123456789'                     # ?2
  custom_charset_3: '@#$%^&*'                        # ?3
  custom_charset_4: ABCDEFGHIJKLMNOPQRSTUVWXYZ       # ?4
```

#### Ephemeral Mask Lists

Store multiple mask patterns with the attack:

- **Attack-local**: Masks are stored with the attack, not as separate resources
- **Temporary**: Deleted when attack is removed
- **Inline Editing**: Add/remove masks directly in the editor

#### Incremental Mode

Generate masks of varying lengths:

```yaml
config:
  base_mask: ?l?l?l?l
  increment: true
  min_length: 4
  max_length: 8
  hash_type: 1000
```

### Example Mask Configurations

#### Simple PIN Mask

```yaml
name: 4-8 Digit PIN
attack_mode: mask
config:
  mask: ?d?d?d?d
  increment: true
  min_length: 4
  max_length: 8
```

#### Complex Password Mask

```yaml
name: Complex Password Pattern
attack_mode: mask
config:
  mask: ?1?1?1?1?2?2?3
  custom_charset_1: abcdefghijklmnopqrstuvwxyz
  custom_charset_2: '0123456789'
  custom_charset_3: '!@#$%'
```

#### Multiple Mask Patterns

```yaml
name: Common Patterns
attack_mode: mask
config:
  ephemeral_masks:
    - ?l?l?l?l?d?d
    - ?u?l?l?l?d?d
    - ?l?l?l?d?d?d?d
```

## Brute Force Attacks

### Simplified Brute Force Interface

The brute force editor provides a user-friendly way to configure incremental attacks:

#### Charset Selection

Use checkboxes to select character types:

```html
<div class="charset-selection">
 <label>
  <input checked="" type="checkbox" value="lowercase"/>
  Lowercase (a-z)
 </label>
 <label>
  <input type="checkbox" value="uppercase"/>
  Uppercase (A-Z)
 </label>
 <label>
  <input checked="" type="checkbox" value="numbers"/>
  Numbers (0-9)
 </label>
 <label>
  <input type="checkbox" value="symbols"/>
  Symbols (!@#$...)
 </label>
 <label>
  <input type="checkbox" value="space"/>
  Space
 </label>
</div>
```

#### Length Range

Set minimum and maximum password lengths:

```html
<div class="length-range">
 <label>
  Min Length:
  <input max="16" min="1" type="range" value="4"/>
 </label>
 <label>
  Max Length:
  <input max="16" min="1" type="range" value="8"/>
 </label>
</div>
```

#### Automatic Mask Generation

The system automatically generates appropriate masks:

- **Selected Charsets**: Combines selected character types into `?1` charset
- **Length-based Mask**: Creates `?1?1?1...` pattern based on max length
- **Incremental Mode**: Automatically enabled with min/max length

### Example Brute Force Configuration

```yaml
name: Lowercase + Numbers Brute Force
attack_mode: mask
config:
  mask: ?1?1?1?1?1?1      # Auto-generated
  custom_charset_1: abcdefghijklmnopqrstuvwxyz0123456789      # Auto-generated
  increment: true
  min_length: 4
  max_length: 6
  hash_type: 0
```

## Hybrid Attacks

### Combination Approaches

Hybrid attacks combine dictionary and mask techniques:

#### Left-side Dictionary (Dictionary + Mask)

```yaml
name: Words + Numbers
attack_mode: hybrid
config:
  mode: dict_mask
  wordlist: common-words.txt
  mask: ?d?d?d
  hash_type: 1000
```

#### Right-side Dictionary (Mask + Dictionary)

```yaml
name: Numbers + Words
attack_mode: hybrid
config:
  mode: mask_dict
  wordlist: common-words.txt
  mask: ?d?d?d
  hash_type: 1000
```

#### With Rules

```yaml
name: Hybrid with Rules
attack_mode: hybrid
config:
  mode: dict_mask
  wordlist: rockyou.txt
  mask: ?d?d
  rule_list: best64.rule
  hash_type: 1000
```

## Performance Optimization

### Resource Allocation

Configure how attacks utilize available resources:

```yaml
performance:
  max_agents: 10
  min_agents: 2
  workload: 3    # 1-4, higher = more GPU utilization
  gpu_temp_abort: 90
  priority: high      # low, medium, high
```

### Distribution Settings

Control how work is distributed across agents:

```yaml
distribution:
  keyspace_division: balanced      # or "sequential"
  chunk_size: 1000000
  adaptive_sizing: true
  overlap_prevention: true
```

### Complexity Scoring

Attacks are automatically assigned complexity scores (1-5):

- **Score 1**: Very simple (small wordlists, short masks)
- **Score 2**: Simple (medium wordlists, basic masks)
- **Score 3**: Moderate (large wordlists, complex masks)
- **Score 4**: Complex (very large keyspaces)
- **Score 5**: Extreme (massive keyspaces, may not complete)

## Hash Type Support

### Common Hash Types

| Code | Hash Type   | Example                                                      |
| ---- | ----------- | ------------------------------------------------------------ |
| 0    | MD5         | 5f4dcc3b5aa765d61d8327deb882cf99                             |
| 100  | SHA1        | a94a8fe5ccb19ba61c4c0873d391e987982fbbd3                     |
| 1000 | NTLM        | b4b9b02e6f09a9bd760f388b67351e2b                             |
| 1800 | SHA512crypt | $6$salt$hash                                                 |
| 3200 | bcrypt      | $2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LffqmoKYYL.kj.jzm |

### Hash Type Detection

Ouroboros v2 includes automatic hash type detection:

- **Confidence Scoring**: Shows detection confidence (0-100%)
- **Multiple Suggestions**: Lists possible hash types
- **Manual Override**: Allow user to select different type
- **Validation**: Ensures hashcat compatibility

## Attack Validation

### Pre-execution Validation

Before attacks run, the system validates:

- **Resource Availability**: Ensures wordlists/rules exist
- **Syntax Checking**: Validates mask patterns and rules
- **Compatibility**: Checks attack mode vs hash type compatibility
- **Keyspace Limits**: Warns about extremely large keyspaces

### Error Handling

Common validation errors and solutions:

1. **Invalid Mask Syntax**

   - Check character class usage (?l, ?u, ?d, ?s)
   - Verify custom charset definitions
   - Ensure proper escaping

2. **Missing Resources**

   - Upload required wordlists or rule files
   - Check project access permissions
   - Verify resource file integrity

3. **Incompatible Combinations**

   - Some hash types don't support certain attack modes
   - Check hashcat documentation for compatibility
   - Use alternative attack approaches

## Best Practices

### Attack Planning

1. **Start Simple**: Begin with dictionary attacks using common wordlists
2. **Progressive Complexity**: Gradually increase attack complexity
3. **Resource Management**: Monitor agent performance and adjust workloads
4. **Time Limits**: Set realistic expectations for completion times

### Performance Tips

1. **Wordlist Optimization**

   - Use targeted, relevant wordlists
   - Remove duplicates and sort by probability
   - Consider wordlist size vs attack time

2. **Mask Efficiency**

   - Start with shorter masks and increment
   - Use custom charsets to reduce keyspace
   - Avoid overly complex patterns

3. **Agent Utilization**

   - Monitor agent temperatures and performance
   - Distribute work evenly across available hardware
   - Use workload settings appropriate for hardware

### Security Considerations

1. **Hash List Protection**

   - Hash lists are strictly project-scoped
   - Ensure proper project access controls
   - Regular cleanup of completed campaigns

2. **Resource Sharing**

   - Mark sensitive wordlists as project-specific
   - Use ephemeral resources for one-time attacks
   - Regular audit of shared resources

## Troubleshooting

### Common Issues

1. **Attack Won't Start**

   - Check agent availability and status
   - Verify hash list has uncracked hashes
   - Ensure attack configuration is valid

2. **Slow Performance**

   - Monitor agent temperatures
   - Check network connectivity
   - Adjust workload settings

3. **No Results**

   - Verify hash format compatibility
   - Check attack configuration accuracy
   - Consider alternative attack approaches

4. **Resource Errors**

   - Ensure wordlists/rules are accessible
   - Check file integrity and format
   - Verify project permissions

### Performance Monitoring

Monitor these metrics during attacks:

- **Hash Rate**: Hashes per second across all agents
- **Progress**: Percentage of keyspace completed
- **Agent Health**: Temperature and utilization
- **Error Rate**: Failed tasks or agent errors
- **ETA**: Estimated time to completion

For additional troubleshooting, see the [Troubleshooting Guide](troubleshooting.md).
