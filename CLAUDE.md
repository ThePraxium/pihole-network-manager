# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Multi-Agent Development System

**IMPORTANT**: This project uses a **multi-agent development system** with specialized Claude agents coordinated through the **BLOCKING protocol**.

### Quick Reference

**Agent Roles**:
- **Scrum Leader** - Sprint orchestration, GitHub Flow, release management
- **Knowledge Manager** - Maintains `.claude/knowledge/*.kd` files, enforces BLOCKING protocol
- **Python Developer** - Python implementation, local testing
- **Pi Infrastructure** - Raspberry Pi configuration, SSH, systemd
- **UAT Pro** - Testing, verification, deployment

**Critical Concepts**:
- **BLOCKING Protocol**: Agents MUST coordinate with Knowledge Manager before updating knowledge
- **KDL Format**: Ultra-compact knowledge encoding (>2.5x token compression vs markdown)
- **Environment Autonomy**: Dev (full) → Test Pi (autonomous) → Production Pi (user approval required)

**Documentation Structure**:
- `.claude/knowledge/*.kd` - Ultra-compact KDL files for AI agents (token-optimized)
- `docs/*.md` - Comprehensive human-readable documentation with Mermaid diagrams
- **1:1 Pairing**: Every .kd file has a corresponding .md file

---

## Documentation Map

### For AI Agents (Token-Optimized)

**KDL Knowledge Base** (`.claude/knowledge/`):
- `_schema.md` - KDL syntax specification
- `agent-workflows.kd` - Agent coordination patterns (62 lines)
- `code-architecture.kd` - Python modules, Pi-hole resources (70 lines)
- `deployment-flows.kd` - Deployment procedures, sprint tracking (32 lines)
- `environment-config.kd` - Environment tiers, autonomy rules (27 lines)
- `troubleshooting.kd` - Known issues and resolutions (48 lines)

**Total**: ~240 lines of ultra-compact knowledge

### For Humans (Comprehensive)

**Primary Documentation** (`docs/`):
- `agent-coordination.md` - Agent workflows, BLOCKING protocol, GitScrum sprints (with Mermaid diagrams)
- `code-reference.md` - Code architecture, module dependencies, SSH patterns (with Mermaid diagrams)
- `deployment-guide.md` - Deployment flows, environment tiers, rollback procedures (with Mermaid diagrams)
- `troubleshooting-guide.md` - Diagnostic trees, resolution procedures (with Mermaid diagrams)
- `architecture.md` - System architecture overview
- `development-guide.md` - Python standards, coding patterns
- `deployment-procedures.md` - Legacy deployment documentation
- `environment-config.md` - Environment configurations

---

## System Architecture (Quick Overview)

**Local Execution Model**:
- Application runs **directly on Raspberry Pi** - no remote SSH required
- All Pi-hole operations execute locally with passwordless sudo

**Communication Pattern**:
```
[Pi-hole Manager on Pi] --subprocess--> [Pi-hole Commands]
```

**Key Classes**:
- `Config` (`core/config.py`) - YAML configuration management
- `State` (`core/state.py`) - Setup state tracking
- `execute_command()` (`core/local_executor.py`) - Local subprocess execution

---

## Quick Start for AI Agents

### 1. Read the Right Documentation

**For Token Efficiency**: Start with `.claude/knowledge/*.kd` files
**For Comprehensive Understanding**: Read `docs/*.md` files

### 2. Use BLOCKING Protocol

When updating knowledge:
```
1. Agent requests update (sends KDL entry to Knowledge Manager)
2. Knowledge Manager validates syntax
3. Knowledge Manager updates .kd file
4. Knowledge Manager commits to git
5. Knowledge Manager confirms with line number
6. Agent unblocks and proceeds
```

**Never update .kd files directly** - always coordinate through Knowledge Manager.

### 3. Know Your Environment

| Environment | Approval | Autonomy | Git Branch |
|-------------|----------|----------|------------|
| **Dev** (local) | None | Full | feature/* |
| **Test Pi** (test-pi.local) | Auto after local | High | release/sprint-N |
| **Production Pi** (pihole.local) | **USER REQUIRED** | Restricted | main |

### 4. Critical Code Patterns

**Local Command Execution**:
```python
from core.local_executor import execute_command

# Execute Pi-hole command
success, stdout, stderr = execute_command("pihole status", sudo=True)

# Execute without sudo
success, stdout, stderr = execute_command("hostname", sudo=False)
```

**Database Queries**:
```python
from core.local_executor import execute_command, query_database

# Via execute_command (slower)
success, output, _ = execute_command(
    "sqlite3 /etc/pihole/gravity.db 'SELECT * FROM domainlist;'",
    sudo=True
)

# Via query_database (faster, direct)
results = query_database("/etc/pihole/gravity.db", "SELECT * FROM domainlist")
```

**SQL Escaping** (MANDATORY):
```python
domain_escaped = domain.replace("'", "''")  # ALWAYS escape!
```

**Gravity Rebuild** (REQUIRED after domain changes):
```python
execute_command("pihole -g", sudo=True)
```

**UI Output** (NEVER use print()):
```python
from core.ui import show_status, show_success, show_error
show_status("Processing...", "info")  # Use Rich console only
```

---

## Critical Gotchas

### 1. Time-Based Content Filtering NOT Automated ⚠️

**MOST IMPORTANT LIMITATION**: Content filter rules can have time schedules, but enforcement is **manual only**.

Schedules exist in JSON but NO cron automation. User must manually toggle rules or create custom cron jobs.

### 2. Always Rebuild Gravity After Changes

After modifying blocklists or domainlist:
```python
from core.local_executor import execute_command
execute_command("pihole -g", sudo=True)  # REQUIRED!
```

### 3. SQL Escaping Required

When inserting domains:
```python
# WRONG - SQL injection risk
query = f"INSERT INTO domainlist VALUES (1, '{domain}', 1);"

# CORRECT
domain_escaped = domain.replace("'", "''")
query = f"INSERT INTO domainlist VALUES (1, '{domain_escaped}', 1);"
```

### 4. Sudo Almost Always Required

Most Pi-hole operations need sudo:
```python
from core.local_executor import execute_command

# WRONG (will fail)
execute_command("pihole status", sudo=False)

# CORRECT
execute_command("pihole status", sudo=True)
```

### 5. Config File Location

```
Pi Configuration:  ~/pihole-network-manager/config.yaml
State Tracking:    ~/pihole-network-manager/state.json
Sudoers Config:    /etc/sudoers.d/pihole-manager
```

All configuration resides on the Pi where the manager runs.

---

## File Locations Reference

| Resource | Location | Sudo Required |
|----------|----------|---------------|
| Gravity Database | `/etc/pihole/gravity.db` | Write: Yes |
| FTL Database | `/etc/pihole/pihole-FTL.db` | Read: Yes |
| Blocklist Profiles | `~/pihole-network-manager/profiles/*.yaml` | No |
| State File | `~/pihole-network-manager/state.json` | No |
| Config File | `~/pihole-network-manager/config.yaml` | No |
| Sudoers Config | `/etc/sudoers.d/pihole-manager` | Yes (read-only) |
| Session Logs | `/tmp/pihole-manager-*.log` | No |

---

## Module Dependencies

**Core Modules** (no dependencies on Management):
- `core/config.py` - YAML + encryption
- `core/local_executor.py` - Subprocess execution
- `core/ui.py` - Rich UI components
- `core/state.py` - State persistence
- `core/logger.py` - Session logging

**All management modules depend ONLY on Core**. No circular dependencies.

---

## Getting More Information

### For Agent Workflows and Coordination
- Read: `docs/agent-coordination.md` (comprehensive)
- Read: `.claude/knowledge/agent-workflows.kd` (compact)

### For Code Architecture
- Read: `docs/code-reference.md` (comprehensive with diagrams)
- Read: `.claude/knowledge/code-architecture.kd` (compact)

### For Deployment Procedures
- Read: `docs/deployment-guide.md` (comprehensive with diagrams)
- Read: `.claude/knowledge/deployment-flows.kd` (compact)
- Read: `.claude/knowledge/environment-config.kd` (compact)

### For Troubleshooting
- Read: `docs/troubleshooting-guide.md` (comprehensive with decision trees)
- Read: `.claude/knowledge/troubleshooting.kd` (compact)

### For Development Patterns
- Read: `docs/development-guide.md` (Python standards, patterns)

---

## Platform Constraints

- **Tested**: Raspberry Pi OS Lite (64-bit) only
- **Init system**: Requires systemd
- **Network**: Local network only (no VPN/remote access)

---

## Quick Commands

**Execute Pi-hole command**:
```python
from core.local_executor import execute_command

success, stdout, stderr = execute_command("pihole status", sudo=True)
```

**Query database (fast)**:
```python
from core.local_executor import query_database, query_database_dict

# Returns list of tuples
results = query_database("/etc/pihole/gravity.db", "SELECT * FROM domainlist")

# Returns list of dicts (easier to use)
results = query_database_dict("/etc/pihole/gravity.db", "SELECT * FROM domainlist")
```

**Check file existence**:
```python
from core.local_executor import file_exists

if file_exists("/etc/pihole/gravity.db"):
    # file exists
```

**Display menu**:
```python
from core.ui import show_menu

choice = show_menu("Title", ["Option 1", "Option 2"], allow_back=True)
```

**Show table**:
```python
from core.ui import show_table

show_table("Results", ["Column 1", "Column 2"], [["data1", "data2"]])
```

---

## Summary

This project uses:
- **Local execution model**: Runs directly on Raspberry Pi (no remote SSH for Pi-hole)
- **Dual-format knowledge base**: `.kd` (AI-optimized) + `.md` (human-readable)
- **Subprocess execution**: All Pi-hole operations via `core/local_executor.py`
- **Passwordless sudo**: Specific commands configured in `/etc/sudoers.d/pihole-manager`
- **State persistence**: Simple setup completion tracking

For detailed information, see the appropriate documentation file above.
