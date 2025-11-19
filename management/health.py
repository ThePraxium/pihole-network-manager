"""
Health and Diagnostics Module

Run diagnostic tests, check system health, verify DNS functionality,
and troubleshoot common issues.
"""

from typing import List, Dict, Tuple
from core.local_executor import execute_command, file_exists
from core.config import Config
from core.ui import (
    console, show_menu, show_table, show_status, show_error,
    show_success, show_warning, confirm_action, wait_for_enter,
    prompt_input, clear_screen, show_key_value_list
)


def run(config: Config):
    """Main health and diagnostics interface"""
    while True:
        clear_screen()
        console.print("[bold cyan]Health & Diagnostics[/bold cyan]\n")

        options = [
            "Run Full Health Check",
            "Test DNS Resolution",
            "Test Blocking Functionality",
            "Check Service Status",
            "Network Connectivity Test",
            "Database Integrity Check",
            "View Error Logs",
            "Generate Diagnostic Report"
        ]

        choice = show_menu("Diagnostic Operations", options, allow_back=True)

        if choice == "9":
            break
        elif choice == "1":
            run_full_health_check()
        elif choice == "2":
            test_dns_resolution()
        elif choice == "3":
            test_blocking_functionality()
        elif choice == "4":
            check_service_status()
        elif choice == "5":
            network_connectivity_test()
        elif choice == "6":
            database_integrity_check()
        elif choice == "7":
            view_error_logs()
        elif choice == "8":
            generate_diagnostic_report()


def run_full_health_check():
    """Run comprehensive health check"""
    clear_screen()
    console.print("[bold cyan]Full Health Check[/bold cyan]\n")

    tests = [
        ("DNS Resolution", test_dns_resolution),
        ("Blocking Functionality", test_blocking_functionality),
        ("Service Status", check_service_status),
        ("Network Connectivity", network_connectivity_test),
        ("Database Integrity", database_integrity_check)
    ]

    results = []

    for test_name, test_func in tests:
        console.print(f"\n[bold]Running: {test_name}[/bold]")
        result = test_func(silent=True)
        results.append((test_name, result))

    # Summary
    console.print("\n" + "="*70)
    console.print("[bold cyan]Health Check Summary[/bold cyan]")
    console.print("="*70 + "\n")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for test_name, result in results:
        status = "[green]✓ PASS[/green]" if result else "[red]✗ FAIL[/red]"
        console.print(f"{status} {test_name}")

    console.print(f"\n[bold]Overall: {passed}/{total} tests passed[/bold]")

    if passed == total:
        console.print("\n[green]✓ All systems operational[/green]\n")
    else:
        console.print("\n[yellow]⚠ Some issues detected - review failed tests above[/yellow]\n")

    wait_for_enter()


def test_dns_resolution(silent=False) -> bool:
    """Test DNS resolution through Pi-hole"""
    if not silent:
        console.print("\n[bold]DNS Resolution Test[/bold]\n")
        show_status("Testing DNS resolution...", "info")

    test_domains = [
        ("google.com", "Should resolve"),
        ("cloudflare.com", "Should resolve"),
        ("example.com", "Should resolve")
    ]

    all_passed = True

    for domain, expected in test_domains:
        success, output, error = execute_command(
            f"dig @127.0.0.1 {domain} +short +time=2",
            sudo=False
        )

        if success and output.strip():
            if not silent:
                console.print(f"[green]✓[/green] {domain}: {output.strip().split()[0]}")
        else:
            if not silent:
                console.print(f"[red]✗[/red] {domain}: Failed to resolve")
            all_passed = False

    if not silent:
        console.print()
        wait_for_enter()

    return all_passed


def test_blocking_functionality(silent=False) -> bool:
    """Test if blocking is working correctly"""
    if not silent:
        console.print("\n[bold]Blocking Functionality Test[/bold]\n")
        show_status("Testing ad blocking...", "info")

    # Test known ad domains
    test_ad_domains = [
        "doubleclick.net",
        "googleadservices.com",
        "facebook.com"  # If blocked by user
    ]

    blocked_count = 0

    for domain in test_ad_domains:
        success, output, _ = execute_command(
            f"dig @127.0.0.1 {domain} +short",
            sudo=False
        )

        if success:
            # Check if response is 0.0.0.0 or empty (blocked)
            response = output.strip()

            if response in ["0.0.0.0", ""] or response.startswith("0.0.0.0"):
                if not silent:
                    console.print(f"[green]✓[/green] {domain}: Blocked")
                blocked_count += 1
            else:
                if not silent:
                    console.print(f"[yellow]○[/yellow] {domain}: Not blocked ({response})")

    if not silent:
        console.print(f"\n{blocked_count}/{len(test_ad_domains)} test domains blocked\n")
        wait_for_enter()

    return blocked_count > 0


def check_service_status(silent=False) -> bool:
    """Check status of critical services"""
    if not silent:
        console.print("\n[bold]Service Status Check[/bold]\n")

    services = ["pihole-FTL", "lighttpd"]

    all_running = True

    for service in services:
        success, output, _ = execute_command(f"systemctl is-active {service}")

        is_active = output.strip() == "active"

        if not silent:
            status = "[green]✓ Running[/green]" if is_active else "[red]✗ Stopped[/red]"
            console.print(f"{status} {service}")

        if not is_active:
            all_running = False

    if not silent:
        console.print()
        wait_for_enter()

    return all_running


def network_connectivity_test(silent=False) -> bool:
    """Test network connectivity"""
    if not silent:
        console.print("\n[bold]Network Connectivity Test[/bold]\n")
        show_status("Testing connectivity...", "info")

    tests = [
        ("Internet connectivity", "ping -c 2 -W 2 8.8.8.8"),
        ("DNS connectivity", "ping -c 2 -W 2 1.1.1.1"),
        ("External DNS resolution", "dig @1.1.1.1 google.com +short +time=2")
    ]

    all_passed = True

    for test_name, command in tests:
        success, output, _ = execute_command(command, sudo=False)

        if success and output.strip():
            if not silent:
                console.print(f"[green]✓[/green] {test_name}")
        else:
            if not silent:
                console.print(f"[red]✗[/red] {test_name}")
            all_passed = False

    if not silent:
        console.print()
        wait_for_enter()

    return all_passed


def database_integrity_check(silent=False) -> bool:
    """Check integrity of Pi-hole databases"""
    if not silent:
        console.print("\n[bold]Database Integrity Check[/bold]\n")
        show_status("Checking databases...", "info")

    databases = [
        "/etc/pihole/gravity.db",
        "/etc/pihole/pihole-FTL.db"
    ]

    all_ok = True

    for db_path in databases:
        # Check if database exists
        if not file_exists(db_path):
            if not silent:
                console.print(f"[red]✗[/red] {db_path}: Not found")
            all_ok = False
            continue

        # Run integrity check
        success, output, _ = execute_command(
            f"sqlite3 {db_path} 'PRAGMA integrity_check;'",
            sudo=True
        )

        if success and "ok" in output.lower():
            if not silent:
                console.print(f"[green]✓[/green] {db_path}: OK")
        else:
            if not silent:
                console.print(f"[red]✗[/red] {db_path}: Integrity check failed")
            all_ok = False

    if not silent:
        console.print()
        wait_for_enter()

    return all_ok


def view_error_logs():
    """View recent error logs"""
    console.print("\n[bold]Error Logs[/bold]\n")

    show_status("Fetching error logs...", "info")

    # Pi-hole FTL errors
    console.print("\n[bold]Pi-hole FTL Errors (Last 20):[/bold]\n")

    success, ftl_errors, _ = execute_command(
        "grep -i error /var/log/pihole-FTL.log 2>/dev/null | tail -20 || echo 'No errors found'",
        sudo=True
    )

    if success:
        console.print(ftl_errors if ftl_errors.strip() else "No errors found")

    # System errors
    console.print("\n[bold]System Errors (Last 10):[/bold]\n")

    success, sys_errors, _ = execute_command(
        "journalctl -p 3 -n 10 --no-pager || dmesg | grep -i error | tail -10",
        sudo=True
    )

    if success:
        console.print(sys_errors if sys_errors.strip() else "No errors found")

    console.print()
    wait_for_enter()


def generate_diagnostic_report():
    """Generate comprehensive diagnostic report"""
    console.print("\n[bold]Generate Diagnostic Report[/bold]\n")

    local_file = prompt_input("Save report to", default="pihole_diagnostics.txt")

    show_status("Generating diagnostic report...", "info")

    # Collect all diagnostic information
    report_lines = []

    report_lines.append("="*70)
    report_lines.append("Pi-hole Diagnostic Report")
    report_lines.append("="*70)
    report_lines.append("")

    # System info
    report_lines.append("[System Information]")

    success, hostname, _ = execute_command("hostname")
    if success:
        report_lines.append(f"Hostname: {hostname.strip()}")

    success, os_info, _ = execute_command("cat /etc/os-release | grep PRETTY_NAME | cut -d'\"' -f2")
    if success:
        report_lines.append(f"OS: {os_info.strip()}")

    success, kernel, _ = execute_command("uname -r")
    if success:
        report_lines.append(f"Kernel: {kernel.strip()}")

    report_lines.append("")

    # Pi-hole version
    report_lines.append("[Pi-hole Version]")

    success, version, _ = execute_command("pihole -v")
    if success:
        report_lines.append(version.strip())

    report_lines.append("")

    # Service status
    report_lines.append("[Service Status]")

    for service in ["pihole-FTL", "lighttpd", "ssh"]:
        success, status, _ = execute_command(f"systemctl status {service} --no-pager")
        if success:
            report_lines.append(f"\n{service}:")
            report_lines.append(status.strip())

    report_lines.append("")

    # DNS test results
    report_lines.append("[DNS Tests]")

    test_dns_resolution(silent=True)

    report_lines.append("")

    # Recent logs
    report_lines.append("[Recent Logs]")

    success, logs, _ = execute_command("tail -50 /var/log/pihole-FTL.log", sudo=True)
    if success:
        report_lines.append(logs.strip())

    # Write to file
    try:
        with open(local_file, 'w') as f:
            f.write('\n'.join(report_lines))

        show_success(f"Diagnostic report saved to {local_file}")
    except Exception as e:
        show_error(f"Failed to save report: {e}")

    wait_for_enter()
