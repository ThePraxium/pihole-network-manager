# Environment Configuration Guide

**Version**: 1.0
**Last Updated**: 2025-01-18
**Purpose**: Environment-specific configurations and agent autonomy rules

---

## Overview

The Pi-hole Network Manager uses a **three-tier environment model** with different configurations and autonomy levels. For ultra-compact knowledge base format, see `.claude/knowledge/environment-config.kd`.

---

## Environment Tiers

### Development (Local Computer)

**Purpose**: Feature development and local testing

**Configuration**:
- **Location**: Developer's local machine
- **Python**: 3.11+ with virtual environment (`~/.pihole-manager-venv`)
- **Pi Required**: No (mock SSH for unit tests)
- **Network**: Local computer only

**Agent Autonomy**:
- **Approval**: None required
- **Git Strategy**: Feature branches
- **Testing**: Unit tests (mocked)
- **Deployment**: Local only
- **Agent Actions**:
  - Create: ✅ Yes
  - Delete: ✅ Yes
  - Deploy: ✅ Yes (local only)
  - Approval: ❌ None

**Use Case**: Daily development work, feature implementation, unit testing

---

### Test Pi (test-pi.local)

**Purpose**: Integration testing and UAT verification

**Configuration**:
- **Location**: Dedicated test Raspberry Pi
- **Host**: `test-pi.local`
- **SSH**: `pi@test-pi.local` with `~/.ssh/pihole_ed25519` key
- **Pi-hole**: Installed and configured
- **Network**: Isolated test network (optional) - no production impact

**Agent Autonomy**:
- **Approval**: Autonomous after local tests pass
- **Git Strategy**: Release branches
- **Testing**: Integration tests, UAT
- **Deployment**: SSH-based
- **Agent Actions**:
  - Python Developer:
    - Create: ✅ Yes
    - Delete: ❌ No
    - Deploy: ✅ Yes (after local tests)
    - Approval: Auto
  - Pi Infrastructure:
    - Configure: ✅ Yes
    - Delete: ❌ No
    - Deploy: ✅ Yes
    - Approval: Auto
  - UAT:
    - Test: ✅ Yes
    - Verify: ✅ Yes
    - Report: ✅ Autonomous
    - Approval: ❌ None (reports only)

**Use Case**: Verify features work on actual Pi before production deployment

---

### Production Pi (pihole.local)

**Purpose**: Live network-wide ad blocking (network-critical)

**Configuration**:
- **Location**: Production Raspberry Pi
- **Host**: `pihole.local`
- **SSH**: `pi@pihole.local` with `~/.ssh/pihole_ed25519` key
- **Pi-hole**: Production configuration
- **Network**: Serves entire network (DNS for all devices)
- **Safety**: Backup before deploy, rollback available, health checks mandatory

**Agent Autonomy**:
- **Approval**: **USER REQUIRED** (mandatory)
- **Git Strategy**: main branch only
- **Testing**: Smoke tests
- **Deployment**: SSH-based with user confirmation
- **Monitoring**: 30-minute post-deployment monitoring
- **Agent Actions**:
  - All Agents:
    - Create: ⚠️ Preparation only (code ready but not deployed)
    - Delete: ❌ No
    - Deploy: ❌ No (user approval required)
    - Approval: **✅ USER MANDATORY**
  - Scrum Leader:
    - Request Approval: ✅ Yes
    - Deploy: ❌ No (only after user approval)
    - Monitor: ✅ Yes (post-deployment)
    - Rollback: ✅ Yes (if needed)

**Use Case**: Live network infrastructure serving all devices

---

## Configuration Files

### Local Configuration

**Path**: `~/.config/pihole-manager/config.yaml`

**Example**:
```yaml
ssh:
  host: pihole.local
  user: pi
  key_file: ~/.ssh/pihole_ed25519
  port: 22

pihole:
  web_password_hash: ""  # Optional

router:
  type: tplink_axe5400
  host: 192.168.1.1
  username: admin
  password: ""  # Optional (automation mode)
```

### Pi-Side Configuration

**Path**: `~/pihole-network-manager/config.yaml` (on Raspberry Pi)

**Example**:
```yaml
pihole:
  admin_email: admin@example.com

blocklists:
  active_profile: moderate

router:
  enabled: true
  automation_mode: false  # true = encrypted password stored
```

---

## Agent Autonomy Matrix

| Environment | Agent              | Create | Deploy | Approve | Autonomy Level |
|-------------|--------------------| ------ | ------ | ------- | -------------- |
| **Dev**     | All Agents         | ✅ Yes | ✅ Yes | ❌ None | Full           |
| **Test Pi** | Python Developer   | ✅ Yes | ✅ Auto| ❌ None | High           |
| **Test Pi** | Pi Infrastructure  | ✅ Yes | ✅ Auto| ❌ None | High           |
| **Test Pi** | UAT                | ❌ No  | ✅ Yes | ❌ None | Testing Only   |
| **Prod Pi** | All Agents         | ⚠️ Prep| ❌ No  | ✅ User | Restricted     |
| **Prod Pi** | Scrum Leader       | ⚠️ Prep| ❌ No  | ✅ Coord| Coordination   |

**Legend**:
- ✅ Yes: Action allowed
- ❌ No: Action not allowed
- ⚠️ Prep: Preparation only (code ready, not deployed)
- Auto: Autonomous after local tests
- User: User approval required
- Coord: Coordinates approval request

---

## Environment-Specific Workflows

### Development Workflow

```
1. Agent creates feature branch
2. Agent implements feature locally
3. Agent tests locally (no Pi needed)
4. Agent updates Knowledge Manager (BLOCKING)
5. Agent reports completion
```

**No approval needed - full autonomy**

---

### Test Pi Workflow

```
1. Local tests passed (prerequisite)
2. Knowledge Manager updated (BLOCKING)
3. Scrum Leader coordinates deployment
4. UAT Agent deploys to test-pi.local
5. UAT Agent runs acceptance tests
6. UAT Agent reports: PASS or FAIL
```

**Autonomous after local tests - no user approval needed**

---

### Production Pi Workflow

```
1. Test Pi verification complete (prerequisite)
2. Knowledge Manager status updated (BLOCKING)
3. Scrum Leader requests USER APPROVAL:
   - Sprint summary
   - UAT status
   - Health checks
   - Rollback plan
4. USER approves: "yes"
5. Scrum Leader deploys to pihole.local
6. Pi Infrastructure runs health checks
7. 30-minute monitoring period
8. Scrum Leader reports completion
```

**USER APPROVAL MANDATORY - restricted autonomy**

---

## Safety Mechanisms

### Test Pi Safety

- **Network Isolation**: Optional isolated test network
- **No Production Impact**: Test Pi doesn't serve production devices
- **Rollback Available**: Can revert changes easily
- **Failure Safe**: Broken Test Pi doesn't affect network

### Production Pi Safety

- **User Approval**: Mandatory for all deployments
- **Health Checks**: Pre and post deployment
- **Backup Before Deploy**: Automatic backup creation
- **Rollback Ready**: 3 rollback methods (git revert, backup restore, reconfigure)
- **Monitoring**: 30-minute post-deployment monitoring
- **Network Impact Assessment**: Clear communication of potential downtime

---

## Environment Variables

### Local Environment

**Python Virtual Environment**: `~/.pihole-manager-venv`

**Created Automatically**: First run of `python3 main.py`

**Activation** (if needed):
```bash
source ~/.pihole-manager-venv/bin/activate
```

### Pi Environment

**Application Root**: `~/pihole-network-manager/`

**Python**: System Python 3 (no venv on Pi)

**Required Packages**: Installed during setup wizard

---

## Network Configuration

### Test Pi Network

**DNS**: Test Pi serves DNS to test devices only

**DHCP**: Optional (can serve DHCP to test network segment)

**Devices**: Test devices only (laptops, phones for testing)

**Internet Access**: Test Pi has internet for blocklist updates

### Production Pi Network

**DNS**: Serves DNS to entire network (critical service)

**DHCP**: May serve DHCP to all network devices

**Devices**: All network devices depend on Pi-hole

**Internet Access**: Required for blocklist updates and upstream DNS

---

## SSH Key Management

### Key Generation

**Done by**: Setup wizard

**Key Type**: Ed25519 (modern, secure)

**Key Location**: `~/.ssh/pihole_ed25519` (private), `~/.ssh/pihole_ed25519.pub` (public)

**Permissions**:
```bash
chmod 600 ~/.ssh/pihole_ed25519        # Private key
chmod 644 ~/.ssh/pihole_ed25519.pub    # Public key
```

### Key Deployment

**Automatic**: Setup wizard copies public key to Pi

**Manual** (if needed):
```bash
ssh-copy-id -i ~/.ssh/pihole_ed25519.pub pi@pihole.local
```

### Multiple Environments

**Same Key**: Use same key for test-pi.local and pihole.local

**Or Separate Keys**: Generate different keys for test and production

---

## Deployment Autonomy Rules

### When Agents Can Deploy Autonomously

1. ✅ **Dev Environment**: Always autonomous
2. ✅ **Test Pi**: After local tests pass
3. ❌ **Production Pi**: Never autonomous (user approval required)

### Approval Flow Examples

**Dev → Test Pi** (Autonomous):
```
Python Developer: "Feature complete, local tests passed"
Knowledge Manager: "✅ CONFIRMED: code-architecture.kd updated"
UAT: "Deploying to test-pi.local..."
UAT: "✅ PASS: All acceptance tests passing"
```

**Test Pi → Production Pi** (User Approval):
```
Scrum Leader: "@user: Sprint ready for pihole.local deployment. Approve? (yes/no)"
User: "yes"
Scrum Leader: "Deploying Sprint 3 to Production Pi..."
Pi Infrastructure: "✅ Health checks PASSED"
Scrum Leader: "✅ Deployment complete"
```

---

## Troubleshooting Environment Issues

### Wrong Environment Targeted

**Symptom**: Agent tries to deploy to production without approval

**Fix**: Verify environment config in `.claude/knowledge/environment-config.kd`

### SSH Key Not Found

**Symptom**: Cannot connect to Pi

**Fix**:
1. Check key exists: `ls -l ~/.ssh/pihole_ed25519`
2. Check permissions: `chmod 600 ~/.ssh/pihole_ed25519`
3. Regenerate if needed via setup wizard

### Configuration Mismatch

**Symptom**: Local config doesn't match Pi config

**Fix**:
1. Local config: `~/.config/pihole-manager/config.yaml`
2. Pi config: `~/pihole-network-manager/config.yaml`
3. These are **separate files** - update both if needed

---

## Summary

**Three-Tier Model**:
1. **Dev** - Local computer, full autonomy, no approval
2. **Test Pi** - Integration testing, autonomous after local tests
3. **Production Pi** - Network-critical, USER APPROVAL REQUIRED

**Key Principle**: Increasing safety controls as deployment progresses from Dev → Test Pi → Production Pi

**Safety Guarantees**:
- Test Pi failures don't affect production
- Production deployments always have user approval
- Rollback always available
- Health checks mandatory for production
