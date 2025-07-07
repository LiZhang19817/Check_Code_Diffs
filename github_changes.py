#!/usr/bin/env python3

import os
from datetime import datetime, timedelta
import click
from github import Github
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.panel import Panel
from rich.columns import Columns
from dotenv import load_dotenv

# Initialize Rich console
console = Console()

def get_commit_changes(repo, branch, days=30):
    """Get the list of commits and their changes for a specific branch within the specified days."""
    try:
        # Calculate the date threshold
        since_date = datetime.now() - timedelta(days=days)
        
        # Get the branch
        branch_obj = repo.get_branch(branch)
        commits = repo.get_commits(sha=branch_obj.commit.sha, since=since_date)
        
        changes = []
        commit_list = list(commits)
        
        if not commit_list:
            return changes
        
        for commit in track(commit_list, description=f"Fetching commits from {branch} (last {days} days)..."):
            commit_info = {
                'sha': commit.sha[:7],
                'author': commit.author.login if commit.author else 'Unknown',
                'date': commit.commit.author.date,
                'message': commit.commit.message.split('\n')[0],
                'files': len(commit.files),
                'additions': commit.stats.additions,
                'deletions': commit.stats.deletions
            }
            changes.append(commit_info)
        
        return changes
    except Exception as e:
        console.print(f"[red]Error fetching commits from {branch}: {str(e)}[/red]")
        return []

def compare_branches(repo, base_branch, compare_branch):
    """Compare two branches and return the commits that are in compare_branch but not in base_branch."""
    try:
        # Get the comparison between branches
        comparison = repo.compare(base_branch, compare_branch)
        
        changes = []
        if comparison.commits:
            for commit in track(comparison.commits, description=f"Comparing {compare_branch} with {base_branch}..."):
                commit_info = {
                    'sha': commit.sha[:7],
                    'author': commit.author.login if commit.author else 'Unknown',
                    'date': commit.commit.author.date,
                    'message': commit.commit.message.split('\n')[0],
                    'files': len(commit.files),
                    'additions': commit.stats.additions,
                    'deletions': commit.stats.deletions
                }
                changes.append(commit_info)
        
        return changes, comparison
    except Exception as e:
        console.print(f"[red]Error comparing branches: {str(e)}[/red]")
        return [], None

def compare_branches_with_time_filter(repo, base_branch, compare_branch, days=30):
    """Compare two branches within a specified time period."""
    try:
        console.print(f"\n[blue]Comparing branches within last {days} days[/blue]\n")
        
        # Get commits from both branches within the time period
        base_changes = get_commit_changes(repo, base_branch, days)
        compare_changes = get_commit_changes(repo, compare_branch, days)
        
        # Get commit SHAs for easy comparison
        base_shas = {change['sha'] for change in base_changes}
        compare_shas = {change['sha'] for change in compare_changes}
        
        # Find commits unique to each branch
        unique_to_base = [change for change in base_changes if change['sha'] not in compare_shas]
        unique_to_compare = [change for change in compare_changes if change['sha'] not in base_shas]
        common_commits = [change for change in base_changes if change['sha'] in compare_shas]
        
        # Calculate statistics
        base_stats = {
            'commits': len(base_changes),
            'unique_commits': len(unique_to_base),
            'additions': sum(change['additions'] for change in base_changes),
            'deletions': sum(change['deletions'] for change in base_changes),
            'files': sum(change['files'] for change in base_changes)
        }
        
        compare_stats = {
            'commits': len(compare_changes),
            'unique_commits': len(unique_to_compare),
            'additions': sum(change['additions'] for change in compare_changes),
            'deletions': sum(change['deletions'] for change in compare_changes),
            'files': sum(change['files'] for change in compare_changes)
        }
        
        return {
            'base_changes': base_changes,
            'compare_changes': compare_changes,
            'unique_to_base': unique_to_base,
            'unique_to_compare': unique_to_compare,
            'common_commits': common_commits,
            'base_stats': base_stats,
            'compare_stats': compare_stats
        }
        
    except Exception as e:
        console.print(f"[red]Error comparing branches with time filter: {str(e)}[/red]")
        return None

def display_changes_table(changes, title, max_rows=None):
    """Display changes in a formatted table."""
    if not changes:
        console.print(f"[yellow]No changes found.[/yellow]")
        return
    
    # Limit rows if specified
    display_changes = changes[:max_rows] if max_rows else changes
    
    # Create and populate the table
    table = Table(show_header=True, header_style="bold magenta", title=title)
    table.add_column("Commit", style="cyan")
    table.add_column("Author", style="blue")
    table.add_column("Date", style="dim")
    table.add_column("Message", style="white")
    table.add_column("Files", justify="right", style="yellow")
    table.add_column("+", justify="right", style="green")
    table.add_column("-", justify="right", style="red")
    
    for change in display_changes:
        table.add_row(
            change['sha'],
            change['author'],
            change['date'].strftime("%Y-%m-%d %H:%M"),
            change['message'][:60] + "..." if len(change['message']) > 60 else change['message'],
            str(change['files']),
            str(change['additions']),
            str(change['deletions'])
        )
    
    if max_rows and len(changes) > max_rows:
        table.caption = f"Showing {max_rows} of {len(changes)} commits"
    
    console.print(table)

def display_comparison_summary(base_branch, compare_branch, comparison_data, days):
    """Display a summary of branch comparison."""
    base_stats = comparison_data['base_stats']
    compare_stats = comparison_data['compare_stats']
    
    # Create summary panels
    base_panel = Panel(
        f"[bold]Total Commits:[/bold] {base_stats['commits']}\n"
        f"[bold]Unique Commits:[/bold] {base_stats['unique_commits']}\n"
        f"[bold]Files Changed:[/bold] {base_stats['files']}\n"
        f"[bold]Additions:[/bold] [green]+{base_stats['additions']}[/green]\n"
        f"[bold]Deletions:[/bold] [red]-{base_stats['deletions']}[/red]",
        title=f"📊 {base_branch}",
        border_style="blue"
    )
    
    compare_panel = Panel(
        f"[bold]Total Commits:[/bold] {compare_stats['commits']}\n"
        f"[bold]Unique Commits:[/bold] {compare_stats['unique_commits']}\n"
        f"[bold]Files Changed:[/bold] {compare_stats['files']}\n"
        f"[bold]Additions:[/bold] [green]+{compare_stats['additions']}[/green]\n"
        f"[bold]Deletions:[/bold] [red]-{compare_stats['deletions']}[/red]",
        title=f"📊 {compare_branch}",
        border_style="green"
    )
    
    summary_panel = Panel(
        f"[bold]Time Period:[/bold] Last {days} days\n"
        f"[bold]Common Commits:[/bold] {len(comparison_data['common_commits'])}\n"
        f"[bold]Branch Divergence:[/bold]\n"
        f"  • {base_branch} unique: {len(comparison_data['unique_to_base'])}\n"
        f"  • {compare_branch} unique: {len(comparison_data['unique_to_compare'])}",
        title="📈 Comparison Summary",
        border_style="yellow"
    )
    
    console.print(Columns([base_panel, compare_panel]))
    console.print(summary_panel)
    console.print()

def normalize_repo_name(repo):
    """Normalize repository name to owner/repository format."""
    # Remove protocol if present
    if repo.startswith('https://'):
        repo = repo[8:]
    elif repo.startswith('http://'):
        repo = repo[7:]
    
    # Remove github.com/ if present
    if repo.startswith('github.com/'):
        repo = repo[11:]
    
    # Remove trailing .git if present
    if repo.endswith('.git'):
        repo = repo[:-4]
    
    # Remove trailing slash if present
    if repo.endswith('/'):
        repo = repo[:-1]
    
    return repo

@click.command()
@click.option('--token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--days', default=30, type=int, help='Number of days to look back for changes (default: 30)')
@click.option('--compare', help='Compare two branches (format: base_branch..compare_branch)')
@click.option('--limit', default=20, type=int, help='Limit number of commits to display per branch (default: 20)')
@click.argument('repo', required=True)
@click.argument('branch', default='main')
def main(token, repo, branch, days, compare, limit):
    """
    CLI utility to list code changes from a GitHub repository.
    
    REPO can be in any of these formats:
    - owner/repository
    - github.com/owner/repository  
    - https://github.com/owner/repository
    
    BRANCH is optional and defaults to 'main'
    
    Use --compare to compare two branches:
    --compare main..feature-branch
    
    Use --days to filter by time period (works with both single branch and comparison modes)
    """
    if not token:
        console.print("[red]Error: GitHub token is required. Either provide --token or set GITHUB_TOKEN environment variable.[/red]")
        return

    try:
        # Normalize repository name
        normalized_repo = normalize_repo_name(repo)
        
        # Initialize GitHub client
        g = Github(token)
        github_repo = g.get_repo(normalized_repo)
        
        if compare:
            # Branch comparison mode
            if '..' not in compare:
                console.print("[red]Error: Compare format should be 'base_branch..compare_branch'[/red]")
                return
            
            base_branch, compare_branch = compare.split('..')
            console.print(f"\n[blue]Repository:[/blue] {normalized_repo}")
            console.print(f"[blue]Comparing:[/blue] {base_branch} ↔ {compare_branch}")
            console.print(f"[blue]Time Period:[/blue] Last {days} days\n")
            
            # Get time-filtered comparison
            comparison_data = compare_branches_with_time_filter(github_repo, base_branch, compare_branch, days)
            
            if comparison_data:
                # Display summary
                display_comparison_summary(base_branch, compare_branch, comparison_data, days)
                
                # Display unique commits for each branch
                if comparison_data['unique_to_base']:
                    display_changes_table(
                        comparison_data['unique_to_base'], 
                        f"🔵 Commits unique to {base_branch}",
                        limit
                    )
                    console.print()
                
                if comparison_data['unique_to_compare']:
                    display_changes_table(
                        comparison_data['unique_to_compare'], 
                        f"🟢 Commits unique to {compare_branch}",
                        limit
                    )
                    console.print()
                
                if comparison_data['common_commits']:
                    display_changes_table(
                        comparison_data['common_commits'], 
                        f"🟡 Common commits in both branches",
                        limit
                    )
            
        else:
            # Single branch mode
            console.print(f"\n[blue]Fetching changes for {normalized_repo} ({branch}) - Last {days} days[/blue]\n")
            
            changes = get_commit_changes(github_repo, branch, days)
            
            if not changes:
                console.print(f"[yellow]No changes found in the last {days} days.[/yellow]")
                return
            
            display_changes_table(changes, f"Recent commits in {branch}", limit)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
    finally:
        if 'g' in locals():
            g.close()

if __name__ == '__main__':
    # Load environment variables from .env file
    load_dotenv()
    main() 