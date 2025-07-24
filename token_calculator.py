import os
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

def calculate_token_usage(base_path, silent=False):
    """
    Calculate total token usage from ui_messages.json files in subdirectories
    that contain Claude Code tasks (filtered by task_metadata.json)
    """
    totals = {
        'tokensIn': 0,
        'tokensOut': 0,
        'cacheWrites': 0,
        'cacheReads': 0,
        'cost': 0.0
    }
    
    file_count = 0
    entry_count = 0
    skipped_count = 0  # Track files skipped (not Claude Code tasks)
    timestamps = []  # Store all timestamps to calculate date range
    request_data = []  # Store individual request data for accurate daily stats
    
    # Convert to Path object for easier handling
    base_path = Path(base_path)
    
    # Check if base path exists
    if not base_path.exists():
        if not silent:
            print(f"Error: Path {base_path} does not exist")
        return totals, file_count, entry_count, skipped_count, timestamps, request_data
    
    # Iterate through all subdirectories
    for folder in base_path.iterdir():
        if folder.is_dir():
            json_file = folder / "ui_messages.json"
            metadata_file = folder / "task_metadata.json"
            
            # Check if both files exist
            if json_file.exists() and metadata_file.exists():
                # First, check if this is a Claude Code task
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    # Check if any model_usage entry has model_provider_id == "claude-code"
                    is_claude_code_task = False
                    if 'model_usage' in metadata:
                        for usage in metadata['model_usage']:
                            if usage.get('model_provider_id') == 'claude-code':
                                is_claude_code_task = True
                                break
                    
                    # Count and skip this folder if it's not a Claude Code task
                    if not is_claude_code_task:
                        skipped_count += 1
                        continue
                        
                except (FileNotFoundError, json.JSONDecodeError, KeyError):
                    # Count and skip folder if metadata file is missing or invalid
                    skipped_count += 1
                    continue
            else:
                # Count folders that don't have the required files
                skipped_count += 1
                continue
                
            # Now process the ui_messages.json file
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                file_count += 1
                if not silent:
                    print(f"Processing: {json_file}")
                
                # Process each entry in the JSON array
                for entry in data:
                    if isinstance(entry, dict) and entry.get('type') == 'say' and entry.get('say') == 'api_req_started':
                        try:
                            # Store timestamp for date range calculation
                            if 'ts' in entry:
                                timestamps.append(entry['ts'])
                            
                            # Parse the nested JSON in the 'text' field
                            text_data = json.loads(entry['text'])
                            
                            # Extract token usage data
                            tokens_in = text_data.get('tokensIn', 0)
                            tokens_out = text_data.get('tokensOut', 0)
                            cache_writes = text_data.get('cacheWrites', 0)
                            cache_reads = text_data.get('cacheReads', 0)
                            cost = text_data.get('cost', 0.0)
                            
                            # Add to totals
                            totals['tokensIn'] += tokens_in
                            totals['tokensOut'] += tokens_out
                            totals['cacheWrites'] += cache_writes
                            totals['cacheReads'] += cache_reads
                            totals['cost'] += cost
                            
                            entry_count += 1
                            
                            # Store individual request data
                            if 'ts' in entry:
                                request_data.append({
                                    'timestamp': entry['ts'],
                                    'tokensIn': tokens_in,
                                    'tokensOut': tokens_out,
                                    'cacheWrites': cache_writes,
                                    'cacheReads': cache_reads,
                                    'cost': cost
                                })
                            
                        except json.JSONDecodeError:
                            # Skip entries where 'text' is not valid JSON
                            continue
                        except (KeyError, TypeError):
                            # Skip entries with missing or invalid data
                            continue
                            
            except FileNotFoundError:
                if not silent:
                    print(f"Warning: Could not read {json_file}")
            except json.JSONDecodeError:
                if not silent:
                    print(f"Warning: Invalid JSON in {json_file}")
            except Exception as e:
                if not silent:
                    print(f"Error processing {json_file}: {e}")
    
    return totals, file_count, entry_count, skipped_count, timestamps, request_data

def calculate_monthly_average(calculated_cost, timestamps):
    """
    Calculate monthly average cost based on actual usage period
    """
    if not timestamps:
        return 0, 0, "No usage data found"
    
    from datetime import datetime
    
    # Convert timestamps from milliseconds to datetime objects
    dates = [datetime.fromtimestamp(ts / 1000) for ts in timestamps]
    dates.sort()
    
    earliest_date = dates[0]
    latest_date = dates[-1]
    
    # Calculate the time span in days
    time_span = (latest_date - earliest_date).days
    
    if time_span == 0:
        # All usage in one day
        return calculated_cost * 30, time_span, f"All usage on {earliest_date.strftime('%Y-%m-%d')}"
    
    # Calculate monthly average
    months_span = time_span / 30.44  # Average days per month
    monthly_average = calculated_cost / months_span if months_span > 0 else calculated_cost
    
    date_range = f"{earliest_date.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')}"
    
    return monthly_average, time_span, date_range

def calculate_daily_usage_stats(request_data):
    """
    Calculate daily usage statistics based on actual request data
    """
    if not request_data:
        return {}
    
    from datetime import datetime
    from collections import defaultdict
    
    # Group actual data by date
    daily_tokens_in = defaultdict(int)
    daily_tokens_out = defaultdict(int)
    daily_cache_writes = defaultdict(int)
    daily_cache_reads = defaultdict(int)
    daily_costs = defaultdict(float)
    daily_requests = defaultdict(int)
    
    # Process each request with its actual data
    for request in request_data:
        date = datetime.fromtimestamp(request['timestamp'] / 1000).date()
        
        # Use actual token counts from each request
        daily_tokens_in[date] += request['tokensIn']
        daily_tokens_out[date] += request['tokensOut']
        daily_cache_writes[date] += request['cacheWrites']
        daily_cache_reads[date] += request['cacheReads']
        daily_costs[date] += request['cost']
        daily_requests[date] += 1
    
    if not daily_costs:
        return {}
    
    # Calculate total tokens per day (in + out)
    daily_total_tokens = {}
    for date in daily_tokens_in.keys():
        daily_total_tokens[date] = daily_tokens_in[date] + daily_tokens_out[date]
    
    # Calculate statistics based on actual data
    costs = list(daily_costs.values())
    tokens = list(daily_total_tokens.values())
    requests = list(daily_requests.values())
    
    stats = {
        'total_active_days': len(costs),
        'avg_daily_cost': sum(costs) / len(costs),
        'max_daily_cost': max(costs),
        'min_daily_cost': min(costs),
        'avg_daily_tokens': sum(tokens) / len(tokens),
        'max_daily_tokens': max(tokens),
        'avg_daily_requests': sum(requests) / len(requests),
        'max_daily_requests': max(requests),
        'dates': list(daily_costs.keys())
    }
    
    return stats

def calculate_cost_from_usage(totals):
    """
    Calculate cost based on token usage with provided rates
    Rates per 1M tokens/operations:
    - Input: $3.00
    - Output: $15.00
    - Cache Write: $3.75
    - Cache Read: $0.30
    """
    rates = {
        'input_per_1M': 3.00,
        'output_per_1M': 15.00,
        'cache_write_per_1M': 3.75,
        'cache_read_per_1M': 0.30
    }
    
    calculated_cost = (
        (totals['tokensIn'] / 1_000_000) * rates['input_per_1M'] +
        (totals['tokensOut'] / 1_000_000) * rates['output_per_1M'] +
        (totals['cacheWrites'] / 1_000_000) * rates['cache_write_per_1M'] +
        (totals['cacheReads'] / 1_000_000) * rates['cache_read_per_1M']
    )
    
    return calculated_cost, rates

def main():
    console = Console()
    
    # Set your base path here - using expanduser to handle ~ properly
    base_path = os.path.expanduser("~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/tasks")
    
    # Header
    console.print()
    console.print(Panel.fit("💰 [bold blue]Cline Claude Cost[/bold blue] 💰", 
                          title="[bold green]CCC[/bold green]", 
                          border_style="bright_blue"))
    console.print()
    
    # Processing info
    console.print(f"[dim]Base path: {base_path}[/dim]")
    console.print()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing files...", total=None)
        totals, file_count, entry_count, skipped_count, timestamps, request_data = calculate_token_usage(base_path, silent=True)
        progress.update(task, completed=100)
    
    # Calculate cost based on usage
    calculated_cost, rates = calculate_cost_from_usage(totals)
    
    # Calculate monthly average
    monthly_average, time_span, date_range = calculate_monthly_average(calculated_cost, timestamps)
    
    # Calculate daily usage statistics based on actual request data
    daily_stats = calculate_daily_usage_stats(request_data)
    
    # Summary Table
    summary_table = Table(title="📊 Usage Summary", box=box.ROUNDED, show_header=True, header_style="bold magenta", width=80)
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Value", style="bright_white", justify="right")
    
    summary_table.add_row("Files processed", f"{file_count:,}")
    summary_table.add_row("Files skipped (not Claude Code task)", f"[dim]{skipped_count:,}[/dim]")
    summary_table.add_row("API calls processed", f"{entry_count:,}")
    summary_table.add_row("Input tokens", f"{totals['tokensIn']:,}")
    summary_table.add_row("Output tokens", f"{totals['tokensOut']:,}")
    summary_table.add_row("Cache writes", f"{totals['cacheWrites']:,}")
    summary_table.add_row("Cache reads", f"{totals['cacheReads']:,}")
    
    console.print(summary_table)
    console.print()
    
    # Cost Breakdown Table
    cost_table = Table(title="💸 Cost Breakdown", box=box.ROUNDED, show_header=True, header_style="bold green", width=80)
    cost_table.add_column("Token Type", style="cyan", no_wrap=True)
    cost_table.add_column("Count", style="bright_white", justify="right")
    cost_table.add_column("Rate per 1M", style="yellow", justify="right")
    cost_table.add_column("Cost", style="bright_green", justify="right")
    
    input_cost = (totals['tokensIn'] / 1_000_000) * rates['input_per_1M']
    output_cost = (totals['tokensOut'] / 1_000_000) * rates['output_per_1M']
    cache_write_cost = (totals['cacheWrites'] / 1_000_000) * rates['cache_write_per_1M']
    cache_read_cost = (totals['cacheReads'] / 1_000_000) * rates['cache_read_per_1M']
    
    cost_table.add_row("Input tokens", f"{totals['tokensIn']:,}", f"${rates['input_per_1M']:.2f}", f"${input_cost:.4f}")
    cost_table.add_row("Output tokens", f"{totals['tokensOut']:,}", f"${rates['output_per_1M']:.2f}", f"${output_cost:.4f}")
    cost_table.add_row("Cache writes", f"{totals['cacheWrites']:,}", f"${rates['cache_write_per_1M']:.2f}", f"${cache_write_cost:.4f}")
    cost_table.add_row("Cache reads", f"{totals['cacheReads']:,}", f"${rates['cache_read_per_1M']:.2f}", f"${cache_read_cost:.4f}", end_section=True)
    cost_table.add_row("[bold]TOTAL CALCULATED", "", "", f"[bold bright_green]${calculated_cost:.4f}[/bold bright_green]")
    
    console.print(cost_table)
    console.print()
    
    # Usage Period Panel
    period_content = f"""[bold]Date range:[/bold] {date_range}
[bold]Time span:[/bold] {time_span} days
[bold]📊 Monthly average:[/bold] [bright_green]${monthly_average:.2f}[/bright_green]"""
    
    console.print(Panel(period_content, title="📅 Usage Period", border_style="blue", width=80))
    console.print()
    
    # Daily Usage Analysis
    if daily_stats:
        daily_table = Table(title="📈 Daily Usage Analysis", box=box.ROUNDED, show_header=True, header_style="bold cyan", width=80)
        daily_table.add_column("Metric", style="cyan", no_wrap=True)
        daily_table.add_column("Value", style="bright_white", justify="right")
        
        daily_table.add_row("Active coding days", f"{daily_stats['total_active_days']}")
        # daily_table.add_row("Average cost per active day", f"${daily_stats['avg_daily_cost']:.4f}")
        # daily_table.add_row("Peak daily cost", f"[bright_red]${daily_stats['max_daily_cost']:.4f}[/bright_red]")
        daily_table.add_row("Average daily tokens", f"{daily_stats['avg_daily_tokens']:,.0f}")
        daily_table.add_row("Peak daily tokens", f"[bright_red]{daily_stats['max_daily_tokens']:,.0f}[/bright_red]")
        daily_table.add_row("Average daily API calls", f"{daily_stats['avg_daily_requests']:.1f}")
        daily_table.add_row("Peak daily API calls", f"[bright_red]{daily_stats['max_daily_requests']}[/bright_red]")
        
        if daily_stats['avg_daily_cost'] > 0:
            peak_vs_avg = ((daily_stats['max_daily_cost'] - daily_stats['avg_daily_cost']) / daily_stats['avg_daily_cost']) * 100
            variation_color = "bright_red" if peak_vs_avg > 100 else "yellow" if peak_vs_avg > 50 else "green"
            daily_table.add_row("Peak day variation", f"[{variation_color}]{peak_vs_avg:.1f}% above average[/{variation_color}]")
        
        console.print(daily_table)
        console.print()
    
    # Additional Statistics
    total_tokens = totals['tokensIn'] + totals['tokensOut']
    total_cache_ops = totals['cacheWrites'] + totals['cacheReads']
    
    additional_table = Table(title="📋 Additional Statistics", box=box.ROUNDED, show_header=True, header_style="bold white", width=80)
    additional_table.add_column("Metric", style="cyan", no_wrap=True)
    additional_table.add_column("Value", style="bright_white", justify="right")
    
    additional_table.add_row("Total tokens (in + out)", f"{total_tokens:,}")
    additional_table.add_row("Total cache operations", f"{total_cache_ops:,}")
    additional_table.add_row("Calendar day average (monthly/30)", f"${monthly_average / 30:.4f}" if monthly_average > 0 else "$0.0000")
    
    if entry_count > 0:
        avg_tokens_per_entry = total_tokens / entry_count
        avg_cost_per_entry = calculated_cost / entry_count
        additional_table.add_row("Average tokens per API call", f"{avg_tokens_per_entry:.1f}")
        # additional_table.add_row("Average cost per API call", f"${avg_cost_per_entry:.4f}")
    
    console.print(additional_table)
    console.print()
    
    # Cost Comparison
#     if totals['cost'] > 0:
#         cost_difference = calculated_cost - totals['cost']
#         cost_difference_percent = (cost_difference / totals['cost']) * 100 if totals['cost'] > 0 else 0
        
#         comparison_content = f"""[bold]Reported cost:[/bold] ${totals['cost']:.4f}
# [bold]Calculated cost:[/bold] ${calculated_cost:.4f}
# [bold]Difference:[/bold] {cost_difference:+.4f} ({cost_difference_percent:+.1f}%)"""
        
#         comparison_color = "red" if abs(cost_difference_percent) > 5 else "green"
#         console.print(Panel(comparison_content, title="🔍 Cost Comparison", border_style=comparison_color, width=80))
    
    console.print()
    console.print("[dim]💡 Tip: Install with 'pip install rich' if you see formatting issues[/dim]")

if __name__ == "__main__":
    main()
