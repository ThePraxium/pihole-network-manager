# User Acceptance Testing (UAT) Guide

**Version**: 1.0
**Created**: 2025-11-20
**Purpose**: Comprehensive testing guide for all Pi-hole Network Manager features

---

## Overview

This guide provides a systematic approach to testing all 51 operations across 7 management modules. Each test includes expected behavior, test data suggestions, and known limitations.

**Testing Environment**:
- Raspberry Pi 4 with Pi-hole installed
- Fresh Pi-hole installation (or known clean state)
- Network connectivity for updates and external tests

**Testing Approach**:
1. Execute each operation in sequence
2. Document actual output vs expected output
3. Check session logs (`/tmp/pihole-manager-*.log`)
4. Note any errors, warnings, or unexpected behavior
5. Categorize issues by severity

---

## Module 1: Blocklist Management (8 Operations)

### Operation 1.1: View Current Blocklist Profile
**Menu Path**: Management → Blocklist Management → View Current Profile
**Expected Output**:
- Current profile name (Light/Moderate/Aggressive/Custom)
- Total domains blocked (~100K / ~300K / ~1M+)
- Last updated timestamp
**Test Data**: N/A (read-only)
**Known Issues**: None

### Operation 1.2: Switch to Light Profile
**Menu Path**: Management → Blocklist Management → Switch Profile → Light
**Expected Output**:
- Confirmation prompt
- Gravity rebuild progress indicator
- Success message with new domain count (~100K)
- Profile saved in config
**Test Data**: None required
**Duration**: 2-5 minutes
**Known Issues**: May timeout on slow Pi or slow network

### Operation 1.3: Switch to Moderate Profile
**Menu Path**: Management → Blocklist Management → Switch Profile → Moderate
**Expected Output**:
- Confirmation prompt
- Gravity rebuild progress
- Success message (~300K domains)
**Test Data**: None required
**Duration**: 5-10 minutes
**Known Issues**: Long rebuild time on older Pi models

### Operation 1.4: Switch to Aggressive Profile
**Menu Path**: Management → Blocklist Management → Switch Profile → Aggressive
**Expected Output**:
- Confirmation prompt
- Gravity rebuild progress
- Success message (~1M+ domains)
- Warning about potential breakage
**Test Data**: None required
**Duration**: 10-20 minutes
**Known Issues**: Can cause legitimate site breakage

### Operation 1.5: View Blocklist URLs
**Menu Path**: Management → Blocklist Management → View Blocklist URLs
**Expected Output**:
- Table of current blocklist URLs
- Comment/description for each URL
- Enabled status
**Test Data**: N/A (read-only)
**Known Issues**: None

### Operation 1.6: Add Custom Blocklist URL
**Menu Path**: Management → Blocklist Management → Add Custom URL
**Expected Output**:
- Prompt for URL input
- Prompt for comment/description
- Confirmation of insertion
- Gravity rebuild prompt
**Test Data**: `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts`
**Known Issues**: Must manually trigger gravity rebuild

### Operation 1.7: Remove Blocklist URL
**Menu Path**: Management → Blocklist Management → Remove URL
**Expected Output**:
- List of current URLs
- Prompt to select URL to remove
- Confirmation prompt
- Success message
- Gravity rebuild prompt
**Test Data**: Use URL from operation 1.6
**Known Issues**: Gravity rebuild required for changes to apply

### Operation 1.8: Update Gravity Database
**Menu Path**: Management → Blocklist Management → Update Gravity
**Expected Output**:
- Progress indicator
- Download statistics
- New domain count
- Success/failure message
**Test Data**: None required
**Duration**: Varies (2-20 minutes depending on profile)
**Known Issues**: Can timeout on slow network

---

## Module 2: Device Management (7 Operations)

### Operation 2.1: List All Devices
**Menu Path**: Management → Device Management → List Devices
**Expected Output**:
- Table with columns: IP, MAC, Hostname, Last Query, Query Count
- All devices that have made DNS queries
**Test Data**: N/A (read-only)
**Known Issues**: Only shows devices that made DNS queries

### Operation 2.2: View Device Details
**Menu Path**: Management → Device Management → View Details → [select device]
**Expected Output**:
- IP address
- MAC address
- Hostname (if available)
- First seen timestamp
- Last query timestamp
- Total query count
- Recent queries (last 10)
**Test Data**: Select any device from list
**Known Issues**: None

### Operation 2.3: Set Custom DNS for Device
**Menu Path**: Management → Device Management → Custom DNS → [select device]
**Expected Output**:
- Current DNS setting
- Prompt for new DNS server
- Validation of DNS format
- Success message
- DHCP reservation note (manual step)
**Test Data**: `1.1.1.1` or `8.8.8.8`
**Known Issues**: Requires manual DHCP configuration on router

### Operation 2.4: Bypass Pi-hole for Device
**Menu Path**: Management → Device Management → Bypass Pi-hole → [select device]
**Expected Output**:
- Confirmation prompt
- Instructions for DHCP override
- Success message
**Test Data**: Any device IP
**Known Issues**: Requires manual DHCP configuration

### Operation 2.5: Set Device Friendly Name
**Menu Path**: Management → Device Management → Set Name → [select device]
**Expected Output**:
- Current name (if set)
- Prompt for new name
- Success message
- Updated device list
**Test Data**: "John's iPhone"
**Known Issues**: Name stored in app only, not in Pi-hole

### Operation 2.6: Group Devices
**Menu Path**: Management → Device Management → Group Devices
**Expected Output**:
- List of existing groups
- Prompt to create/edit group
- Device selection interface
- Success message
**Test Data**: Create "Family Devices" group
**Known Issues**: Grouping is cosmetic only

### Operation 2.7: Search Device by IP/MAC
**Menu Path**: Management → Device Management → Search
**Expected Output**:
- Prompt for IP or MAC
- Matching device details
- Recent query history
**Test Data**: Known device IP from operation 2.1
**Known Issues**: None

---

## Module 3: Whitelist/Blacklist (10 Operations)

### Operation 3.1: View Whitelist
**Menu Path**: Management → Whitelist/Blacklist → View Whitelist
**Expected Output**:
- Table of whitelisted domains
- Comment/reason for each
- Enabled status
**Test Data**: N/A (read-only)
**Known Issues**: None

### Operation 3.2: Add Domain to Whitelist
**Menu Path**: Management → Whitelist/Blacklist → Add to Whitelist
**Expected Output**:
- Prompt for domain
- Prompt for comment (optional)
- Confirmation message
- Gravity rebuild prompt
**Test Data**: `example.com`
**Known Issues**: Gravity rebuild required

### Operation 3.3: Remove Domain from Whitelist
**Menu Path**: Management → Whitelist/Blacklist → Remove from Whitelist
**Expected Output**:
- List of whitelisted domains
- Prompt to select domain
- Confirmation prompt
- Success message
- Gravity rebuild prompt
**Test Data**: `example.com` (from operation 3.2)
**Known Issues**: Gravity rebuild required

### Operation 3.4: View Blacklist
**Menu Path**: Management → Whitelist/Blacklist → View Blacklist
**Expected Output**:
- Table of blacklisted domains
- Comment/reason for each
- Enabled status
**Test Data**: N/A (read-only)
**Known Issues**: None

### Operation 3.5: Add Domain to Blacklist
**Menu Path**: Management → Whitelist/Blacklist → Add to Blacklist
**Expected Output**:
- Prompt for domain
- Prompt for comment (optional)
- Confirmation message
- Gravity rebuild prompt
**Test Data**: `ads.example.com`
**Known Issues**: Gravity rebuild required

### Operation 3.6: Remove Domain from Blacklist
**Menu Path**: Management → Whitelist/Blacklist → Remove from Blacklist
**Expected Output**:
- List of blacklisted domains
- Prompt to select domain
- Confirmation prompt
- Success message
- Gravity rebuild prompt
**Test Data**: `ads.example.com` (from operation 3.5)
**Known Issues**: Gravity rebuild required

### Operation 3.7: View Regex Filters
**Menu Path**: Management → Whitelist/Blacklist → View Regex Filters
**Expected Output**:
- Table of regex patterns
- Type (whitelist/blacklist)
- Comment
- Enabled status
**Test Data**: N/A (read-only)
**Known Issues**: None

### Operation 3.8: Add Regex Filter
**Menu Path**: Management → Whitelist/Blacklist → Add Regex
**Expected Output**:
- Prompt for regex pattern
- Prompt for type (whitelist/blacklist)
- Prompt for comment
- Validation of regex syntax
- Success message
**Test Data**: `^ad[sz]\..*\..+$` (blocks ads.example.com, adz.example.com)
**Known Issues**: Invalid regex can cause database errors

### Operation 3.9: Test Regex Pattern
**Menu Path**: Management → Whitelist/Blacklist → Test Regex
**Expected Output**:
- Prompt for regex pattern
- Prompt for test domain
- Match result (matched/not matched)
**Test Data**: Pattern: `^ad.*`, Domain: `ads.example.com`
**Known Issues**: None

### Operation 3.10: Bulk Import Domains
**Menu Path**: Management → Whitelist/Blacklist → Bulk Import
**Expected Output**:
- Prompt for file path or paste domains
- Format validation
- Import progress
- Summary (added/skipped/errors)
- Gravity rebuild prompt
**Test Data**: Create file with 5 domains, one per line
**Known Issues**: Large imports can be slow

---

## Module 4: Content Filtering (8 Operations)

### Operation 4.1: List All Rules
**Menu Path**: Management → Content Filtering → List Rules
**Expected Output**:
- Table of rules: ID, Name, Category, Status, Device Count, Schedule
- Enabled/disabled indicator
**Test Data**: N/A (read-only)
**Known Issues**: None

### Operation 4.2: Create Basic Rule (No Schedule)
**Menu Path**: Management → Content Filtering → Create Rule
**Expected Output**:
- Prompt for rule name
- Prompt for category
- Domain selection interface
- Device selection (all or specific)
- Confirmation and success message
**Test Data**:
- Name: "Block Facebook"
- Category: social_media
- Domains: facebook.com, *.facebook.com
- Devices: All
**Known Issues**: Rule created but not active until enabled

### Operation 4.3: Create Scheduled Rule
**Menu Path**: Management → Content Filtering → Create Rule → Enable Schedule
**Expected Output**:
- All prompts from 4.2
- Schedule configuration:
  - Start time (HH:MM)
  - End time (HH:MM)
  - Days of week
- Warning about manual enforcement
- Success message
**Test Data**:
- Name: "Block Social at Work"
- Schedule: 09:00-17:00, Mon-Fri
- Domains: facebook.com, twitter.com
**Known Issues**: **CRITICAL** - Schedule is not automated, manual enforcement required

### Operation 4.4: Enable Rule
**Menu Path**: Management → Content Filtering → Enable Rule
**Expected Output**:
- List of disabled rules
- Prompt to select rule
- Confirmation prompt
- Domains added to domainlist
- Gravity rebuild
- Success message
**Test Data**: Use rule from operation 4.2
**Known Issues**: Can take several minutes for gravity rebuild

### Operation 4.5: Disable Rule
**Menu Path**: Management → Content Filtering → Disable Rule
**Expected Output**:
- List of enabled rules
- Prompt to select rule
- Confirmation prompt
- Domains removed from domainlist
- Gravity rebuild
- Success message
**Test Data**: Use rule from operation 4.4
**Known Issues**: Gravity rebuild required

### Operation 4.6: View Rule Details
**Menu Path**: Management → Content Filtering → View Details → [select rule]
**Expected Output**:
- Rule name and ID
- Category
- Status (enabled/disabled)
- Domain list (all domains in rule)
- Device filter (all or specific IPs)
- Schedule details (if scheduled)
- Last modified timestamp
**Test Data**: Any existing rule
**Known Issues**: None

### Operation 4.7: Edit Rule
**Menu Path**: Management → Content Filtering → Edit Rule
**Expected Output**:
- Current rule details
- Prompts to modify each field
- Validation
- Confirmation
- Success message
**Test Data**: Modify rule from 4.2 (add another domain)
**Known Issues**: Editing enabled rule requires gravity rebuild

### Operation 4.8: Delete Rule
**Menu Path**: Management → Content Filtering → Delete Rule
**Expected Output**:
- List of rules
- Prompt to select rule
- Confirmation prompt (permanent action)
- Success message
- Note about gravity rebuild if rule was enabled
**Test Data**: Delete rule from operation 4.2
**Known Issues**: None

---

## Module 5: Statistics & Monitoring (9 Operations)

### Operation 5.1: View Query Dashboard
**Menu Path**: Management → Statistics & Monitoring → Query Dashboard
**Expected Output**:
- Total queries (today)
- Blocked queries (count and percentage)
- Queries per minute (average)
- Top blocked domain
- Top client
- Refresh/auto-update option
**Test Data**: N/A (read-only)
**Known Issues**: None

### Operation 5.2: View Top Domains (Allowed)
**Menu Path**: Management → Statistics & Monitoring → Top Domains → Allowed
**Expected Output**:
- Table: Domain, Hits, Percentage
- Top 10 (or configurable) allowed domains
- Total allowed queries
**Test Data**: N/A (read-only)
**Known Issues**: None

### Operation 5.3: View Top Domains (Blocked)
**Menu Path**: Management → Statistics & Monitoring → Top Domains → Blocked
**Expected Output**:
- Table: Domain, Hits, Percentage
- Top 10 blocked domains
- Total blocked queries
**Test Data**: N/A (read-only)
**Known Issues**: None

### Operation 5.4: View Top Clients
**Menu Path**: Management → Statistics & Monitoring → Top Clients
**Expected Output**:
- Table: Client IP/Hostname, Total Queries, Blocked Queries
- Top 10 clients by query count
**Test Data**: N/A (read-only)
**Known Issues**: Hostname resolution may fail for some IPs

### Operation 5.5: View Query Log (Real-time)
**Menu Path**: Management → Statistics & Monitoring → Query Log
**Expected Output**:
- Scrolling log of recent queries (last 100)
- Columns: Timestamp, Client, Domain, Type, Status
- Color coding (allowed/blocked)
- Refresh option
**Test Data**: N/A (read-only)
**Known Issues**: Can be overwhelming on busy networks

### Operation 5.6: Search Query History
**Menu Path**: Management → Statistics & Monitoring → Search Queries
**Expected Output**:
- Prompt for search term (domain or client)
- Prompt for time range
- Table of matching queries
- Export option
**Test Data**: Search for "google.com" in last 24 hours
**Known Issues**: Large time ranges can be slow

### Operation 5.7: Query Type Breakdown
**Menu Path**: Management → Statistics & Monitoring → Query Types
**Expected Output**:
- Pie chart or table
- A, AAAA, PTR, SRV, etc.
- Count and percentage for each type
**Test Data**: N/A (read-only)
**Known Issues**: Chart rendering may be ASCII/text-based

### Operation 5.8: View Query Trends (Placeholder)
**Menu Path**: Management → Statistics & Monitoring → Query Trends
**Expected Output**:
- Placeholder message or basic text-based graph
- Note about exporting data for analysis
**Test Data**: N/A
**Known Issues**: **LIMITATION** - Graphing not fully implemented

### Operation 5.9: Export Statistics to CSV
**Menu Path**: Management → Statistics & Monitoring → Export → CSV
**Expected Output**:
- Prompt for time range
- Prompt for output file path
- Export progress
- Success message with file location
- CSV file created with query data
**Test Data**: Export last 7 days to `/tmp/pihole-stats.csv`
**Known Issues**: Large exports can take time and disk space

---

## Module 6: Maintenance & Updates (9 Operations)

### Operation 6.1: Check Pi-hole Status
**Menu Path**: Management → Maintenance & Updates → Check Status
**Expected Output**:
- Pi-hole version
- FTL version
- Web interface version
- Service status (running/stopped)
- Uptime
**Test Data**: N/A (read-only)
**Known Issues**: None

### Operation 6.2: Update Pi-hole
**Menu Path**: Management → Maintenance & Updates → Update Pi-hole
**Expected Output**:
- Current version
- Available version (if update available)
- Confirmation prompt
- Update progress
- Success/failure message
- Service restart confirmation
**Test Data**: None required
**Duration**: 5-15 minutes
**Known Issues**: Requires internet connection, may require sudo password

### Operation 6.3: Update Raspberry Pi OS
**Menu Path**: Management → Maintenance & Updates → Update System
**Expected Output**:
- Update check progress
- List of available updates
- Confirmation prompt
- Update progress (can be lengthy)
- Success message
- Reboot recommendation if kernel updated
**Test Data**: None required
**Duration**: 10-60 minutes depending on updates
**Known Issues**: Can require significant disk space

### Operation 6.4: Restart Pi-hole Services
**Menu Path**: Management → Maintenance & Updates → Restart Services → Pi-hole
**Expected Output**:
- Confirmation prompt
- Service stop progress
- Service start progress
- Success message
- Service status verification
**Test Data**: None required
**Duration**: 5-10 seconds
**Known Issues**: Brief DNS outage during restart

### Operation 6.5: Restart System
**Menu Path**: Management → Maintenance & Updates → Reboot Pi
**Expected Output**:
- Warning about network outage
- Confirmation prompt (requires explicit yes)
- Reboot initiated message
- SSH connection lost (expected)
**Test Data**: None required
**Duration**: 30-90 seconds
**Known Issues**: Will disconnect session, must SSH back in

### Operation 6.6: View System Resources
**Menu Path**: Management → Maintenance & Updates → System Resources
**Expected Output**:
- CPU usage (current and average)
- RAM usage (used/total/percentage)
- Disk usage (used/total/percentage by partition)
- Temperature (°C)
- Load average (1/5/15 min)
- Uptime
**Test Data**: N/A (read-only)
**Known Issues**: None

### Operation 6.7: Clear Pi-hole Logs
**Menu Path**: Management → Maintenance & Updates → Clear Logs
**Expected Output**:
- Current log size
- Warning about permanent deletion
- Confirmation prompt
- Clearing progress
- Success message
- New log size verification
**Test Data**: None required
**Known Issues**: Cannot recover cleared logs

### Operation 6.8: Flush DNS Cache
**Menu Path**: Management → Maintenance & Updates → Flush Cache
**Expected Output**:
- Confirmation prompt
- Cache flush execution
- Success message
**Test Data**: None required
**Known Issues**: Can cause brief resolution delay

### Operation 6.9: View Service Status
**Menu Path**: Management → Maintenance & Updates → Service Status
**Expected Output**:
- Table of services:
  - pihole-FTL (status, uptime)
  - lighttpd (status, uptime)
  - SSH (status, uptime)
- Port status (53, 80, 22)
**Test Data**: N/A (read-only)
**Known Issues**: None

---

## Module 7: Health & Diagnostics (8 Operations)

### Operation 7.1: Run Full Health Check
**Menu Path**: Management → Health & Diagnostics → Full Health Check
**Expected Output**:
- Progress indicator for each check
- Results summary:
  - DNS resolution test (pass/fail)
  - Service status (pass/fail)
  - Database integrity (pass/fail)
  - Network connectivity (pass/fail)
  - Disk space (pass/warning/fail)
  - System resources (pass/warning/fail)
- Overall health score
- Recommendations for any failures
**Test Data**: None required
**Duration**: 30-60 seconds
**Known Issues**: None

### Operation 7.2: Test DNS Resolution
**Menu Path**: Management → Health & Diagnostics → Test DNS
**Expected Output**:
- Prompt for test domain (default: google.com)
- Resolution result:
  - Resolved IP addresses
  - Response time
  - Authoritative server
  - Query status
- Pass/fail indicator
**Test Data**: `google.com` or `example.com`
**Known Issues**: Fails if upstream DNS is down

### Operation 7.3: Test Ad Blocking
**Menu Path**: Management → Health & Diagnostics → Test Blocking
**Expected Output**:
- Test against known ad domains
- Results:
  - Domain, Expected (blocked), Actual (blocked/allowed), Status
- Overall pass/fail
- Note if blocklists need updating
**Test Data**: None required (uses built-in test domains)
**Known Issues**: May fail if blocklists are too aggressive or too light

### Operation 7.4: Check Service Status
**Menu Path**: Management → Health & Diagnostics → Service Check
**Expected Output**:
- pihole-FTL: running/stopped
- lighttpd: running/stopped
- SSH: running/stopped
- Port availability check
- Overall status: healthy/degraded/critical
**Test Data**: None required
**Known Issues**: None

### Operation 7.5: Test Network Connectivity
**Menu Path**: Management → Health & Diagnostics → Network Test
**Expected Output**:
- Tests:
  - Local gateway ping (pass/fail, latency)
  - Internet connectivity (8.8.8.8 ping)
  - DNS resolution (external DNS)
  - Speed test (optional, basic)
- Overall connectivity status
**Test Data**: None required
**Known Issues**: May fail on restricted networks

### Operation 7.6: Check Database Integrity
**Menu Path**: Management → Health & Diagnostics → Database Check
**Expected Output**:
- gravity.db integrity check (pass/fail)
- pihole-FTL.db integrity check (pass/fail)
- File permissions verification
- Database size
- Recommendations if corruption detected
**Test Data**: None required
**Known Issues**: Cannot auto-repair corruption

### Operation 7.7: View Error Logs
**Menu Path**: Management → Health & Diagnostics → View Logs
**Expected Output**:
- Recent errors from:
  - Pi-hole logs
  - FTL logs
  - System logs (relevant to Pi-hole)
- Timestamp, source, error message
- Severity level
**Test Data**: N/A (read-only)
**Known Issues**: Can be overwhelming on problematic systems

### Operation 7.8: Generate Diagnostic Report
**Menu Path**: Management → Health & Diagnostics → Generate Report
**Expected Output**:
- Comprehensive report generation progress
- Report includes:
  - System info
  - Pi-hole version and config
  - Recent error logs
  - Service status
  - Database stats
  - Network config
- Report saved to file
- File path displayed
**Test Data**: None required
**Duration**: 10-30 seconds
**Known Issues**: Report may contain sensitive information (IPs, domains)

---

## Test Result Categorization

### Severity Levels

**Critical**:
- Feature completely broken
- Causes system instability
- Data loss risk
- Security vulnerability

**High**:
- Feature mostly broken
- Major functionality impaired
- Poor user experience
- Frequent failures

**Medium**:
- Feature partially works
- Minor functionality issues
- Workarounds available
- Intermittent failures

**Low**:
- Cosmetic issues
- Minor inconveniences
- Documentation gaps
- Performance issues (non-critical)

### Issue Types

- **Bug**: Unexpected behavior, errors, crashes
- **Performance**: Slow operations, timeouts, resource issues
- **UX**: Confusing menus, unclear messages, poor feedback
- **Documentation**: Missing docs, incorrect docs, unclear instructions
- **Limitation**: Known limitation that should be documented

---

## Test Execution Log Template

```
Date: YYYY-MM-DD
Tester: [Name]
Environment: [Pi Model, OS Version, Pi-hole Version]

Module: [Module Name]
Operation: [Operation Number and Name]

Steps Executed:
1. [Step 1]
2. [Step 2]
...

Expected Result:
[Expected behavior from guide]

Actual Result:
[What actually happened]

Screen Output:
[Paste relevant output]

Log Entry (if relevant):
[Paste from /tmp/pihole-manager-*.log]

Status: PASS / FAIL / PARTIAL

Issues Found:
- Issue 1: [Description] (Severity: [Critical/High/Medium/Low])
- Issue 2: [Description] (Severity: [Critical/High/Medium/Low])

Notes:
[Any additional observations]
```

---

## Known Limitations Summary

1. **Time-Based Content Filtering**: Manual enforcement only, no cron automation
2. **Historical Statistics**: Placeholder implementation, export to CSV recommended
3. **Device Management**: Name/grouping stored in app only, not in Pi-hole
4. **Gravity Rebuilds**: Can be slow (2-20 minutes depending on profile)
5. **Query Log**: Can be overwhelming on busy networks
6. **Update Operations**: May timeout on slow Pi or slow network
7. **Diagnostic Report**: May contain sensitive information

---

## Pre-Test Checklist

- [ ] Pi-hole is installed and running
- [ ] Initial setup (`initial-setup.sh`) has been completed
- [ ] Test Pi is on the network
- [ ] SSH access is available
- [ ] Backup of gravity.db exists (optional but recommended)
- [ ] Log file location confirmed: `/tmp/pihole-manager-*.log`
- [ ] Clean state: No active content filter rules
- [ ] Clean state: Known blocklist profile (e.g., Moderate)

---

## Post-Test Checklist

- [ ] All 51 operations tested
- [ ] All issues documented with severity
- [ ] Session log archived
- [ ] Test results document created
- [ ] Prioritized fixes todo list created
- [ ] Critical issues flagged for immediate attention

---

## Next Steps

After completing UAT:
1. Create `docs/uat-results-YYYY-MM-DD.md` with detailed results
2. Analyze results and categorize issues by severity
3. Create `docs/uat-fixes-todo.md` with prioritized fixes
4. Commit UAT results and fixes todo to git
