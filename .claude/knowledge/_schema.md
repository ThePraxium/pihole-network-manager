# Knowledge Definition Language (KDL) Schema

**Version**: 1.0
**Project**: Pi-hole Network Manager
**Purpose**: Ultra-compact, token-optimized knowledge representation for AI agent consumption

---

## Overview

KDL is a domain-specific language for encoding project knowledge in an extremely compact format optimized for AI token efficiency. Each entry is a single line containing hierarchical metadata about code, infrastructure, deployments, or issues.

**Token Efficiency**: KDL achieves >2.5x compression vs. markdown while maintaining semantic completeness.

---

## Core Syntax

### Pattern
```
<category>::<type>::<name>:<primary-id>|<key>:<value>|<key>:<value>...
```

### Components

1. **Category** (`<category>`) - Top-level classification
   - Examples: `python`, `pi`, `pihole`, `ssh`, `deploy`, `env`, `issue`
   - Format: lowercase, no spaces
   - Purpose: Primary organization axis

2. **Type** (`<type>`) - Sub-classification within category
   - Examples: `module`, `service`, `db`, `command`, `config`
   - Format: lowercase, hyphens allowed
   - Purpose: Specific resource type

3. **Name** (`<name>`) - Human-readable identifier
   - Examples: `core-config`, `pihole-ftl`, `gravity-db`
   - Format: lowercase, hyphens for readability
   - Purpose: Descriptive label

4. **Primary ID** (`<primary-id>`) - Unique identifier
   - Examples: `core/config.py`, `pihole-FTL`, `gravity.db`
   - Format: actual resource identifier (file path, service name, etc.)
   - Purpose: Unambiguous resource reference

5. **Attributes** (`|<key>:<value>`) - Metadata key-value pairs
   - Examples: `features:yaml,ssh`, `status:active`, `port:53`
   - Format: pipe-separated, colon between key and value
   - Purpose: Arbitrary metadata

### Separators

- `::` - Hierarchical level separator
- `:` - Key-value separator (also name-from-id separator)
- `|` - Attribute separator
- `,` - Value list separator (within single value)

### Rules

1. No multi-line entries (one entry = one line)
2. No spaces in structural syntax (spaces OK in values)
3. Case-sensitive throughout
4. Attributes are optional (minimum: category::type::name:id)
5. Attribute order doesn't matter
6. Duplicate keys not allowed within single entry

---

## Categories

### `python` - Python Application Components

**Types**:
- `module` - Python modules and packages
- `class` - Important classes
- `function` - Key functions
- `config` - Configuration files

**Common Keys**:
- `file` - File path relative to project root
- `imports` - Key dependencies (comma-separated)
- `features` - Main capabilities (comma-separated)
- `entry` - Is entry point? (true/false)
- `sudo` - Requires sudo? (yes/no/required)

**Example**:
```
python::module::core-executor:core/local_executor.py|features:subprocess,sqlite,file-ops|imports:subprocess,sqlite3|sudo:required
```

### `pi` - Raspberry Pi OS and Services

**Types**:
- `service` - Systemd services
- `config` - OS configuration files
- `network` - Network settings
- `system` - System-level resources

**Common Keys**:
- `desc` - Description
- `status` - Service status (active, inactive, failed)
- `port` - Network port
- `systemd` - Is systemd service? (true/false)
- `path` - File system path

**Example**:
```
pi::service::pihole-ftl:pihole-FTL|desc:dns-dhcp|status:active|port:53|systemd:true
```

### `pihole` - Pi-hole Specific Resources

**Types**:
- `db` - Pi-hole databases
- `command` - Pi-hole CLI commands
- `config` - Pi-hole configuration
- `blocklist` - Blocklist sources
- `profile` - Blocklist profiles

**Common Keys**:
- `path` - File path
- `tables` - Database tables (comma-separated)
- `sudo` - Requires sudo (true/false/required)
- `purpose` - Command purpose
- `duration` - Expected duration
- `domains` - Domain count estimate

**Example**:
```
pihole::db::gravity:gravity.db|path:/etc/pihole|tables:adlist,domainlist,gravity|sudo:read-write
pihole::command::gravity:pihole -g|sudo:true|purpose:rebuild-blocklists|duration:varies
```

### `deploy` - Deployment Procedures

**Types**:
- `dev` - Development deployments
- `test-pi` - Test Pi deployments
- `prod-pi` - Production Pi deployments
- `sprint` - Sprint-based releases
- `rollback` - Rollback procedures
- `stage` - Deployment stages

**Common Keys**:
- `target` - Target environment/host
- `method` - Deployment method
- `approval` - Approval requirement
- `autonomy` - Autonomy level
- `git` - Git branch/tag
- `start-date` - Sprint start (YYYY-MM-DD)
- `issues` - GitHub issues (comma-separated)
- `status` - Current status
- `duration` - Expected duration

**Example**:
```
deploy::prod-pi::git-deploy:git-pull-restart|target:pihole.local|approval:required|user-confirm:mandatory|method:git-pull
deploy::sprint::sprint-3:release/sprint-3|start-date:2025-11-20|issues:#47,#52,#58|status:planned|duration:2-weeks
```

### `env` - Environment Configurations

**Types**:
- `dev` - Development environment
- `test-pi` - Test Pi environment
- `prod-pi` - Production Pi environment

**Common Keys**:
- `host` - Hostname
- `python` - Python version
- `network` - Network context
- `approval` - Approval requirement
- `autonomy` - Deployment autonomy level

**Example**:
```
env::prod-pi::config:production|host:pihole.local|python:3.11+|network-critical:true|approval:required|autonomy:restricted
```

### `issue` - Known Problems and Resolutions

**Types**: Category of problem
- `setup` - Setup and permission issues
- `pihole` - Pi-hole issues
- `python` - Python issues
- `deploy` - Deployment issues
- `router` - Router issues

**Common Keys**:
- `cause` - Root cause
- `fix` - Resolution steps
- `severity` - Severity (critical, high, medium, low)
- `common` - Is common issue? (true/false)
- `github-issue` - GitHub issue number (#N)
- `known-limitation` - Known limitation? (true/false)

**Example**:
```
issue::setup::sudo-password:sudo-prompts-password|cause:user-not-in-group|fix:logout-login-after-setup|severity:medium|common:true
```

---

## Token Optimization

### Abbreviation Standards

Use consistent abbreviations to reduce token count:

| Full Term | Abbreviation |
|-----------|--------------|
| environment | env |
| database | db |
| authentication | auth |
| configuration | config |
| notification | notif |
| description | desc |
| permission(s) | perms |

### Compact Value Formats

- ✅ `timeout:300` (not `timeout-seconds:300`)
- ✅ `python:3.11+` (not `python-version:3.11 or higher`)
- ✅ `imports:subprocess,yaml` (not separate `import1`, `import2` keys)

### Omit Redundant Context

- ✅ `python::module::core-config:core/config.py` (file path is self-documenting)
- ❌ `python::module::core-config:core-config-module-core/config.py` (redundant)

---

## Validation

### Syntax Validation

```python
import re

def validate_kdl_syntax(line):
    pattern = r'^[a-z]+::[a-z0-9-]+::[a-z0-9-]+:[^|]+(\|[a-z0-9-]+:[^|]+)*$'
    if not re.match(pattern, line):
        return False, "Invalid KDL syntax"
    return True, None
```

### Semantic Validation

**File Paths**:
- Must be valid relative paths
- Use forward slashes (/)
- Example: `core/config.py`, `management/blocklists.py`

**Hostnames**:
- Must be valid DNS names or IP addresses
- Example: `pihole.local`, `test-pi.local`, `192.168.1.100`

**SSH Key Permissions**:
- Must be valid octal permissions
- Example: `600`, `644`, `700`

**Dates**:
- ISO format: YYYY-MM-DD
- Example: `2025-11-20`

**GitHub Issues**:
- Format: `#N` where N is issue number
- Example: `#47`, `#52`, `#58`

---

## File Organization

### Standard Files

1. **code-architecture.kd** - Python modules, Pi-hole resources, services
2. **deployment-flows.kd** - Deployment procedures, sprint tracking
3. **troubleshooting.kd** - Known issues by category
4. **environment-config.kd** - Environment-specific configs
5. **agent-workflows.kd** - Agent coordination patterns

### Section Organization Within Files

**Principle**: Group by category first, then by type

**Example** (`code-architecture.kd`):
```
# Core Modules
python::module::main:...
python::module::core-config:...

# Setup Modules
python::module::setup-connection:...

# Management Modules
python::module::mgmt-blocklists:...
```

### Comments

- Start line with `#` for comments
- Use section headers for organization
- Brief, descriptive

---

## Usage Examples

### Adding New Module

```
python::module::mgmt-router:management/router_control.py|features:device-list,mac-blocking,dhcp|router:tplink-axe5400
```

### Tracking Sprint

```
deploy::sprint::sprint-5:release/sprint-5|start-date:2025-12-01|issues:#61,#62,#63|status:planned|duration:2-weeks|target:router-integration
```

### Documenting Issue

```
issue::router::auth-failed:router-authentication-fails|cause:wrong-password|fix:update-password-in-config|severity:medium
```

### Updating Sprint Status

```
# Original entry
deploy::sprint::sprint-5:release/sprint-5|start-date:2025-12-01|issues:#61,#62,#63|status:planned|duration:2-weeks

# After Test Pi verification
deploy::sprint::sprint-5:release/sprint-5|start-date:2025-12-01|issues:#61,#62,#63|status:test-pi-verified|uat:PASS|ready:prod-pi|duration:2-weeks
```

---

## Best Practices

1. **One entry per line** - Never split entries across multiple lines
2. **Consistent naming** - Use hyphens in names for readability
3. **Minimal attributes** - Only include meaningful metadata
4. **Token efficiency** - Use abbreviations, compact formats
5. **Validation** - Always validate syntax before committing
6. **Documentation** - Pair .kd files with comprehensive .md files (1:1 pairing mandatory)
7. **Updates** - Modify in place when possible, preserve line numbers
8. **Deletions** - Remove entire line, update references

---

## .kd and .md File Pairing

**Mandatory 1:1 Pairing**:
- Every `.kd` file MUST have a corresponding `.md` file
- `.kd` file: Ultra-compact KDL syntax for AI consumption
- `.md` file: Comprehensive human-readable documentation

**Example Pairing**:
- `.claude/knowledge/code-architecture.kd` (compact)
- `docs/architecture.md` (comprehensive, diagrams, examples)

**Purpose**:
- `.kd` files fit in AI context windows (token-optimized)
- `.md` files provide full details for humans (no token constraints)

---

## Maintenance

### Regular Audits

- Monthly review for drift (entries don't match reality)
- Validate syntax with validation script
- Check for duplicate entries
- Verify cross-references

### Updates

**Agent-driven** (via Knowledge Manager blocking protocol):
- Agent requests update
- Knowledge Manager validates, updates, commits
- Knowledge Manager confirms to agent

**Drift detection** (autonomous):
- Compare KDL to Pi/system reality
- Auto-correct single-attribute changes
- Flag major changes for review

---

## Summary

KDL provides a **token-efficient, semantically rich** format for encoding project knowledge. By following this schema, we achieve:

- **>2.5x token compression** vs. markdown
- **Machine-readable** structure for AI agents
- **Human-understandable** with minimal training
- **Validation-friendly** with simple regex patterns
- **Git-friendly** with one-entry-per-line format

All KDL files are complemented by comprehensive .md documentation for human reference.
