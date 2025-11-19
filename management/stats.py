"""
Statistics and Monitoring Module

View Pi-hole statistics, query dashboards, top domains/clients,
and real-time monitoring capabilities.
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from core.local_executor import execute_command
from core.config import Config
from core.ui import (
    console, show_menu, show_table, show_status, show_error,
    show_success, show_warning, confirm_action, wait_for_enter,
    prompt_input, show_panel, clear_screen, show_key_value_list
)


def run(config: Config):
    """Main statistics and monitoring interface"""
    while True:
        clear_screen()
        console.print("[bold cyan]Statistics & Monitoring[/bold cyan]\n")

        options = [
            "Dashboard Overview",
            "Query Statistics",
            "Top Blocked Domains",
            "Top Allowed Domains",
            "Top Clients",
            "Query Types",
            "Real-time Query Log",
            "Historical Trends",
            "Export Statistics"
        ]

        choice = show_menu("Statistics Operations", options, allow_back=True)

        if choice == "9":
            break
        elif choice == "1":
            show_dashboard(config)
        elif choice == "2":
            show_query_stats(config)
        elif choice == "3":
            show_top_blocked(config)
        elif choice == "4":
            show_top_allowed(config)
        elif choice == "5":
            show_top_clients(config)
        elif choice == "6":
            show_query_types(config)
        elif choice == "7":
            show_realtime_log(config)
        elif choice == "8":
            show_historical_trends(config)
        elif choice == "9":
            export_statistics(config)


def show_dashboard(config: Config):
    """Display comprehensive Pi-hole dashboard"""
    clear_screen()
    console.print("[bold cyan]Pi-hole Dashboard[/bold cyan]\n")

    show_status("Loading dashboard...", "info")

    # Get summary statistics
    summary = get_summary_stats()

    if not summary:
        show_error("Failed to fetch statistics")
        wait_for_enter()
        return

    # Display summary
    console.print("[bold]Query Statistics (Last 24 Hours):[/bold]\n")

    stats_data = {
        "Total Queries": f"{summary.get('total_queries', 0):,}",
        "Queries Blocked": f"{summary.get('blocked_queries', 0):,}",
        "Percent Blocked": f"{summary.get('percent_blocked', 0):.1f}%",
        "Queries Allowed": f"{summary.get('allowed_queries', 0):,}",
        "Queries Cached": f"{summary.get('cached_queries', 0):,}",
        "Cache Hit Rate": f"{summary.get('cache_hit_rate', 0):.1f}%"
    }

    show_key_value_list(stats_data)

    # System info
    console.print("[bold]System Information:[/bold]\n")

    system_info = get_system_info()

    if system_info:
        show_key_value_list(system_info)

    # Domains on blocklist
    success, domains_count, _ = execute_command(
        "sqlite3 /etc/pihole/gravity.db 'SELECT COUNT(*) FROM gravity;'",
        sudo=True
    )

    if success and domains_count.strip():
        console.print(f"[bold]Domains on Blocklist:[/bold] {int(domains_count.strip()):,}\n")

    wait_for_enter()


def show_query_stats(config: Config):
    """Show detailed query statistics"""
    console.print("\n[bold]Query Statistics[/bold]\n")

    # Time range selection
    time_range = select_time_range(config)

    show_status("Fetching query statistics...", "info")

    # Get stats for selected range
    stats = get_query_stats_for_range(time_range)

    if not stats:
        show_warning("No data available for selected time range")
        wait_for_enter()
        return

    # Display stats
    console.print(f"\n[bold]Time Range:[/bold] {time_range['label']}\n")

    query_data = {
        "Total Queries": f"{stats.get('total', 0):,}",
        "Blocked": f"{stats.get('blocked', 0):,} ({stats.get('blocked_percent', 0):.1f}%)",
        "Allowed": f"{stats.get('allowed', 0):,} ({stats.get('allowed_percent', 0):.1f}%)",
        "Cached": f"{stats.get('cached', 0):,} ({stats.get('cached_percent', 0):.1f}%)",
        "Forwarded": f"{stats.get('forwarded', 0):,}"
    }

    show_key_value_list(query_data, "Query Breakdown")

    # Query types breakdown
    if stats.get('query_types'):
        console.print("[bold]Query Types:[/bold]\n")

        type_rows = []
        for qtype, count in stats['query_types'].items():
            percent = (count / stats['total'] * 100) if stats['total'] > 0 else 0
            type_rows.append([qtype, f"{count:,}", f"{percent:.1f}%"])

        show_table(
            title="",
            headers=["Type", "Count", "Percent"],
            rows=type_rows,
            styles=["cyan", "white", "yellow"]
        )

    wait_for_enter()


def show_top_blocked(config: Config):
    """Show top blocked domains"""
    console.print("\n[bold]Top Blocked Domains[/bold]\n")

    time_range = select_time_range(config)
    top_count = config.get("stats", "top_items_count", 10)

    show_status("Fetching top blocked domains...", "info")

    # Query database
    time_filter = get_time_filter(time_range)

    success, output, error = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db \"SELECT domain, COUNT(*) as count FROM queries WHERE {time_filter} AND status = 1 GROUP BY domain ORDER BY count DESC LIMIT {top_count};\"",
        sudo=True
    )

    if not success:
        show_error(f"Failed to fetch data: {error}")
        wait_for_enter()
        return

    if not output.strip():
        show_warning("No blocked queries in selected time range")
        wait_for_enter()
        return

    # Parse results
    rows = []
    total_blocked = 0

    for line in output.strip().split('\n'):
        parts = line.split('|')
        if len(parts) >= 2:
            domain, count = parts[0], int(parts[1])
            total_blocked += count
            rows.append([domain[:60], f"{count:,}"])

    # Add percentages
    for row in rows:
        count = int(row[1].replace(',', ''))
        percent = (count / total_blocked * 100) if total_blocked > 0 else 0
        row.append(f"{percent:.1f}%")

    show_table(
        title=f"Top {top_count} Blocked Domains - {time_range['label']}",
        headers=["Domain", "Queries", "% of Blocked"],
        rows=rows,
        styles=["white", "cyan", "yellow"]
    )

    console.print(f"\nTotal blocked queries: {total_blocked:,}\n")
    wait_for_enter()


def show_top_allowed(config: Config):
    """Show top allowed domains"""
    console.print("\n[bold]Top Allowed Domains[/bold]\n")

    time_range = select_time_range(config)
    top_count = config.get("stats", "top_items_count", 10)

    show_status("Fetching top allowed domains...", "info")

    time_filter = get_time_filter(time_range)

    success, output, error = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db \"SELECT domain, COUNT(*) as count FROM queries WHERE {time_filter} AND status IN (2, 3) GROUP BY domain ORDER BY count DESC LIMIT {top_count};\"",
        sudo=True
    )

    if not success:
        show_error(f"Failed to fetch data: {error}")
        wait_for_enter()
        return

    if not output.strip():
        show_warning("No allowed queries in selected time range")
        wait_for_enter()
        return

    rows = []
    total_allowed = 0

    for line in output.strip().split('\n'):
        parts = line.split('|')
        if len(parts) >= 2:
            domain, count = parts[0], int(parts[1])
            total_allowed += count
            rows.append([domain[:60], f"{count:,}"])

    for row in rows:
        count = int(row[1].replace(',', ''))
        percent = (count / total_allowed * 100) if total_allowed > 0 else 0
        row.append(f"{percent:.1f}%")

    show_table(
        title=f"Top {top_count} Allowed Domains - {time_range['label']}",
        headers=["Domain", "Queries", "% of Allowed"],
        rows=rows,
        styles=["white", "cyan", "yellow"]
    )

    console.print(f"\nTotal allowed queries: {total_allowed:,}\n")
    wait_for_enter()


def show_top_clients(config: Config):
    """Show top clients by query count"""
    console.print("\n[bold]Top Clients[/bold]\n")

    time_range = select_time_range(config)
    top_count = config.get("stats", "top_items_count", 10)

    show_status("Fetching top clients...", "info")

    time_filter = get_time_filter(time_range)

    success, output, error = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db \"SELECT client, COUNT(*) as count FROM queries WHERE {time_filter} GROUP BY client ORDER BY count DESC LIMIT {top_count};\"",
        sudo=True
    )

    if not success:
        show_error(f"Failed to fetch data: {error}")
        wait_for_enter()
        return

    if not output.strip():
        show_warning("No query data in selected time range")
        wait_for_enter()
        return

    rows = []
    total_queries = 0

    for line in output.strip().split('\n'):
        parts = line.split('|')
        if len(parts) >= 2:
            client_ip, count = parts[0], int(parts[1])
            total_queries += count

            # Try to get client name
            success_name, name_output, _ = execute_command(
                f"sqlite3 /etc/pihole/pihole-FTL.db \"SELECT name FROM network WHERE ip = '{client_ip}';\"",
                sudo=True
            )

            client_name = name_output.strip() if success_name and name_output.strip() else "Unknown"

            rows.append([client_ip, client_name, f"{count:,}"])

    for row in rows:
        count = int(row[2].replace(',', ''))
        percent = (count / total_queries * 100) if total_queries > 0 else 0
        row.append(f"{percent:.1f}%")

    show_table(
        title=f"Top {top_count} Clients - {time_range['label']}",
        headers=["IP Address", "Name", "Queries", "% of Total"],
        rows=rows,
        styles=["cyan", "white", "white", "yellow"]
    )

    console.print(f"\nTotal queries: {total_queries:,}\n")
    wait_for_enter()


def show_query_types(config: Config):
    """Show breakdown of DNS query types"""
    console.print("\n[bold]Query Types[/bold]\n")

    time_range = select_time_range(config)

    show_status("Fetching query types...", "info")

    time_filter = get_time_filter(time_range)

    success, output, error = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db \"SELECT type, COUNT(*) as count FROM queries WHERE {time_filter} GROUP BY type ORDER BY count DESC;\"",
        sudo=True
    )

    if not success:
        show_error(f"Failed to fetch data: {error}")
        wait_for_enter()
        return

    if not output.strip():
        show_warning("No query data available")
        wait_for_enter()
        return

    # Map query types
    type_names = {
        "1": "A (IPv4)",
        "2": "AAAA (IPv6)",
        "5": "CNAME",
        "6": "SOA",
        "12": "PTR (Reverse)",
        "15": "MX (Mail)",
        "16": "TXT",
        "28": "AAAA (IPv6)",
        "33": "SRV",
        "255": "ANY"
    }

    rows = []
    total = 0

    for line in output.strip().split('\n'):
        parts = line.split('|')
        if len(parts) >= 2:
            qtype, count = parts[0], int(parts[1])
            total += count

            type_name = type_names.get(qtype, f"Type {qtype}")
            rows.append([type_name, f"{count:,}"])

    for row in rows:
        count = int(row[1].replace(',', ''))
        percent = (count / total * 100) if total > 0 else 0
        row.append(f"{percent:.1f}%")

    show_table(
        title=f"Query Types - {time_range['label']}",
        headers=["Type", "Count", "Percent"],
        rows=rows,
        styles=["cyan", "white", "yellow"]
    )

    console.print(f"\nTotal: {total:,}\n")
    wait_for_enter()


def show_realtime_log(config: Config):
    """Show real-time query log"""
    console.print("\n[bold]Real-time Query Log[/bold]\n")
    console.print("[yellow]Showing last 50 queries. Press Ctrl+C to stop.[/yellow]\n")

    try:
        # Get recent queries
        success, output, _ = execute_command(
            "sqlite3 /etc/pihole/pihole-FTL.db 'SELECT timestamp, client, domain, status FROM queries ORDER BY timestamp DESC LIMIT 50;'",
            sudo=True
        )

        if not success or not output.strip():
            show_warning("No recent queries")
            wait_for_enter()
            return

        rows = []
        for line in output.strip().split('\n'):
            parts = line.split('|')
            if len(parts) >= 4:
                timestamp, client, domain, status = parts[0], parts[1], parts[2], parts[3]

                # Format timestamp
                try:
                    ts_dt = datetime.fromtimestamp(int(timestamp)).strftime("%H:%M:%S")
                except:
                    ts_dt = timestamp

                # Format status
                status_map = {
                    "1": "[red]BLOCKED[/red]",
                    "2": "[green]ALLOWED[/green]",
                    "3": "[yellow]CACHED[/yellow]"
                }
                status_text = status_map.get(status, f"Status {status}")

                rows.append([ts_dt, client, domain[:50], status_text])

        show_table(
            title="Recent Queries",
            headers=["Time", "Client", "Domain", "Status"],
            rows=rows,
            styles=["cyan", "yellow", "white", "white"]
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped[/yellow]")

    wait_for_enter()


def show_historical_trends(config: Config):
    """Show historical query trends"""
    console.print("\n[bold]Historical Trends[/bold]\n")
    console.print("Coming soon: Hourly/daily query trends with ASCII graphs\n")
    wait_for_enter()


def export_statistics(config: Config):
    """Export statistics to CSV"""
    console.print("\n[bold]Export Statistics[/bold]\n")

    time_range = select_time_range(config)
    local_file = prompt_input("Local file path to save", default=f"pihole_stats_{time.strftime('%Y%m%d')}.csv")

    show_status("Exporting statistics...", "info")

    time_filter = get_time_filter(time_range)

    # Get all queries
    success, output, error = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db \"SELECT timestamp, client, domain, type, status FROM queries WHERE {time_filter} ORDER BY timestamp DESC;\"",
        sudo=True
    )

    if not success:
        show_error(f"Failed to export: {error}")
        wait_for_enter()
        return

    if not output.strip():
        show_warning("No data to export")
        wait_for_enter()
        return

    # Write CSV
    try:
        with open(local_file, 'w') as f:
            f.write("Timestamp,Client,Domain,Type,Status\n")

            for line in output.strip().split('\n'):
                parts = line.split('|')
                if len(parts) >= 5:
                    f.write(','.join(parts) + '\n')

        show_success(f"Statistics exported to {local_file}")
    except Exception as e:
        show_error(f"Failed to write file: {e}")

    wait_for_enter()


# Helper functions

def select_time_range(config: Config) -> Dict[str, Any]:
    """Prompt user to select time range"""
    default_range = config.get("stats", "default_range", "24h")

    console.print("\n[bold]Time Range:[/bold]")
    console.print("  [1] Last 24 hours")
    console.print("  [2] Last 7 days")
    console.print("  [3] Last 30 days")
    console.print("  [4] All time")

    choice = prompt_input("Select range (1-4)", default="1")

    now = int(time.time())

    if choice == "2":
        return {"label": "Last 7 days", "start": now - 604800, "end": now}
    elif choice == "3":
        return {"label": "Last 30 days", "start": now - 2592000, "end": now}
    elif choice == "4":
        return {"label": "All time", "start": 0, "end": now}
    else:
        return {"label": "Last 24 hours", "start": now - 86400, "end": now}


def get_time_filter(time_range: Dict[str, Any]) -> str:
    """Generate SQL time filter"""
    if time_range["start"] == 0:
        return "1=1"
    else:
        return f"timestamp >= {time_range['start']} AND timestamp <= {time_range['end']}"


def get_summary_stats() -> Optional[Dict[str, Any]]:
    """Get summary statistics for dashboard"""
    now = int(time.time())
    yesterday = now - 86400

    # Total queries
    success, total, _ = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db 'SELECT COUNT(*) FROM queries WHERE timestamp > {yesterday};'",
        sudo=True
    )

    if not success:
        return None

    total_queries = int(total.strip()) if total.strip() else 0

    # Blocked queries
    success, blocked, _ = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db 'SELECT COUNT(*) FROM queries WHERE timestamp > {yesterday} AND status = 1;'",
        sudo=True
    )

    blocked_queries = int(blocked.strip()) if blocked.strip() else 0

    # Cached queries
    success, cached, _ = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db 'SELECT COUNT(*) FROM queries WHERE timestamp > {yesterday} AND status = 3;'",
        sudo=True
    )

    cached_queries = int(cached.strip()) if cached.strip() else 0

    allowed_queries = total_queries - blocked_queries
    percent_blocked = (blocked_queries / total_queries * 100) if total_queries > 0 else 0
    cache_hit_rate = (cached_queries / total_queries * 100) if total_queries > 0 else 0

    return {
        "total_queries": total_queries,
        "blocked_queries": blocked_queries,
        "allowed_queries": allowed_queries,
        "cached_queries": cached_queries,
        "percent_blocked": percent_blocked,
        "cache_hit_rate": cache_hit_rate
    }


def get_system_info() -> Optional[Dict[str, str]]:
    """Get system information"""
    info = {}

    # Uptime
    success, uptime, _ = execute_command("uptime -p")
    if success:
        info["Uptime"] = uptime.strip().replace("up ", "")

    # Load average
    success, load, _ = execute_command("cat /proc/loadavg | awk '{print $1, $2, $3}'")
    if success:
        info["Load Average"] = load.strip()

    # Memory usage
    success, mem, _ = execute_command("free -h | grep Mem | awk '{print $3 \"/\" $2}'")
    if success:
        info["Memory Usage"] = mem.strip()

    # Disk usage
    success, disk, _ = execute_command("df -h / | tail -1 | awk '{print $3 \"/\" $2 \" (\" $5 \" used)\"}'")
    if success:
        info["Disk Usage"] = disk.strip()

    return info if info else None


def get_query_stats_for_range(time_range: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get detailed query statistics for time range"""
    time_filter = get_time_filter(time_range)

    # Total queries
    success, total, _ = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db 'SELECT COUNT(*) FROM queries WHERE {time_filter};'",
        sudo=True
    )

    if not success:
        return None

    total_count = int(total.strip()) if total.strip() else 0

    if total_count == 0:
        return None

    # Blocked, allowed, cached
    success, blocked, _ = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db 'SELECT COUNT(*) FROM queries WHERE {time_filter} AND status = 1;'",
        sudo=True
    )

    success2, cached, _ = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db 'SELECT COUNT(*) FROM queries WHERE {time_filter} AND status = 3;'",
        sudo=True
    )

    blocked_count = int(blocked.strip()) if blocked.strip() else 0
    cached_count = int(cached.strip()) if cached.strip() else 0
    allowed_count = total_count - blocked_count

    return {
        "total": total_count,
        "blocked": blocked_count,
        "blocked_percent": (blocked_count / total_count * 100) if total_count > 0 else 0,
        "allowed": allowed_count,
        "allowed_percent": (allowed_count / total_count * 100) if total_count > 0 else 0,
        "cached": cached_count,
        "cached_percent": (cached_count / total_count * 100) if total_count > 0 else 0,
        "forwarded": allowed_count - cached_count
    }
