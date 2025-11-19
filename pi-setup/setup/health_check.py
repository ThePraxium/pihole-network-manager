"""
Health Check Module

Performs comprehensive system validation:
- DNS resolution testing
- Pi-hole service status
- Firewall rules validation
- Network connectivity
- Disk space and system resources
- Generate health report
"""

import subprocess
from pathlib import Path
from rich.table import Table
from rich.panel import Panel


def run_command(cmd, check=True):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def test_dns_resolution(console):
    """Test DNS resolution through Pi-hole"""
    console.print("\n[bold]Testing DNS Resolution...[/bold]")

    tests = [
        ("Normal domain (google.com)", "dig @127.0.0.1 google.com +short"),
        ("Known ad domain", "dig @127.0.0.1 doubleclick.net +short"),
        ("External DNS query", "dig @1.1.1.1 google.com +short"),
    ]

    results = []

    for test_name, command in tests:
        success, stdout, stderr = run_command(command, check=False)

        if success and stdout.strip():
            if test_name.startswith("Known ad"):
                # Should return 0.0.0.0 or similar
                if "0.0.0.0" in stdout or not stdout.strip():
                    results.append((test_name, True, "Blocked (correct)"))
                else:
                    results.append((test_name, False, "Not blocked"))
            else:
                results.append((test_name, True, "Resolved"))
        else:
            results.append((test_name, False, "Failed"))

    # Display results
    for test_name, passed, result in results:
        status = "[green]✓[/green]" if passed else "[red]✗[/red]"
        console.print(f"  {status} {test_name}: {result}")

    all_passed = all(passed for _, passed, _ in results)
    return all_passed, results


def check_services(console):
    """Check critical service status"""
    console.print("\n[bold]Checking System Services...[/bold]")

    services = [
        ("Pi-hole FTL", "pihole-FTL"),
        ("Lighttpd (Web)", "lighttpd"),
        ("UFW Firewall", "ufw"),
        ("Fail2ban", "fail2ban"),
        ("SSH", "ssh"),
    ]

    results = []

    for service_name, service in services:
        success, stdout, _ = run_command(f"systemctl is-active {service}", check=False)

        if success and "active" in stdout:
            results.append((service_name, True, "Running"))
        else:
            results.append((service_name, False, "Not running"))

    # Display results
    for service_name, running, status in results:
        status_icon = "[green]✓[/green]" if running else "[red]✗[/red]"
        console.print(f"  {status_icon} {service_name}: {status}")

    all_running = all(running for _, running, _ in results)
    return all_running, results


def check_firewall_rules(console):
    """Verify firewall rules are correct"""
    console.print("\n[bold]Verifying Firewall Rules...[/bold]")

    required_ports = [
        ("22", "SSH"),
        ("53", "DNS"),
        ("80", "HTTP"),
        ("443", "HTTPS"),
    ]

    success, stdout, _ = run_command("ufw status", check=False)

    results = []

    if success:
        for port, service in required_ports:
            if port in stdout:
                results.append((f"{service} (port {port})", True, "Allowed"))
            else:
                results.append((f"{service} (port {port})", False, "Not configured"))
    else:
        console.print("  [red]✗ UFW not running or not configured[/red]")
        return False, []

    # Display results
    for rule_name, configured, status in results:
        status_icon = "[green]✓[/green]" if configured else "[yellow]⚠[/yellow]"
        console.print(f"  {status_icon} {rule_name}: {status}")

    all_configured = all(configured for _, configured, _ in results)
    return all_configured, results


def check_network_connectivity(console):
    """Test network connectivity"""
    console.print("\n[bold]Testing Network Connectivity...[/bold]")

    tests = [
        ("Gateway", "ping -c 2 -W 2 $(ip route | grep default | awk '{print $3}')"),
        ("Cloudflare DNS", "ping -c 2 -W 2 1.1.1.1"),
        ("Google DNS", "ping -c 2 -W 2 8.8.8.8"),
        ("Internet (google.com)", "ping -c 2 -W 2 google.com"),
    ]

    results = []

    for test_name, command in tests:
        success, stdout, _ = run_command(command, check=False)
        if success:
            results.append((test_name, True, "Reachable"))
        else:
            results.append((test_name, False, "Unreachable"))

    # Display results
    for test_name, reachable, status in results:
        status_icon = "[green]✓[/green]" if reachable else "[red]✗[/red]"
        console.print(f"  {status_icon} {test_name}: {status}")

    all_reachable = all(reachable for _, reachable, _ in results)
    return all_reachable, results


def check_system_resources(console):
    """Check system resources"""
    console.print("\n[bold]Checking System Resources...[/bold]")

    # Disk space
    success, stdout, _ = run_command("df -h / | tail -1", check=False)
    if success:
        parts = stdout.split()
        if len(parts) >= 5:
            used_pct = parts[4].rstrip('%')
            try:
                used_pct_int = int(used_pct)
                disk_status = "OK" if used_pct_int < 80 else "Warning"
                disk_color = "green" if used_pct_int < 80 else "yellow"
                console.print(f"  [{disk_color}]•[/{disk_color}] Disk usage: {used_pct}% ({disk_status})")
            except ValueError:
                console.print(f"  [yellow]•[/yellow] Disk usage: {used_pct}%")

    # Memory
    success, stdout, _ = run_command("free -h | grep Mem", check=False)
    if success:
        parts = stdout.split()
        if len(parts) >= 3:
            total_mem = parts[1]
            used_mem = parts[2]
            console.print(f"  [cyan]•[/cyan] Memory: {used_mem} / {total_mem} used")

    # CPU temperature (Raspberry Pi specific)
    temp_file = Path("/sys/class/thermal/thermal_zone0/temp")
    if temp_file.exists():
        with open(temp_file, 'r') as f:
            temp_millidegrees = int(f.read().strip())
            temp_celsius = temp_millidegrees / 1000
            temp_status = "OK" if temp_celsius < 70 else "Warning"
            temp_color = "green" if temp_celsius < 70 else "yellow"
            console.print(f"  [{temp_color}]•[/{temp_color}] CPU Temperature: {temp_celsius:.1f}°C ({temp_status})")

    # Uptime
    success, stdout, _ = run_command("uptime -p", check=False)
    if success:
        uptime = stdout.strip()
        console.print(f"  [cyan]•[/cyan] Uptime: {uptime}")

    return True, []


def check_pihole_stats(console):
    """Get Pi-hole statistics"""
    console.print("\n[bold]Pi-hole Statistics...[/bold]")

    # Queries today
    success, stdout, _ = run_command("pihole -c -j", check=False)
    if success and stdout:
        try:
            import json
            stats = json.loads(stdout)

            domains_blocked = stats.get('domains_being_blocked', 'N/A')
            queries_today = stats.get('dns_queries_today', 'N/A')
            blocked_today = stats.get('ads_blocked_today', 'N/A')
            percent_blocked = stats.get('ads_percentage_today', 'N/A')

            console.print(f"  [cyan]•[/cyan] Domains on blocklist: {domains_blocked}")
            console.print(f"  [cyan]•[/cyan] Queries today: {queries_today}")
            console.print(f"  [cyan]•[/cyan] Blocked today: {blocked_today}")
            console.print(f"  [green]•[/green] Blocking percentage: {percent_blocked}%")

        except (json.JSONDecodeError, KeyError):
            console.print("  [yellow]•[/yellow] Could not parse Pi-hole stats")
    else:
        # Fallback to simpler command
        success, stdout, _ = run_command("pihole status", check=False)
        if success:
            console.print(f"  [cyan]•[/cyan] Status: {stdout.strip()}")

    return True, []


def generate_health_report(all_results, console):
    """Generate comprehensive health report"""
    console.print("\n[bold cyan]═══ System Health Report ═══[/bold cyan]\n")

    # Count passed/failed checks
    total_checks = sum(len(results) for _, results in all_results.items() if isinstance(results, list))
    passed_checks = sum(
        sum(1 for _, passed, _ in results if passed)
        for _, results in all_results.items()
        if isinstance(results, list)
    )

    # Overall status
    if passed_checks == total_checks:
        status = "[bold green]✓ HEALTHY[/bold green]"
        status_text = "All systems operational"
    elif passed_checks >= total_checks * 0.8:
        status = "[bold yellow]⚠ MOSTLY HEALTHY[/bold yellow]"
        status_text = "Minor issues detected"
    else:
        status = "[bold red]✗ ISSUES DETECTED[/bold red]"
        status_text = "Action required"

    console.print(f"[bold]Overall Status:[/bold] {status}")
    console.print(f"[bold]Checks Passed:[/bold] {passed_checks}/{total_checks}")
    console.print(f"[bold]Assessment:[/bold] {status_text}")
    console.print()

    # Recommendations
    if passed_checks < total_checks:
        console.print("[bold yellow]Recommendations:[/bold yellow]")

        # Check specific failures
        for category, results in all_results.items():
            if isinstance(results, list):
                failed = [(name, result) for name, passed, result in results if not passed]
                if failed:
                    console.print(f"\n[yellow]{category}:[/yellow]")
                    for name, result in failed:
                        console.print(f"  • Fix {name}: {result}")

    console.print()

    # Access information
    success, ip_output, _ = run_command("hostname -I | awk '{print $1}'")
    ip_address = ip_output.strip() if success else "unknown"

    access_info = f"""
[bold]Pi-hole Access:[/bold]
  • Web Interface: http://{ip_address}/admin
  • DNS Server: {ip_address}:53
  • SSH: ssh user@{ip_address}

[bold]Quick Commands:[/bold]
  • View stats: pihole -c
  • Restart FTL: systemctl restart pihole-FTL
  • Update gravity: pihole -g
  • Check logs: tail -f /var/log/pihole.log
    """

    console.print(Panel(access_info.strip(), title="System Information", border_style="cyan"))


def run(config, console):
    """Main entry point for health check"""
    console.print("\n[bold cyan]═══ Health Check Module ═══[/bold cyan]\n")

    console.print("[cyan]Running comprehensive system health check...[/cyan]")

    all_results = {}

    # Run all checks
    checks = [
        ("DNS Resolution", test_dns_resolution),
        ("System Services", check_services),
        ("Firewall Rules", check_firewall_rules),
        ("Network Connectivity", check_network_connectivity),
        ("System Resources", check_system_resources),
        ("Pi-hole Statistics", check_pihole_stats),
    ]

    for check_name, check_func in checks:
        try:
            passed, results = check_func(console)
            all_results[check_name] = results
        except Exception as e:
            console.print(f"[red]✗ {check_name} check failed: {e}[/red]")
            all_results[check_name] = []

    # Generate report
    generate_health_report(all_results, console)

    console.print("\n[bold green]✓ Health check completed![/bold green]")

    return True
