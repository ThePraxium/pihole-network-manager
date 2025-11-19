# Agent Coordination and Workflows

**Version**: 1.0
**Last Updated**: 2025-11-18
**Paired KDL**: `.claude/knowledge/agent-workflows.kd`

---

## Overview

The Pi-hole Network Manager uses a **multi-agent development system** where specialized AI agents coordinate through structured workflows. This document visualizes how agents interact, coordinate through the BLOCKING protocol, and execute GitScrum sprints.

---

## Agent Roles and Responsibilities

```mermaid
graph TB
    subgraph Agents
        SL[Scrum Leader<br/>Sprint Orchestration<br/>GitHub Issues<br/>Release Management]
        KM[Knowledge Manager<br/>KDL File Maintenance<br/>BLOCKING Protocol<br/>Validation]
        PD[Python Developer<br/>Code Implementation<br/>Local Testing<br/>Feature Development]
        PI[Pi Infrastructure<br/>Pi Configuration<br/>SSH Setup<br/>Systemd Services]
        UAT[UAT Pro<br/>Testing & Verification<br/>Deployment<br/>Quality Reports]
    end

    SL -->|Orchestrates| PD
    SL -->|Orchestrates| PI
    SL -->|Orchestrates| UAT
    PD -->|Updates Knowledge| KM
    PI -->|Updates Knowledge| KM
    UAT -->|Updates Knowledge| KM
    KM -->|Validates & Confirms| PD
    KM -->|Validates & Confirms| PI
    KM -->|Validates & Confirms| UAT

    style KM fill:#f9f,stroke:#333,stroke-width:4px
    style SL fill:#bbf,stroke:#333,stroke-width:2px
```

**Key Characteristics:**
- **Scrum Leader**: Central orchestrator, no blocking on its own actions
- **Knowledge Manager**: MANDATORY coordination point - enforces BLOCKING protocol
- **Python Developer**: Implements features, coordinates with Knowledge Manager
- **Pi Infrastructure**: Handles Pi-side configuration and services
- **UAT Pro**: Autonomous test execution, reports to Scrum Leader

---

## BLOCKING Protocol

The BLOCKING protocol ensures knowledge synchronization across all agents before proceeding with tasks.

```mermaid
sequenceDiagram
    participant Agent as Any Agent
    participant KM as Knowledge Manager
    participant KDL as .kd Files

    Agent->>KM: 1. Request knowledge update<br/>(sends KDL entry)
    activate KM
    Note over Agent: Agent BLOCKS<br/>and waits
    KM->>KM: 2. Validate syntax
    KM->>KDL: 3. Update .kd file
    KM->>KM: 4. Git commit
    KM->>Agent: 5. Confirmation<br/>(line number)
    deactivate KM
    Note over Agent: Agent UNBLOCKS<br/>and proceeds
    Agent->>Agent: 6. Continue with task
```

**Protocol Steps:**

1. **Request** - Agent sends KDL-formatted entry to Knowledge Manager
2. **Validate** - Knowledge Manager validates syntax against schema
3. **Update** - Knowledge Manager updates appropriate .kd file
4. **Commit** - Knowledge Manager commits change to git
5. **Confirm** - Knowledge Manager sends confirmation with line number
6. **Proceed** - Agent unblocks and continues execution

**Why BLOCKING?**
- Ensures all agents have synchronized knowledge
- Prevents drift between agent understanding and system reality
- Creates audit trail of knowledge changes
- Enforces validation before persistence

---

## GitScrum Sprint Workflow

```mermaid
graph LR
    subgraph Sprint Phases
        A[Planning<br/>1-2 hours] --> B[Implementation<br/>1.5 weeks]
        B --> C[Review<br/>2-3 days]
        C --> D[Retrospective<br/>30 minutes]
    end

    D -.->|Next Sprint| A

    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#e1ffe1
    style D fill:#ffe1f5
```

### Sprint Phase Details

#### 1. Planning (1-2 hours)

```mermaid
flowchart TD
    Start([Sprint Planning]) --> Backlog[Review Backlog]
    Backlog --> Scope[Define Scope]
    Scope --> Branch[Create release/sprint-N branch]
    Branch --> Knowledge[Update Knowledge Base<br/>BLOCKING protocol]
    Knowledge --> Notify[Notify All Agents]
    Notify --> End([Start Implementation])
```

**Artifacts:**
- Sprint backlog (GitHub issues)
- Release branch (`release/sprint-N`)
- Updated `.claude/knowledge/deployment-flows.kd`

#### 2. Implementation (1.5 weeks)

```mermaid
flowchart TD
    Start([Implementation]) --> Feature[Create Feature Branch]
    Feature --> Implement[Python Dev Implements]
    Implement --> LocalTest[Local Testing]
    LocalTest -->|Pass| KM1[Update Knowledge<br/>BLOCKING]
    LocalTest -->|Fail| Implement
    KM1 --> UAT1[UAT Verify Local]
    UAT1 -->|Pass| PR[Create Pull Request]
    UAT1 -->|Fail| Implement
    PR --> TestPi[Deploy to Test Pi]
    TestPi --> UAT2[UAT Integration Tests]
    UAT2 -->|Pass| Merge[Merge to release/sprint-N]
    UAT2 -->|Fail| Implement
    Merge --> KM2[Update Knowledge<br/>BLOCKING]
    KM2 --> End([Feature Complete])
```

**Quality Gates:**
- ✅ Local tests pass
- ✅ Knowledge base updated
- ✅ UAT verification pass
- ✅ Test Pi integration pass

#### 3. Review (2-3 days)

```mermaid
flowchart TD
    Start([Sprint Review]) --> Verify[Verify All Complete]
    Verify --> Deploy1[Deploy to Test Pi]
    Deploy1 --> UAT[Final UAT Pass]
    UAT -->|Pass| Approval[Request User Approval]
    UAT -->|Fail| Fix[Fix Issues]
    Fix --> Deploy1
    Approval -->|Approved| Deploy2[Deploy to Production Pi]
    Approval -->|Rejected| Fix
    Deploy2 --> Health[Health Checks]
    Health -->|Pass| Close[Sprint Closure]
    Health -->|Fail| Rollback[Rollback]
    Rollback --> Fix
    Close --> KM[Update Knowledge<br/>BLOCKING]
    KM --> End([Sprint Complete])
```

**Deliverables:**
- Production deployment
- Updated knowledge base
- Sprint metrics

#### 4. Retrospective (30 minutes)

```mermaid
flowchart LR
    Start([Retrospective]) --> Metrics[Review Metrics]
    Metrics --> Learnings[Document Learnings]
    Learnings --> Improvements[Identify Improvements]
    Improvements --> Plan[Plan Next Sprint]
    Plan --> End([Retrospective Complete])
```

---

## Feature Development Workflow

```mermaid
flowchart TD
    Start([New Feature]) --> Branch[Create feature/issue-N-description]
    Branch --> Implement[Python Dev: Implement Feature]
    Implement --> KM1[Knowledge Manager:<br/>Update code-architecture.kd<br/>BLOCKING]
    KM1 --> LocalTest[Python Dev: Local Tests]
    LocalTest -->|Fail| Implement
    LocalTest -->|Pass| UAT1[UAT: Verify Local]
    UAT1 -->|Fail| Implement
    UAT1 -->|Pass| PR[Create Pull Request<br/>→ release/sprint-N]
    PR --> TestDeploy[UAT: Deploy to Test Pi]
    TestDeploy --> UAT2[UAT: Integration Tests]
    UAT2 -->|Fail| Implement
    UAT2 -->|Pass| Merge[Merge to release/sprint-N]
    Merge --> DeleteBranch[Delete Feature Branch]
    DeleteBranch --> KM2[Knowledge Manager:<br/>Update deployment-flows.kd<br/>BLOCKING]
    KM2 --> End([Feature Complete])

    style KM1 fill:#f9f
    style KM2 fill:#f9f
```

---

## Bug Fix Workflow

```mermaid
flowchart TD
    Start([Bug Reported]) --> Triage[Scrum Leader: Triage]
    Triage --> GH[Create GitHub Issue<br/>Labels: bug, priority, component]
    GH --> KM1[Knowledge Manager:<br/>Add to troubleshooting.kd<br/>BLOCKING]
    KM1 --> Assess{Severity?}

    Assess -->|Emergency| Emergency[Emergency Hotfix Path]
    Assess -->|Normal| Batch[Batch with Other Bugs<br/>3-5 issues per hotfix branch]

    Batch --> HotfixBranch[Create hotfix/batch-N]
    Emergency --> EmergencyBranch[Create hotfix/emergency-issue-N]

    HotfixBranch --> Fix[Python Dev or Pi Infra:<br/>Implement Fix]
    EmergencyBranch --> Fix

    Fix --> LocalTest[Local Tests<br/>Focused Scope]
    LocalTest -->|Fail| Fix
    LocalTest -->|Pass| TestDeploy[UAT: Deploy to Test Pi]
    TestDeploy --> Regression[UAT: Regression Tests]
    Regression -->|Fail| Fix
    Regression -->|Pass| Approve{Go/No-Go?}

    Approve -->|No-Go| Fix
    Approve -->|Go| Merge[Merge to release/sprint-N]
    Merge --> KM2[Knowledge Manager:<br/>Update troubleshooting.kd<br/>Mark resolved<br/>BLOCKING]
    KM2 --> End([Bug Fixed])

    style KM1 fill:#f9f
    style KM2 fill:#f9f
    style Emergency fill:#fdd
```

**Bug Batching Strategy:**
- Group 3-5 related bugs per hotfix branch
- Reduces context switching
- Easier regression testing
- More efficient PR reviews

**Emergency Hotfix Criteria:**
- Network-critical DNS failures
- Security vulnerabilities
- Complete service outages
- Data corruption risks

---

## Deployment Coordination

```mermaid
graph TB
    subgraph Deployment Environments
        Dev[Development<br/>Local Computer<br/>No Approval<br/>Full Autonomy]
        TestPi[Test Pi<br/>test-pi.local<br/>Auto-Approval after Local<br/>Autonomous Deployment]
        ProdPi[Production Pi<br/>pihole.local<br/>USER APPROVAL REQUIRED<br/>Restricted Autonomy]
    end

    Dev -->|Local Tests Pass| TestPi
    TestPi -->|UAT Pass| Request[Request User Approval]
    Request -->|Approved| ProdPi
    Request -->|Rejected| Dev

    ProdPi -->|Health Check Fail| Rollback[Rollback]
    Rollback --> Dev

    style Dev fill:#e1f5ff
    style TestPi fill:#fff4e1
    style ProdPi fill:#ffe1e1
```

### Deployment Flow Details

```mermaid
sequenceDiagram
    participant PD as Python Dev
    participant UAT as UAT Agent
    participant SL as Scrum Leader
    participant User as User
    participant KM as Knowledge Manager

    Note over PD: Local Environment
    PD->>PD: Implement & Test Locally
    PD->>KM: Update knowledge (BLOCKING)
    KM-->>PD: Confirmed

    Note over UAT: Test Pi Environment
    PD->>UAT: Request Test Pi Deployment
    UAT->>UAT: Deploy to Test Pi<br/>(Autonomous)
    UAT->>UAT: Run Integration Tests
    UAT->>SL: Report: PASS

    Note over SL,User: Production Pi Environment
    SL->>User: Request Approval for Production
    User-->>SL: Approved
    SL->>UAT: Deploy to Production Pi
    UAT->>UAT: Deploy with Backup
    UAT->>UAT: Run Health Checks
    UAT->>UAT: Monitor Services
    UAT->>SL: Report: Deployment Success
    SL->>KM: Update deployment status (BLOCKING)
    KM-->>SL: Confirmed
```

---

## Agent Communication Patterns

```mermaid
flowchart LR
    subgraph Communication Types
        A[Delegation<br/>Async, No Wait]
        B[Blocking Request<br/>Sync, Must Wait]
        C[Verification Request<br/>Async, Report Expected]
        D[Approval Request<br/>Sync, User Must Confirm]
    end

    A -.->|Example| A1["Scrum Leader → Python Dev<br/>'Implement issue #47'"]
    B -.->|Example| B1["Any Agent → Knowledge Manager<br/>'Update KDL file'<br/>AGENT BLOCKS"]
    C -.->|Example| C1["Python Dev → UAT<br/>'Verify deployment'"]
    D -.->|Example| D1["Scrum Leader → User<br/>'Approve production deploy?'<br/>AGENT BLOCKS"]

    style B fill:#f9f
    style D fill:#fdd
```

---

## Multi-Agent Coordination Matrix

| Workflow Type | Agents Involved | Sequence | Blocking Point |
|---------------|----------------|----------|----------------|
| **Feature Development** | Scrum Leader, Python Dev, UAT, Knowledge Manager | Sequential | Knowledge Manager |
| **Bug Fix** | Scrum Leader, Python/Pi Infra, UAT, Knowledge Manager | Sequential | Knowledge Manager |
| **Sprint Execution** | All Agents | Parallel within phase | Knowledge Manager (sync points) |
| **Deployment** | Scrum Leader, UAT, Knowledge Manager | Sequential | User Approval + Knowledge Manager |

---

## Quality Gates

```mermaid
flowchart LR
    subgraph Quality Gates
        G1[Local Tests Pass<br/>Owner: Python Dev<br/>Blocker: YES]
        G2[Test Pi UAT Pass<br/>Owner: UAT Agent<br/>Blocker: YES]
        G3[Knowledge Sync<br/>Owner: Knowledge Manager<br/>Blocker: YES]
        G4[User Approval<br/>Owner: User<br/>Blocker: YES]
        G5[Health Checks Pass<br/>Owner: Pi Infrastructure<br/>Blocker: YES]
    end

    G1 --> G2
    G2 --> G3
    G3 --> G4
    G4 --> G5

    style G1 fill:#e1f5ff
    style G2 fill:#fff4e1
    style G3 fill:#f9f
    style G4 fill:#fdd
    style G5 fill:#e1ffe1
```

All quality gates are **BLOCKING** - workflow cannot proceed until gate passes.

---

## Knowledge Base Updates

```mermaid
flowchart TD
    Start([Knowledge Update Needed]) --> Type{Update Type}

    Type -->|New Module| CodeArch[code-architecture.kd]
    Type -->|Deployment| DeployFlow[deployment-flows.kd]
    Type -->|Bug/Issue| Trouble[troubleshooting.kd]
    Type -->|Environment| EnvConfig[environment-config.kd]
    Type -->|Workflow Change| AgentWork[agent-workflows.kd]

    CodeArch --> KM[Knowledge Manager<br/>BLOCKING Protocol]
    DeployFlow --> KM
    Trouble --> KM
    EnvConfig --> KM
    AgentWork --> KM

    KM --> Validate[Validate KDL Syntax]
    Validate -->|Invalid| Error[Return Error to Agent]
    Validate -->|Valid| Update[Update .kd File]
    Update --> Commit[Git Commit]
    Commit --> Confirm[Confirm to Agent<br/>with Line Number]
    Confirm --> End([Agent Unblocked])

    Error --> End

    style KM fill:#f9f
```

---

## Best Practices

### For Agents

1. **Always use BLOCKING protocol** when updating knowledge
2. **Wait for Knowledge Manager confirmation** before proceeding
3. **Include all required KDL attributes** in update requests
4. **Coordinate through Scrum Leader** for multi-agent tasks
5. **Report status** to appropriate agents (UAT → Scrum Leader, Python Dev → Knowledge Manager)

### For Knowledge Manager

1. **Validate ALL KDL syntax** before updates
2. **Commit changes immediately** after validation
3. **Confirm with line numbers** so agents can reference
4. **Reject invalid entries** with clear error messages
5. **Maintain .kd ↔ .md pairing** (update both when needed)

### For Scrum Leader

1. **Orchestrate, don't implement** - delegate to specialized agents
2. **Coordinate approval requests** for production deployments
3. **Track sprint progress** via GitHub issues
4. **Facilitate retrospectives** and document learnings
5. **Monitor quality gates** and escalate blockers

---

## References

- **KDL Schema**: `.claude/knowledge/_schema.md`
- **KDL File**: `.claude/knowledge/agent-workflows.kd`
- **Deployment Procedures**: `docs/deployment-procedures.md`
- **Environment Configuration**: `docs/environment-config.md`

---

## Glossary

- **BLOCKING Protocol**: Synchronous coordination mechanism requiring Knowledge Manager confirmation
- **GitScrum**: Agile methodology using Git branches + Scrum sprints
- **Quality Gate**: Required checkpoint that must pass before proceeding
- **KDL**: Knowledge Definition Language - ultra-compact knowledge encoding format
- **UAT**: User Acceptance Testing - integration and verification testing
