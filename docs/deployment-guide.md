# Deployment Guide and Environment Configuration

**Version**: 1.0
**Last Updated**: 2025-11-18
**Paired KDL**: `.claude/knowledge/deployment-flows.kd`, `.claude/knowledge/environment-config.kd`

---

## Overview

This document provides comprehensive deployment procedures, environment tier configurations, and agent autonomy rules for the Pi-hole Network Manager across three deployment environments.

---

## Environment Tiers

```mermaid
graph LR
    subgraph Environments
        Dev[Development<br/>Local Computer<br/>Python 3.11+ venv<br/>No Pi Required]
        TestPi[Test Pi<br/>test-pi.local<br/>Isolated Network<br/>Non-Critical]
        ProdPi[Production Pi<br/>pihole.local<br/>Production Network<br/>Network-Critical]
    end

    Dev -->|Local Tests Pass| TestPi
    TestPi -->|UAT Pass + Approval| ProdPi

    ProdPi -.->|Health Check Fail| Rollback[Rollback to Dev]
    Rollback -.-> Dev

    style Dev fill:#e1f5ff
    style TestPi fill:#fff4e1
    style ProdPi fill:#ffe1e1
```

### Environment Details

| Aspect | Development | Test Pi | Production Pi |
|--------|-------------|---------|---------------|
| **Location** | Local computer | test-pi.local | pihole.local |
| **Python** | 3.11+ | 3.11+ | 3.11+ |
| **Pi Required** | No | Yes | Yes |
| **SSH** | Mock for unit tests | Real SSH | Real SSH |
| **Network Impact** | None | Isolated test network | **Entire production network** |
| **Approval** | None | Auto after local tests | **User approval required** |
| **Autonomy** | Full | High (autonomous deploy) | Restricted |
| **Git Branch** | feature/* branches | release/sprint-N | main |
| **Testing** | Unit tests | Integration + UAT | Smoke tests + health checks |
| **Rollback** | N/A | Yes | **Yes (mandatory backup first)** |

---

## Deployment Flow: End-to-End

```mermaid
flowchart TD
    Start([Code Change]) --> LocalDev[Development Environment]

    subgraph Local Development
        LocalDev --> LocalTest[Run Unit Tests<br/>pytest]
        LocalTest -->|Fail| Fix1[Fix Issues]
        Fix1 --> LocalTest
        LocalTest -->|Pass| LocalCommit[Git Commit<br/>feature/issue-N]
    end

    LocalCommit --> TestDeploy[Deploy to Test Pi]

    subgraph Test Pi Environment
        TestDeploy --> TestTransfer[SSH Transfer<br/>SFTP upload]
        TestTransfer --> TestExec[Execute on Test Pi]
        TestExec --> IntTest[Integration Tests]
        IntTest -->|Fail| Fix2[Fix Issues]
        Fix2 --> LocalDev
        IntTest -->|Pass| UAT[UAT Verification]
        UAT -->|Fail| Fix3[Fix Issues]
        Fix3 --> LocalDev
        UAT -->|Pass| TestHealth[Health Checks]
    end

    TestHealth -->|Pass| RequestApproval{Request<br/>User Approval}
    RequestApproval -->|Denied| LocalDev
    RequestApproval -->|Approved| ProdDeploy[Deploy to Production Pi]

    subgraph Production Pi Environment
        ProdDeploy --> Backup[Create Backup<br/>MANDATORY]
        Backup --> ProdTransfer[SSH Transfer<br/>SFTP upload]
        ProdTransfer --> ProdExec[Execute on Production Pi]
        ProdExec --> SmokeTest[Smoke Tests]
        SmokeTest -->|Fail| RollbackProc[Rollback]
        SmokeTest -->|Pass| ProdHealth[Health Checks]
        ProdHealth -->|Fail| RollbackProc
        ProdHealth -->|Pass| Monitor[Post-Deploy Monitoring]
    end

    RollbackProc --> RestoreBackup[Restore from Backup]
    RestoreBackup --> LocalDev

    Monitor --> Success([Deployment Complete])

    style LocalDev fill:#e1f5ff
    style TestDeploy fill:#fff4e1
    style ProdDeploy fill:#ffe1e1
    style RequestApproval fill:#fdd
```

---

## Agent Autonomy by Environment

```mermaid
graph TB
    subgraph Development Environment - FULL AUTONOMY
        DevAgent[All Agents] --> DevCreate[Create: YES]
        DevAgent --> DevDelete[Delete: YES]
        DevAgent --> DevDeploy[Deploy: YES]
        DevAgent --> DevApproval[Approval: NONE]
    end

    subgraph Test Pi Environment - HIGH AUTONOMY
        TestPD[Python Dev] --> TestCreate1[Create: YES]
        TestPD --> TestDeploy1[Deploy: YES after local]
        TestPD --> TestApproval1[Approval: AUTO]

        TestPI[Pi Infrastructure] --> TestConfig[Configure: YES]
        TestPI --> TestDeploy2[Deploy: YES]
        TestPI --> TestApproval2[Approval: AUTO]

        TestUAT[UAT Agent] --> TestTest[Test: FULL]
        TestUAT --> TestVerify[Verify: YES]
        TestUAT --> TestReport[Report: AUTONOMOUS]
    end

    subgraph Production Pi Environment - RESTRICTED AUTONOMY
        ProdAll[All Agents] --> ProdCreate[Create: Prep Only]
        ProdAll --> ProdDelete[Delete: NO]
        ProdAll --> ProdDeploy[Deploy: NO]
        ProdAll --> ProdApproval[Approval: USER REQUIRED]

        ProdSL[Scrum Leader] --> ProdCoord[Coordinate: YES]
        ProdSL --> ProdRequest[Request Approval: YES]
        ProdSL --> ProdMonitor[Monitor: YES]
    end

    style DevAgent fill:#e1f5ff
    style TestPD fill:#fff4e1
    style ProdAll fill:#ffe1e1
```

### Autonomy Matrix

| Agent | Dev | Test Pi | Production Pi |
|-------|-----|---------|---------------|
| **Python Developer** | Full autonomy | Deploy after local tests pass | Prep only, no deploy |
| **Pi Infrastructure** | Full autonomy | Configure & deploy autonomously | Prep only, no deploy |
| **UAT Agent** | Full testing autonomy | Full testing autonomy | Smoke tests only, report |
| **Scrum Leader** | Full orchestration | Coordinate deployment | Request approval, monitor |
| **Knowledge Manager** | Update autonomously | Update autonomously | Update autonomously |

---

## Deployment Methods

### 1. Local Development Deployment

```mermaid
flowchart LR
    Start([Local Change]) --> Venv[Activate venv]
    Venv --> Run[python3 main.py]
    Run --> Test[Run Unit Tests<br/>pytest]
    Test -->|Pass| Commit[Git Commit]
    Test -->|Fail| Fix[Fix & Retry]
    Fix --> Test
    Commit --> End([Ready for Test Pi])

    style Start fill:#e1f5ff
```

**Commands**:
```bash
# Setup virtual environment
python3 -m venv ~/.pihole-manager-venv
source ~/.pihole-manager-venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run locally
python3 main.py

# Run tests
pytest tests/

# Commit
git add .
git commit -m "feature: description"
```

**Characteristics**:
- No approval required
- Full autonomy for all agents
- Mock SSH connections for unit tests
- Git: feature/* branches

---

### 2. Test Pi Deployment

```mermaid
sequenceDiagram
    participant Dev as Developer/Agent
    participant Git as Git Repository
    participant SSH as SSH Client
    participant TestPi as Test Pi<br/>(test-pi.local)

    Dev->>Git: Push feature branch
    Note over Dev: Autonomous deployment<br/>after local tests pass

    Dev->>SSH: Connect to test-pi.local
    SSH->>TestPi: Establish SSH connection

    Dev->>SSH: Upload files via SFTP
    SSH->>TestPi: Transfer Python files

    Dev->>SSH: Execute setup commands
    SSH->>TestPi: Install dependencies<br/>Configure services

    TestPi-->>SSH: Installation complete
    SSH-->>Dev: Deploy successful

    Dev->>SSH: Run integration tests
    SSH->>TestPi: Execute UAT tests
    TestPi-->>SSH: Test results
    SSH-->>Dev: UAT: PASS

    Dev->>SSH: Run health checks
    SSH->>TestPi: DNS, services, DB checks
    TestPi-->>SSH: Health: PASS
    SSH-->>Dev: Test Pi deployment verified

    Note over Dev: Ready for production<br/>approval
```

**Deployment Script**:
```bash
# Connect and transfer
ssh pi@test-pi.local "mkdir -p ~/pihole-network-manager"
scp -r * pi@test-pi.local:~/pihole-network-manager/

# Execute setup
ssh pi@test-pi.local "cd ~/pihole-network-manager && sudo python3 setup.py"

# Run integration tests
ssh pi@test-pi.local "cd ~/pihole-network-manager && pytest tests/integration/"

# Health check
ssh pi@test-pi.local "cd ~/pihole-network-manager && python3 health_check.py"
```

**Characteristics**:
- Autonomous deployment after local tests pass
- No user approval required
- Isolated test network (no production impact)
- Git: release/sprint-N branches
- Full integration and UAT testing

---

### 3. Production Pi Deployment

```mermaid
sequenceDiagram
    participant Agent as Agent/Scrum Leader
    participant User as User
    participant SSH as SSH Client
    participant ProdPi as Production Pi<br/>(pihole.local)
    participant Network as Production Network

    Agent->>User: Request deployment approval
    Note over Agent: AGENT BLOCKS<br/>until approval

    User-->>Agent: APPROVED

    Agent->>SSH: Connect to pihole.local
    SSH->>ProdPi: Establish SSH connection

    Agent->>SSH: Create backup
    SSH->>ProdPi: Backup config, databases, state
    ProdPi-->>SSH: Backup created
    SSH-->>Agent: Backup confirmation

    Agent->>SSH: Upload files via SFTP
    SSH->>ProdPi: Transfer Python files

    Agent->>SSH: Execute deployment
    SSH->>ProdPi: Install/update services
    ProdPi-->>SSH: Deployment complete

    Agent->>SSH: Run smoke tests
    SSH->>ProdPi: Basic functionality tests
    ProdPi-->>SSH: Smoke tests: PASS

    Agent->>SSH: Run health checks
    SSH->>ProdPi: DNS, services, DB integrity
    ProdPi-->>SSH: Health checks: PASS

    ProdPi->>Network: Resume serving DNS/DHCP
    Note over Network: All devices affected

    Agent->>SSH: Monitor for 5 minutes
    SSH->>ProdPi: Check logs, query counts
    ProdPi-->>SSH: Monitoring: PASS
    SSH-->>Agent: Deployment verified

    Agent->>User: Deployment complete - network stable
```

**Deployment Script**:
```bash
# Request approval (via agent coordination)
# USER MUST APPROVE BEFORE PROCEEDING

# Create backup
ssh pi@pihole.local "sudo ~/pihole-network-manager/backup.sh"

# Transfer files
ssh pi@pihole.local "mkdir -p ~/pihole-network-manager-new"
scp -r * pi@pihole.local:~/pihole-network-manager-new/

# Deploy (with rollback capability)
ssh pi@pihole.local "
    sudo mv ~/pihole-network-manager ~/pihole-network-manager-backup &&
    sudo mv ~/pihole-network-manager-new ~/pihole-network-manager &&
    cd ~/pihole-network-manager &&
    sudo python3 setup.py
"

# Smoke test
ssh pi@pihole.local "dig @localhost google.com"

# Health check
ssh pi@pihole.local "cd ~/pihole-network-manager && python3 health_check.py"

# Monitor
ssh pi@pihole.local "journalctl -u pihole-FTL -f --since '5 minutes ago'"
```

**Characteristics**:
- **USER APPROVAL REQUIRED** (mandatory gate)
- Backup created BEFORE deployment
- Network-critical operation (affects all devices)
- Git: main branch only
- Smoke tests + health checks + monitoring
- Rollback capability ready

---

## Rollback Procedures

```mermaid
flowchart TD
    Trigger{Rollback<br/>Trigger}

    Trigger -->|Code Issue| CodeRollback[Code Rollback]
    Trigger -->|Config Issue| ConfigRollback[Config Rollback]
    Trigger -->|Pi-hole Issue| PiHoleRollback[Pi-hole Rollback]

    subgraph Code Rollback
        CodeRollback --> GitRevert[Git Revert Commit]
        GitRevert --> Redeploy1[Redeploy via SSH]
        Redeploy1 --> Verify1[UAT Verify]
        Verify1 -->|Pass| Approval1[Request User Approval]
        Approval1 --> Complete1[Rollback Complete]
    end

    subgraph Config Rollback
        ConfigRollback --> RestoreBackup[Restore from Backup]
        RestoreBackup --> RestoreFiles[Restore config.yaml<br/>Restore databases]
        RestoreFiles --> Verify2[Health Check]
        Verify2 -->|Pass| Approval2[Request User Approval]
        Approval2 --> Complete2[Rollback Complete]
    end

    subgraph Pi-hole Rollback
        PiHoleRollback --> PiHoleRepair[pihole -r --reconfigure]
        PiHoleRepair --> Verify3[DNS Test]
        Verify3 -->|Pass| Approval3[Request User Approval]
        Approval3 --> Complete3[Rollback Complete]
    end

    Complete1 --> Monitor[Monitor 30 minutes]
    Complete2 --> Monitor
    Complete3 --> Monitor

    Monitor --> Done([Rollback Verified])

    style Trigger fill:#fdd
```

### Rollback Commands

**Code Rollback**:
```bash
# Revert commit
git revert <commit-hash>
git push origin main

# Redeploy
ssh pi@pihole.local "
    cd ~/pihole-network-manager &&
    git pull &&
    sudo systemctl restart pihole-manager
"

# Verify
ssh pi@pihole.local "cd ~/pihole-network-manager && python3 health_check.py"
```

**Config Rollback**:
```bash
# Restore from backup
ssh pi@pihole.local "
    sudo cp ~/pihole-network-manager-backup/config.yaml ~/pihole-network-manager/ &&
    sudo cp ~/pihole-network-manager-backup/gravity.db /etc/pihole/ &&
    sudo systemctl restart pihole-FTL
"

# Verify
ssh pi@pihole.local "pihole status"
```

**Pi-hole Repair**:
```bash
# Reconfigure Pi-hole
ssh pi@pihole.local "sudo pihole -r"

# Select: Reconfigure

# Verify DNS
dig @pihole.local google.com
```

---

## Health Check Procedures

```mermaid
flowchart TD
    Start([Health Check]) --> DNS[DNS Resolution Test]

    DNS --> DNSLocal[Test Local DNS<br/>dig @localhost google.com]
    DNSLocal -->|Fail| DNSFail[DNS FAILURE]
    DNSLocal -->|Pass| DNSUpstream[Test Upstream DNS<br/>dig @8.8.8.8 google.com]
    DNSUpstream -->|Fail| UpstreamFail[UPSTREAM FAILURE]
    DNSUpstream -->|Pass| Blocking[Test Blocking]

    Blocking --> BlockTest[Query known ad domain]
    BlockTest -->|Not Blocked| BlockFail[BLOCKING FAILURE]
    BlockTest -->|Blocked| Services[Service Status]

    Services --> CheckFTL[systemctl status pihole-FTL]
    CheckFTL -->|Inactive| FTLFail[FTL SERVICE DOWN]
    CheckFTL -->|Active| CheckHTTP[systemctl status lighttpd]
    CheckHTTP -->|Inactive| HTTPFail[WEB INTERFACE DOWN]
    CheckHTTP -->|Active| DB[Database Integrity]

    DB --> GravityDB[PRAGMA integrity_check<br/>gravity.db]
    GravityDB -->|Fail| DBFail[DATABASE CORRUPTION]
    GravityDB -->|Pass| FTLDB[PRAGMA integrity_check<br/>pihole-FTL.db]
    FTLDB -->|Fail| DBFail
    FTLDB -->|Pass| Network[Network Connectivity]

    Network --> Ping[Ping Gateway]
    Ping -->|Fail| NetFail[NETWORK DOWN]
    Ping -->|Pass| Internet[Ping 8.8.8.8]
    Internet -->|Fail| InternetFail[INTERNET DOWN]
    Internet -->|Pass| Success[ALL CHECKS PASS]

    DNSFail --> Report[Generate Report]
    UpstreamFail --> Report
    BlockFail --> Report
    FTLFail --> Report
    HTTPFail --> Report
    DBFail --> Report
    NetFail --> Report
    InternetFail --> Report
    Success --> Report

    Report --> End([Return Results])

    style DNSFail fill:#fdd
    style BlockFail fill:#fdd
    style FTLFail fill:#fdd
    style DBFail fill:#fdd
    style Success fill:#e1ffe1
```

**Health Check Script**:
```bash
#!/bin/bash

echo "=== Health Check ==="

# DNS Resolution
echo "Testing DNS resolution..."
dig @localhost google.com +short || echo "❌ DNS FAIL"

# Blocking Test
echo "Testing blocking..."
dig @localhost ads.example.com +short | grep "0.0.0.0" || echo "❌ BLOCKING FAIL"

# Service Status
echo "Checking services..."
systemctl is-active pihole-FTL || echo "❌ FTL DOWN"
systemctl is-active lighttpd || echo "❌ WEB DOWN"

# Database Integrity
echo "Checking databases..."
sqlite3 /etc/pihole/gravity.db "PRAGMA integrity_check;" || echo "❌ DB CORRUPT"

# Network
echo "Checking network..."
ping -c 1 8.8.8.8 || echo "❌ NETWORK DOWN"

echo "✅ Health check complete"
```

---

## Sprint-Based Deployment

```mermaid
gantt
    title Sprint Deployment Timeline (2 weeks)
    dateFormat  YYYY-MM-DD
    section Planning
    Sprint Planning           :a1, 2025-11-18, 1d
    Create Release Branch     :a2, after a1, 1d

    section Implementation
    Feature Development       :b1, after a2, 7d
    Local Testing             :b2, after b1, 2d
    Test Pi Deployment        :b3, after b2, 1d

    section Review
    Final UAT                 :c1, after b3, 1d
    Request Approval          :c2, after c1, 1d
    Production Deployment     :crit, c3, after c2, 1d
    Monitoring                :c4, after c3, 2d

    section Closure
    Sprint Retrospective      :d1, after c4, 1d
```

**Sprint Deployment Stages**:

1. **Planning** (Day 1-2):
   - Create `release/sprint-N` branch
   - Update `.claude/knowledge/deployment-flows.kd`
   - Notify all agents

2. **Implementation** (Day 3-10):
   - Feature branches merge to release branch
   - Continuous local testing
   - UAT verification per feature

3. **Review** (Day 11-14):
   - Deploy to Test Pi
   - Final UAT pass
   - Request user approval
   - Deploy to Production Pi
   - Monitor for 48 hours

4. **Closure** (Day 15):
   - Sprint retrospective
   - Update knowledge base
   - Merge release branch to main

---

## Deployment Checklist

### Pre-Deployment

- [ ] Local tests pass
- [ ] Knowledge base updated (BLOCKING protocol)
- [ ] Git branch correct (feature → release → main)
- [ ] Test Pi deployment successful
- [ ] UAT verification complete
- [ ] User approval obtained (for production)
- [ ] Backup created (for production)

### Deployment

- [ ] SSH connection established
- [ ] Files transferred successfully
- [ ] Dependencies installed
- [ ] Services configured
- [ ] Smoke tests pass
- [ ] Health checks pass

### Post-Deployment

- [ ] Monitoring active (5-30 minutes)
- [ ] Logs reviewed
- [ ] Network stability confirmed
- [ ] Knowledge base updated
- [ ] Deployment documented

---

## Safety Mechanisms

```mermaid
flowchart LR
    subgraph Safety Measures
        Backup[Mandatory Backup<br/>Before Production]
        Approval[User Approval<br/>Production Only]
        Health[Health Checks<br/>All Environments]
        Rollback[Rollback Capability<br/>Always Available]
        Monitor[Post-Deploy Monitoring<br/>Production]
    end

    Deployment[Deployment] --> Backup
    Backup --> Approval
    Approval --> Deploy[Execute Deploy]
    Deploy --> Health
    Health -->|Fail| Rollback
    Health -->|Pass| Monitor
    Monitor -->|Issues| Rollback
    Monitor -->|Stable| Success[Deployment Complete]

    style Backup fill:#e1f5ff
    style Approval fill:#fdd
    style Rollback fill:#ffe1e1
```

---

## Environment-Specific Configuration

### Development

```yaml
environment: development
python_version: 3.11+
venv_path: ~/.pihole-manager-venv
ssh_mock: true
pi_required: false
approval: none
autonomy: full
```

### Test Pi

```yaml
environment: test-pi
host: test-pi.local
ssh_user: pi
ssh_key: ~/.ssh/pihole_ed25519
pihole_installed: true
network: isolated-test-network
approval: auto-after-local-pass
autonomy: high
```

### Production Pi

```yaml
environment: production
host: pihole.local
ssh_user: pi
ssh_key: ~/.ssh/pihole_ed25519
pihole_installed: true
network: production-network
network_critical: true
approval: user-mandatory
autonomy: restricted
backup_before_deploy: mandatory
monitoring: post-deploy-required
```

---

## References

- **KDL Files**: `.claude/knowledge/deployment-flows.kd`, `.claude/knowledge/environment-config.kd`
- **Agent Coordination**: `docs/agent-coordination.md`
- **Deployment Procedures (legacy)**: `docs/deployment-procedures.md`

---

## Quick Reference

**Deploy to Test Pi**:
```bash
ssh pi@test-pi.local "mkdir -p ~/pihole-network-manager"
scp -r * pi@test-pi.local:~/pihole-network-manager/
ssh pi@test-pi.local "cd ~/pihole-network-manager && sudo python3 setup.py"
```

**Deploy to Production** (after approval):
```bash
ssh pi@pihole.local "sudo ~/pihole-network-manager/backup.sh"
scp -r * pi@pihole.local:~/pihole-network-manager-new/
ssh pi@pihole.local "sudo mv ~/pihole-network-manager ~/pihole-network-manager-backup && sudo mv ~/pihole-network-manager-new ~/pihole-network-manager"
ssh pi@pihole.local "cd ~/pihole-network-manager && python3 health_check.py"
```

**Rollback**:
```bash
ssh pi@pihole.local "sudo mv ~/pihole-network-manager ~/pihole-network-manager-failed && sudo mv ~/pihole-network-manager-backup ~/pihole-network-manager"
ssh pi@pihole.local "sudo systemctl restart pihole-FTL"
```
