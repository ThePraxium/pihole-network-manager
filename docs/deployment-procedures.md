# Deployment Procedures

**Version**: 1.0
**Last Updated**: 2025-01-18
**Purpose**: Comprehensive guide to deploying Pi-hole Network Manager across environments

---

## Table of Contents

1. [Overview](#overview)
2. [Environment Tiers](#environment-tiers)
3. [Deployment Methods](#deployment-methods)
4. [Local Development](#local-development)
5. [Test Pi Deployment](#test-pi-deployment)
6. [Production Pi Deployment](#production-pi-deployment)
7. [Rollback Procedures](#rollback-procedures)
8. [Health Checks](#health-checks)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Pi-hole Network Manager uses a **three-tier deployment model** with increasing levels of control and approval requirements:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│      Dev     │────▶│   Test Pi    │────▶│  Production Pi   │
│   (Local)    │     │(test-pi.local│     │  (pihole.local)  │
└──────────────┘     └──────────────┘     └──────────────────┘
   No approval         Auto after         USER APPROVAL
   Full autonomy       local tests        REQUIRED
```

### Deployment Philosophy

1. **Test locally first** - No Pi needed for basic testing
2. **Verify on Test Pi** - Integration testing before production
3. **Approve for Production** - Explicit user confirmation required
4. **Monitor post-deployment** - Health checks mandatory
5. **Rollback ready** - Always have rollback plan

---

## Environment Tiers

### Development (Local Computer)

**Purpose**: Feature development and unit testing

**Characteristics**:
- Location: Developer's local machine
- Python: 3.11+ with virtual environment
- Pi Required: No (mock SSH for unit tests)
- Approval: None
- Autonomy: Full

**Configuration**:
```yaml
# ~/.config/pihole-manager/config.yaml
environment: dev
testing_mode: true
mock_ssh: true  # Optional for unit tests
```

**Typical Workflow**:
```bash
cd pihole-network-manager
python3 main.py  # Auto-creates venv, installs dependencies
# Test features locally
```

### Test Pi (test-pi.local)

**Purpose**: Integration testing and UAT verification

**Characteristics**:
- Location: Dedicated test Raspberry Pi
- SSH Access: pi@test-pi.local
- SSH Key: ~/.ssh/pihole_ed25519
- Pi-hole: Installed and configured
- Network: Isolated test network (optional)
- Approval: Autonomous after local tests pass
- Autonomy: High

**Configuration**:
```yaml
# ~/.config/pihole-manager/config.yaml
test_pi:
  host: test-pi.local
  user: pi
  key_file: ~/.ssh/pihole_ed25519
  port: 22
```

**Network Setup**:
- DNS: Test Pi serves DNS to test devices only
- DHCP: Optional (can serve DHCP to test network)
- Production Impact: None (isolated)

### Production Pi (pihole.local)

**Purpose**: Live network-wide ad blocking

**Characteristics**:
- Location: Production Raspberry Pi
- SSH Access: pi@pihole.local
- SSH Key: ~/.ssh/pihole_ed25519
- Pi-hole: Production configuration
- Network: Serves entire network
- Approval: **USER MANDATORY**
- Autonomy: Restricted

**Configuration**:
```yaml
# ~/.config/pihole-manager/config.yaml
production_pi:
  host: pihole.local
  user: pi
  key_file: ~/.ssh/pihole_ed25519
  port: 22
  require_approval: true
```

**Network Impact**:
- DNS: Critical - serves all network devices
- DHCP: May serve DHCP to entire network
- Downtime: Affects all devices during deployment

---

## Deployment Methods

### SSH-Based Deployment

All Pi deployments use SSH/SFTP:

1. **Transfer files** - SFTP upload to Pi
2. **Execute remotely** - SSH command execution
3. **Verify** - Health checks via SSH
4. **Monitor** - Post-deployment monitoring

### Deployment Artifacts

**What Gets Deployed**:
- Python modules (core, setup, management)
- Configuration files (YAML, profile definitions)
- Setup scripts (if initial setup)

**What Stays Local**:
- Virtual environment (local only)
- SSH keys (local only)
- Backups (local storage: ~/.config/pihole-manager/backups/)

---

## Local Development

### Setup

```bash
# Clone repository
git clone <repository-url>
cd pihole-network-manager

# First run auto-creates venv
python3 main.py
```

The application automatically:
1. Creates virtual environment (~/.pihole-manager-venv)
2. Installs dependencies from requirements.txt
3. Presents main menu

### Testing Without Pi

**Unit Tests**:
```bash
# Test individual modules
python3 -m pytest tests/

# Test SSH client with mocks
python3 tests/test_ssh_client_mock.py
```

**Manual Testing**:
- Use mock SSH connections
- Test UI components locally
- Verify configuration parsing

### Local Workflow

```
1. Create feature branch
2. Implement changes
3. Test locally (no Pi needed)
4. Commit to feature branch
5. Notify Knowledge Manager of changes
6. Ready for Test Pi deployment
```

---

## Test Pi Deployment

### Prerequisites

- ✅ Local tests passed
- ✅ SSH key configured (~/.ssh/pihole_ed25519)
- ✅ Test Pi accessible (ping test-pi.local)
- ✅ Knowledge Manager updated (BLOCKING)

### Deployment Process

**Automated (via UAT Agent)**:

```
Scrum Leader: "UAT Agent, deploy feature/47-blocklist-scheduling to test-pi.local.

Expected behavior:
- Blocklist scheduling functional
- Cron jobs created
- Gravity rebuild works

Deploy autonomously via SSH, test, and report."

UAT Agent:
1. SSH transfers files to test-pi.local
2. Executes setup/update commands
3. Runs acceptance tests
4. Reports: "✅ PASS: Deployment successful, all tests passing"
```

**Manual (if needed)**:

```bash
# From local computer
cd pihole-network-manager

# Run deployment via main.py management interface
python3 main.py
# Select: Pi-hole Management → Configuration → Deploy to Test Pi

# Or direct SSH
scp -r core management setup pi@test-pi.local:/opt/pihole-manager/
ssh pi@test-pi.local "sudo systemctl restart pihole-manager"  # If service exists
```

### Verification

**Automated Checks** (UAT Agent):
- Pi-hole FTL service status
- DNS resolution working
- Query blocking functional
- System resources normal
- Feature-specific tests

**Manual Verification**:
```bash
# SSH to Test Pi
ssh pi@test-pi.local

# Check Pi-hole status
pihole status

# Check DNS
dig @localhost google.com

# Check logs
tail -f /var/log/pihole.log
```

### Approval Flow

```
Test Pi deployment: AUTONOMOUS

No user approval needed if:
✅ Local tests passed
✅ Knowledge base updated
✅ Scrum Leader coordinated deployment
```

---

## Production Pi Deployment

### Prerequisites

- ✅ Test Pi verification complete (UAT PASS)
- ✅ Knowledge Manager status updated
- ✅ Health checks passed on Test Pi
- ✅ Rollback plan documented
- ✅ **USER APPROVAL OBTAINED**

### Approval Request

**Scrum Leader requests approval**:

```
Scrum Leader: "@user: Sprint 3 is ready for Production Pi deployment.

Sprint Summary:
- Issues closed: #47 (Blocklist scheduling), #52 (Device grouping), #58 (Router control)
- UAT Status: PASS (test-pi.local verification complete)
- Deployment target: pihole.local (Production Pi)
- Network impact: Brief DNS interruption possible during gravity rebuild

Release notes:
- Blocklist scheduling: Schedule profile switches via cron
- Device grouping: Group devices for easier management
- Router control: Enhanced TP-Link integration

Health checks passed on Test Pi:
✅ Pi-hole FTL operational
✅ DNS resolution working
✅ Query blocking functional
✅ No resource issues

Rollback plan: Git revert + SSH redeploy (estimated 5 minutes)

Approve Production Pi deployment? (yes/no)"
```

### User Response

**User**: "yes"

### Deployment Execution

```
Scrum Leader: "Deploying Sprint 3 to Production Pi...

Step 1: Merge release/sprint-3 to main branch"
[Git merge executed]

"Step 2: Backup current Production Pi configuration"
[Backup created via SSH]

"Step 3: SSH deploy to pihole.local"
[Files transferred via SFTP]

"Step 4: Execute update commands on Production Pi"
[SSH commands executed]

"Step 5: Restart Pi-hole services"
[pihole restartdns executed]

"Step 6: Coordinate health checks with Pi Infrastructure Agent"

Pi Infrastructure Agent: "Running health checks on pihole.local...

✅ Pi-hole FTL: active (uptime: 2m)
✅ DNS resolution: working (tested 10 domains)
✅ Query blocking: functional (test ads blocked)
✅ System resources: CPU 15%, RAM 45%, Temp 42°C
✅ Network: All devices resolving DNS

Health checks PASSED."

Scrum Leader: "✅ Sprint 3 deployed successfully to Production Pi.

Deployment complete at: 2025-01-18 14:32:15
Post-deployment status: All systems operational
Network impact: None detected

Monitoring will continue for 30 minutes."
```

### Post-Deployment Monitoring

**Duration**: 30 minutes minimum

**Monitored Metrics**:
- Pi-hole FTL service status
- DNS query success rate
- Query blocking rate
- System resources (CPU, memory, temperature)
- Network device connectivity

**Alert Conditions**:
- Service failure
- DNS resolution drops below 95%
- System resources exceed thresholds
- User reports issues

---

## Rollback Procedures

### When to Rollback

**Immediate Rollback If**:
- Production Pi service failure
- DNS resolution failure affecting network
- Critical bug discovered post-deployment
- System instability

**Consider Rollback If**:
- Feature not working as expected
- Performance degradation
- User reports issues
- UAT discovers regression

### Rollback Methods

#### 1. Git Revert + Redeploy (Recommended)

**Speed**: 5-10 minutes
**Risk**: Low

```
Scrum Leader: "Initiating rollback for Production Pi...

Step 1: Create revert branch"
git checkout main
git revert <commit-hash> -m 1
git checkout -b revert/sprint-3-issues
git push origin revert/sprint-3-issues

"Step 2: Deploy revert to Production Pi"
[SSH transfer and execute]

"Step 3: Verify rollback"
Pi Infrastructure: "Health checks after rollback:
✅ Pi-hole FTL: active
✅ DNS resolution: restored
✅ Services: stable

Rollback successful."
```

#### 2. Backup Restore

**Speed**: 3-5 minutes
**Risk**: Very Low

```
Scrum Leader: "Restoring from backup...

Backup used: backup-2025-01-18-13-00.tar.gz
Created: Before Sprint 3 deployment"

[SSH restore commands executed]

Pi Infrastructure: "Backup restored successfully.
Pi-hole configuration: Reverted to pre-deployment state
Services: Restarted and stable"
```

#### 3. Pi-hole Reconfigure

**Speed**: 10-15 minutes
**Risk**: Medium (full reconfigure)

```
ssh pi@pihole.local "sudo pihole -r --reconfigure"
```

Use only if git revert and backup restore fail.

### Rollback Verification

**Checklist**:
- ✅ Pi-hole FTL service active
- ✅ DNS resolution working
- ✅ Query blocking functional
- ✅ No errors in logs
- ✅ Network devices resolving DNS
- ✅ User confirmation of restored functionality

---

## Health Checks

### Pre-Deployment Checks

**Test Pi**:
```bash
# SSH connection
ssh pi@test-pi.local "echo 'Connection OK'"

# Pi-hole status
ssh pi@test-pi.local "pihole status"

# DNS resolution
ssh pi@test-pi.local "dig @localhost google.com +short"

# Disk space
ssh pi@test-pi.local "df -h / | tail -1 | awk '{print \$5}'"
```

**Expected Results**:
- SSH connection: Success
- Pi-hole status: Active
- DNS resolution: IP address returned
- Disk space: < 80% used

### Post-Deployment Checks

**Automated** (Pi Infrastructure Agent):

```python
def health_check(ssh_client, hostname):
    checks = {
        "pihole_ftl": check_service_status(ssh_client, "pihole-FTL"),
        "dns_resolution": check_dns(ssh_client),
        "query_blocking": check_blocking(ssh_client),
        "system_resources": check_resources(ssh_client),
        "disk_space": check_disk(ssh_client),
        "temperature": check_temp(ssh_client)
    }

    return all(checks.values()), checks
```

**Manual Verification**:

```bash
# Service status
sudo systemctl status pihole-FTL

# Query stats
pihole -c -e  # Exit with Ctrl+C

# Recent queries
pihole -t  # Tail log

# System resources
htop

# Temperature
vcgencmd measure_temp
```

### Health Check Schedule

**Production Pi**:
- Pre-deployment: Mandatory
- Post-deployment: Immediate + 30 minutes monitoring
- Daily: Automated health check (cron job optional)
- On-demand: Via management tool

---

## Troubleshooting

### Deployment Failures

**SSH Connection Failed**:
```
Symptom: Cannot connect to Pi
Cause: Pi offline, wrong hostname, network issue
Fix:
  1. Ping Pi: ping pihole.local
  2. Check power and network cable
  3. Verify hostname in config.yaml
  4. Check SSH key permissions: chmod 600 ~/.ssh/pihole_ed25519
```

**File Transfer Failed**:
```
Symptom: SFTP upload fails
Cause: Permissions, disk space
Fix:
  1. Check disk space: ssh pi@pihole.local "df -h"
  2. Check permissions: ssh pi@pihole.local "ls -la /opt/pihole-manager"
  3. Verify SSH user has write access
```

**Pi-hole Service Won't Start**:
```
Symptom: pihole-FTL service fails to start after deployment
Cause: Configuration error, port conflict, corrupted database
Fix:
  1. Check logs: journalctl -u pihole-FTL -n 50
  2. Verify configuration: pihole -d (debug mode)
  3. Check port 53 availability: sudo lsof -i :53
  4. Reconfigure if needed: sudo pihole -r
```

### Rollback Issues

**Rollback Fails**:
```
Symptom: Rollback command completes but service still broken
Cause: Incomplete rollback, database corruption
Fix:
  1. Restore from backup (most reliable)
  2. Manual reconfigure: sudo pihole -r --reconfigure
  3. Check /etc/pihole/ configuration files
  4. Worst case: Reinstall Pi-hole
```

### Health Check Failures

**DNS Not Resolving**:
```
Symptom: dig @localhost fails
Cause: Pi-hole FTL not running, upstream DNS issue
Fix:
  1. Restart service: sudo systemctl restart pihole-FTL
  2. Check upstream DNS: pihole -g
  3. Verify /etc/pihole/setupVars.conf
```

**High Resource Usage**:
```
Symptom: CPU > 80%, Memory > 90%
Cause: Blocklist too large, query volume high, memory leak
Fix:
  1. Switch to lighter blocklist profile
  2. Check query volume: pihole -c
  3. Restart Pi-hole: pihole restartdns
  4. Reboot Pi if needed: sudo reboot
```

---

## Deployment Autonomy Matrix

| Environment | Agent | Create | Deploy | Approve | Monitor |
|-------------|-------|--------|--------|---------|---------|
| **Dev** | All | ✅ Yes | ✅ Yes | ❌ None | ✅ Optional |
| **Test Pi** | Python Dev | ✅ Yes | ✅ Auto* | ❌ None | ✅ Yes |
| **Test Pi** | Pi Infrastructure | ✅ Yes | ✅ Auto* | ❌ None | ✅ Yes |
| **Test Pi** | UAT | ❌ No | ✅ Yes | ❌ None | ✅ Yes |
| **Prod Pi** | All Agents | ✅ Prep | ❌ No | ✅ **USER** | ✅ **MANDATORY** |

*Auto = Autonomous after local tests pass

---

## Summary

**Deployment Best Practices**:

1. ✅ **Always test locally first**
2. ✅ **Verify on Test Pi before Production**
3. ✅ **Update Knowledge Manager** (BLOCKING)
4. ✅ **Obtain user approval for Production Pi**
5. ✅ **Run health checks** pre and post deployment
6. ✅ **Have rollback plan ready**
7. ✅ **Monitor for 30 minutes** after Production deployment
8. ✅ **Document issues** in troubleshooting.kd

**Never**:

❌ Deploy to Production Pi without Test Pi verification
❌ Skip user approval for Production Pi
❌ Deploy without Knowledge Manager confirmation
❌ Skip health checks
❌ Deploy without rollback plan

**Deployment is safe when process is followed.**
