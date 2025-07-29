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

def get_pull_requests(repo, branch, state='all', days=None, jira_id=None):
    """Get pull requests for a specific branch, optionally filtered by Jira ID."""
    try:
        # Calculate the date threshold if days is specified
        since_date = None
        if days:
            # Create timezone-aware datetime to match GitHub API responses
            from datetime import timezone
            since_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get pull requests
        pulls = repo.get_pulls(state=state, sort='updated', direction='desc')
        
        pull_requests = []
        pull_list = list(pulls)
        
        if not pull_list:
            return pull_requests
        
        for pr in track(pull_list, description=f"Fetching pull requests for {branch}..."):
            # Filter by branch (head branch for PRs created from this branch, or base branch for PRs targeting this branch)
            include_pr = False
            pr_type = None
            
            if pr.head.ref == branch:
                include_pr = True
                pr_type = "from"  # PR created from this branch
            elif pr.base.ref == branch:
                include_pr = True
                pr_type = "to"    # PR targeting this branch
            
            if include_pr:
                # Apply date filter if specified
                if since_date:
                    try:
                        # Ensure both datetimes are comparable
                        pr_updated = pr.updated_at
                        if pr_updated.tzinfo is None:
                            # If PR datetime is naive, make it UTC
                            from datetime import timezone
                            pr_updated = pr_updated.replace(tzinfo=timezone.utc)
                        
                        if pr_updated < since_date:
                            continue
                    except Exception as date_error:
                        console.print(f"[yellow]Date comparison error for PR #{pr.number}: {date_error}[/yellow]")
                        # If date comparison fails, include the PR to be safe
                        pass
                
                # Apply Jira ID filter if specified
                if jira_id:
                    jira_pattern = jira_id.upper()
                    pr_title = pr.title.upper()
                    pr_body = (pr.body or "").upper()
                    
                    # Check if Jira ID is mentioned in title or body
                    if jira_pattern not in pr_title and jira_pattern not in pr_body:
                        continue
                
                pr_info = {
                    'number': pr.number,
                    'title': pr.title,
                    'state': pr.state,
                    'author': pr.user.login if pr.user else 'Unknown',
                    'created_at': pr.created_at,
                    'updated_at': pr.updated_at,
                    'head_branch': pr.head.ref,
                    'base_branch': pr.base.ref,
                    'url': pr.html_url,
                    'type': pr_type,
                    'draft': pr.draft,
                    'mergeable': pr.mergeable,
                    'comments': pr.comments,
                    'review_comments': pr.review_comments,
                    'commits': pr.commits,
                    'additions': pr.additions,
                    'deletions': pr.deletions,
                    'changed_files': pr.changed_files
                }
                pull_requests.append(pr_info)
        
        # Sort by updated_at descending (most recent first)
        pull_requests.sort(key=lambda x: x['updated_at'], reverse=True)
        
        return pull_requests
    except Exception as e:
        console.print(f"[red]Error fetching pull requests for {branch}: {str(e)}[/red]")
        return []

def display_pull_requests_table(pull_requests, title, max_rows=None):
    """Display pull requests in a formatted table."""
    if not pull_requests:
        console.print(f"[yellow]No pull requests found.[/yellow]")
        return
    
    # Limit rows if specified
    display_prs = pull_requests[:max_rows] if max_rows else pull_requests
    
    # Create and populate the table
    table = Table(show_header=True, header_style="bold magenta", title=title)
    table.add_column("PR #", style="cyan")
    table.add_column("State", style="blue")
    table.add_column("Type", style="yellow")
    table.add_column("Title", style="white")
    table.add_column("Author", style="green")
    table.add_column("Updated", style="dim")
    table.add_column("Comments", justify="right", style="magenta")
    table.add_column("Files", justify="right", style="yellow")
    table.add_column("+", justify="right", style="green")
    table.add_column("-", justify="right", style="red")
    
    for pr in display_prs:
        # Determine state color
        state_color = {
            'open': 'green',
            'closed': 'red',
            'merged': 'blue'
        }.get(pr['state'], 'white')
        
        # Determine type display
        type_display = {
            'from': f"FROM {pr['head_branch']}",
            'to': f"TO {pr['base_branch']}"
        }.get(pr['type'], 'UNKNOWN')
        
        # Add draft indicator
        if pr['draft']:
            state_display = f"[dim]{pr['state'].upper()} (DRAFT)[/dim]"
        else:
            state_display = pr['state'].upper()
        
        table.add_row(
            f"#{pr['number']}",
            f"[{state_color}]{state_display}[/{state_color}]",
            type_display,
            pr['title'][:80] + "..." if len(pr['title']) > 80 else pr['title'],
            pr['author'],
            pr['updated_at'].strftime("%Y-%m-%d %H:%M"),
            str(pr['comments'] + pr['review_comments']),
            str(pr['changed_files']),
            str(pr['additions']),
            str(pr['deletions'])
        )
    
    if max_rows and len(pull_requests) > max_rows:
        table.caption = f"Showing {max_rows} of {len(pull_requests)} pull requests"
    
    console.print(table)

@click.command()
@click.option('--token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--days', default=3, type=int, help='Number of days to look back for changes (default: 3)')
@click.option('--compare', help='Compare two branches (format: base_branch..compare_branch)')
@click.option('--pull-requests', is_flag=True, help='List pull requests for the specified branch')
@click.option('--pr-state', default='all', type=click.Choice(['open', 'closed', 'all']), help='Filter pull requests by state (default: all)')
@click.option('--jira-id', help='Filter pull requests containing this Jira ID (e.g., PROJQUAY-9184)')
@click.option('--limit', default=20, type=int, help='Limit number of commits/PRs to display per branch (default: 20)')
@click.argument('repo', required=True)
@click.argument('branch', default='main')
def main(token, repo, branch, days, compare, pull_requests, pr_state, jira_id, limit):
    """
    CLI utility to list code changes from a GitHub repository.
    
    REPO can be in any of these formats:
    - owner/repository
    - github.com/owner/repository  
    - https://github.com/owner/repository
    
    BRANCH is optional and defaults to 'main'
    
    Use --compare to compare two branches:
    --compare main..feature-branch
    
    Use --pull-requests to list pull requests for the branch:
    --pull-requests --pr-state open
    
    Use --days to filter by time period (works with all modes)
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
        
        if pull_requests:
            # Pull requests mode
            console.print(f"\n[blue]Repository:[/blue] {normalized_repo}")
            console.print(f"[blue]Branch:[/blue] {branch}")
            console.print(f"[blue]State Filter:[/blue] {pr_state}")
            if days:
                console.print(f"[blue]Time Period:[/blue] Last {days} days")
            if jira_id:
                console.print(f"[blue]Jira ID Filter:[/blue] {jira_id}")
            console.print()
            
            # Get pull requests
            prs = get_pull_requests(github_repo, branch, pr_state, days, jira_id)
            
            if not prs:
                console.print(f"[yellow]No pull requests found for branch '{branch}' with state '{pr_state}'.[/yellow]")
                return
            
            # Create summary panel
            from_branch_prs = [pr for pr in prs if pr['type'] == 'from']
            to_branch_prs = [pr for pr in prs if pr['type'] == 'to']
            
            summary_panel = Panel(
                f"[bold]Total Pull Requests:[/bold] {len(prs)}\n"
                f"[bold]PRs FROM {branch}:[/bold] {len(from_branch_prs)}\n"
                f"[bold]PRs TO {branch}:[/bold] {len(to_branch_prs)}\n"
                f"[bold]Open PRs:[/bold] {len([pr for pr in prs if pr['state'] == 'open'])}\n"
                f"[bold]Closed PRs:[/bold] {len([pr for pr in prs if pr['state'] == 'closed'])}\n"
                f"[bold]Draft PRs:[/bold] {len([pr for pr in prs if pr['draft']])}",
                title=f"📋 Pull Request Summary for {branch}",
                border_style="blue"
            )
            console.print(summary_panel)
            console.print()
            
            display_pull_requests_table(prs, f"Pull Requests for {branch}", limit)
            
        elif compare:
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