# UAT Fixes Todo List

**Created**: 2025-11-20
**Source**: Pre-UAT Discovery Phase Results
**Status**: Issues identified, priorities assigned

---

## Priority Legend

- 🔴 **P0 - Critical**: Blocks core functionality, must fix immediately
- 🟠 **P1 - High**: Major functionality impaired, fix before next release
- 🟡 **P2 - Medium**: Notable issues, fix when possible
- 🟢 **P3 - Low**: Minor improvements, nice to have

---

## Critical Issues (P0)

### ✅ FIXED: Issue #1 - Pi-hole Installation Corruption
**Status**: ✅ Resolved during pre-testing
**Severity**: 🔴 P0 - Critical
**Category**: Setup / Installation
**Module**: pi-setup/

**Problem**:
- `/opt/pihole/` directory completely missing after setup wizard
- pihole-FTL service failed to start (status 203/EXEC)
- All pihole commands non-functional
- Setup wizard reported success but installation was incomplete

**Root Cause**:
- Pi-hole installation script failure or incomplete execution
- Setup wizard marked pihole_install as complete without verification
- No health check to verify /opt/pihole/ directory exists

**Resolution Applied**:
- Manually reinstalled Pi-hole using official installer
- Verified service operational
- All checks passing

**Permanent Fix Required**:
1. **Add installation verification to setup wizard**:
   - File: `pi-setup/setup.py` (pihole_install module)
   - Check `/opt/pihole/` directory exists after installation
   - Verify `pihole` command works
   - Test pihole-FTL service status
   - Don't mark complete until verified

2. **Add startup health check to main.py**:
   - Before showing main menu, verify:
     - `/opt/pihole/` directory exists
     - `pihole-FTL` service is running
     - `/etc/pihole/gravity.db` exists and is readable
   - If checks fail, show error with repair instructions

3. **Add repair option to maintenance menu**:
   - New option: "Repair Pi-hole Installation"
   - Runs: `curl -sSL https://install.pi-hole.net | sudo bash`
   - Useful for recovery from this type of failure

**Estimated Effort**: 4-6 hours
- Verification logic: 2 hours
- Startup checks: 1 hour
- Repair option: 1 hour
- Testing: 2 hours

**Files to Modify**:
- `pi-setup/setup.py` (pihole_install module)
- `main.py` (add health check before menu)
- `management/maintenance.py` (add repair option)
- `docs/troubleshooting-guide.md` (document fix)

---

## Medium Issues (P2)

### ✅ FIXED: Issue #2 - Log Directory Permission Denied
**Status**: ✅ Resolved during pre-testing
**Severity**: 🟡 P2 - Medium
**Category**: Configuration / Permissions
**Module**: core/logger.py, pi-setup/

**Problem**:
- Logger fails to write to `/opt/pihole-network-manager/logs/` directory
- Error: `[Errno 13] Permission denied`
- Directory owned by root:root, application runs as pihole user
- Session logging disabled, no audit trail

**Root Cause**:
- `initial-setup.sh` doesn't set correct ownership on logs/ directory
- Application assumes write permission to logs/

**Resolution Applied**:
- Manually changed ownership: `sudo chown -R pihole:pihole logs/`
- Logging now functional

**Permanent Fix Required**:
1. **Fix initial-setup.sh**:
   - File: `pi-setup/initial-setup.sh`
   - After creating directories, add:
     ```bash
     chown -R $USER:$USER /opt/pihole-network-manager/logs
     chmod 755 /opt/pihole-network-manager/logs
     ```

2. **Add fallback logging**:
   - File: `core/logger.py`
   - If `/opt/pihole-network-manager/logs/` fails, try `/tmp/pihole-manager-*.log`
   - Show warning but don't prevent app from starting

3. **Add permission check on startup**:
   - File: `main.py`
   - Check logs/ is writable before starting logger
   - If not, show friendly warning:
     ```
     Warning: Cannot write to logs/ directory
     Run: sudo chown -R $USER:$USER /opt/pihole-network-manager/logs
     Logging to /tmp/ instead
     ```

**Estimated Effort**: 2-3 hours
- Fix setup script: 30 minutes
- Add fallback: 1 hour
- Permission check: 30 minutes
- Testing: 1 hour

**Files to Modify**:
- `pi-setup/initial-setup.sh`
- `core/logger.py`
- `main.py`

---

### Issue #3 - sqlite3 Command Not Installed
**Status**: ⚠️ Open
**Severity**: 🟡 P2 - Medium
**Category**: Dependencies
**Module**: pi-setup/

**Problem**:
- `sqlite3` command not available for direct database queries
- Some documentation examples won't work
- Manual troubleshooting more difficult

**Root Cause**:
- Not included in system dependencies
- Not in `initial-setup.sh` or requirements.txt

**Impact**:
- Application still works (uses Python's sqlite3 library)
- Only affects manual troubleshooting and documentation examples

**Fix Required**:
1. **Add to system dependencies**:
   - File: `pi-setup/initial-setup.sh`
   - Add `sqlite3` to apt-get install list:
     ```bash
     sudo apt-get install -y python3 sqlite3 git ...
     ```

2. **Update documentation**:
   - File: `docs/troubleshooting-guide.md`
   - Add note about sqlite3 dependency
   - Provide alternative Python commands for manual queries

3. **Add dependency check**:
   - File: `management/health.py`
   - Add to health check: verify sqlite3 command exists
   - If missing, warn user and suggest: `sudo apt-get install sqlite3`

**Estimated Effort**: 1-2 hours
- Update setup script: 15 minutes
- Update docs: 30 minutes
- Add health check: 30 minutes
- Testing: 30 minutes

**Files to Modify**:
- `pi-setup/initial-setup.sh`
- `docs/troubleshooting-guide.md`
- `management/health.py` (database integrity check)

---

## Potential Issues (Identified but not confirmed)

### Issue #4 - query_database Return Type Error
**Status**: ⚠️ Suspected
**Severity**: 🟠 P1 - High (if confirmed)
**Category**: Code / Bug
**Module**: core/local_executor.py

**Problem**:
- During testing, got error: `'bool' object is not subscriptable`
- Suggests `query_database()` returning boolean instead of tuple/list
- May affect all database query operations

**Investigation Needed**:
1. Review `core/local_executor.py` implementation
2. Check return values in error conditions
3. Test with various query scenarios
4. Verify error handling

**Potential Fix**:
- Ensure `query_database()` always returns list/tuple
- On error, return empty list [] instead of False
- Add proper error handling and logging
- Update docstrings to clarify return types

**Estimated Effort**: 2-3 hours (after investigation)

**Priority**: 🟠 P1 if confirmed (affects many operations)

---

## Enhancements (Not blocking)

### Enhancement #1 - Add Automated Testing Support
**Severity**: 🟢 P3 - Low
**Category**: Testing / Quality

**Description**:
- Current TUI makes automated testing difficult
- Consider adding programmatic interface for CI/CD testing

**Suggestions**:
1. Add `--test-mode` flag to bypass interactive prompts
2. Create test fixtures for each module
3. Add unit tests for core utilities
4. Add integration tests that don't require TUI

**Estimated Effort**: 8-16 hours

**Benefits**:
- Faster testing cycles
- Regression detection
- CI/CD integration

---

### Enhancement #2 - Improve Error Messages
**Severity**: 🟢 P3 - Low
**Category**: UX / Usability

**Description**:
- Current error messages could be more actionable
- Link to troubleshooting guide when appropriate

**Examples**:
- Permission denied → Suggest chmod/chown command
- Service not running → Suggest repair option
- Database locked → Suggest waiting or restart

**Estimated Effort**: 4-6 hours

---

## Testing Blockers Removed

✅ **Pi-hole service operational** (Issue #1 fixed)
✅ **Application launches successfully** (Issue #2 fixed)
✅ **Environment verified stable**

**System is now READY for comprehensive UAT testing.**

---

## Summary

| Category | Total | Fixed | Open | In Progress |
|----------|-------|-------|------|-------------|
| Critical (P0) | 1 | 1 | 0 | 0 |
| High (P1) | 1 | 0 | 0 | 1 |
| Medium (P2) | 2 | 1 | 1 | 0 |
| Low (P3) | 2 | 0 | 2 | 0 |
| **Total** | **6** | **2** | **3** | **1** |

---

## Recommended Action Plan

### Phase 1: Immediate Fixes (Before next UAT session)
**Duration**: 1 day
**Priority**: P2 issues

1. Install sqlite3: `sudo apt-get install sqlite3` (5 minutes)
2. Fix logs permissions in setup script (30 minutes)
3. Add fallback logging to /tmp (1 hour)
4. Test fixes (1 hour)

### Phase 2: Critical Improvements (Before production)
**Duration**: 1-2 days
**Priority**: P0 and P1 issues

1. Add Pi-hole installation verification (2 hours)
2. Add startup health checks (1 hour)
3. Investigate and fix query_database issue (3 hours)
4. Add repair option to maintenance menu (1 hour)
5. Comprehensive testing (4 hours)

### Phase 3: Enhancements (Post-production)
**Duration**: 1 week
**Priority**: P3 issues

1. Improve error messages (1 day)
2. Add automated testing support (2-3 days)
3. Documentation updates (1 day)

---

## Next Steps for Manual UAT

**Prerequisites (All met ✅)**:
- ✅ Pi-hole operational
- ✅ Application launches
- ✅ Logging functional
- ✅ Comprehensive guide available

**Testing Instructions**:
1. SSH into Pi-hole: `ssh -i ~/.ssh/pihole_rsa pihole@192.168.0.12`
2. Navigate to app: `cd /opt/pihole-network-manager`
3. Launch app: `python3 main.py`
4. Follow: `docs/uat-testing-guide.md`
5. Document results using template
6. Estimated time: 3-4 hours for 51 operations

**Deliverables from Manual UAT**:
- Detailed test results for each operation
- Screenshots/output samples (optional)
- Bug reports for new issues found
- UX feedback
- Performance observations

---

## Files Referenced

- **UAT Guide**: `docs/uat-testing-guide.md`
- **UAT Results**: `docs/uat-results-20251120.md`
- **Troubleshooting**: `docs/troubleshooting-guide.md`
- **Setup Script**: `pi-setup/initial-setup.sh`
- **Logger**: `core/logger.py`
- **Main Entry**: `main.py`

---

**Document Status**: ✅ Complete
**Last Updated**: 2025-11-20
**Next Review**: After comprehensive UAT session

---

*Created by Claude Code AI Assistant based on pre-UAT discovery phase findings.*
