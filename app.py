#!/usr/bin/env python3

import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from github import Github
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
CORS(app)

def normalize_repo_name(repo):
    """Normalize repository name to owner/repository format."""
    if repo.startswith('https://'):
        repo = repo[8:]
    elif repo.startswith('http://'):
        repo = repo[7:]
    
    if repo.startswith('github.com/'):
        repo = repo[11:]
    
    if repo.endswith('.git'):
        repo = repo[:-4]
    
    if repo.endswith('/'):
        repo = repo[:-1]
    
    return repo

def get_commit_changes(repo, branch, days=30):
    """Get the list of commits and their changes for a specific branch within the specified days."""
    try:
        since_date = datetime.now() - timedelta(days=days)
        branch_obj = repo.get_branch(branch)
        commits = repo.get_commits(sha=branch_obj.commit.sha, since=since_date)
        
        changes = []
        for commit in list(commits):
            commit_info = {
                'sha': commit.sha[:7],
                'full_sha': commit.sha,
                'author': commit.author.login if commit.author else 'Unknown',
                'date': commit.commit.author.date.isoformat(),
                'message': commit.commit.message.split('\n')[0],
                'full_message': commit.commit.message,
                'files': len(commit.files),
                'additions': commit.stats.additions,
                'deletions': commit.stats.deletions,
                'url': commit.html_url
            }
            changes.append(commit_info)
        
        return changes
    except Exception as e:
        raise Exception(f"Error fetching commits from {branch}: {str(e)}")

def compare_branches_with_time_filter(repo, base_branch, compare_branch, days=30):
    """Compare two branches within a specified time period."""
    try:
        base_changes = get_commit_changes(repo, base_branch, days)
        compare_changes = get_commit_changes(repo, compare_branch, days)
        
        base_shas = {change['sha'] for change in base_changes}
        compare_shas = {change['sha'] for change in compare_changes}
        
        unique_to_base = [change for change in base_changes if change['sha'] not in compare_shas]
        unique_to_compare = [change for change in compare_changes if change['sha'] not in base_shas]
        common_commits = [change for change in base_changes if change['sha'] in compare_shas]
        
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
        raise Exception(f"Error comparing branches: {str(e)}")

def get_pull_requests(repo, branch, state='all', days=None, jira_id=None):
    """Get pull requests for a specific branch, optionally filtered by Jira ID."""
    try:
        print(f"Fetching pull requests for branch: '{branch}', state: '{state}', days: {days}, jira_id: {jira_id}")
        
        # Calculate the date threshold if days is specified
        since_date = None
        if days:
            # Create timezone-aware datetime to match GitHub API responses
            from datetime import timezone
            since_date = datetime.now(timezone.utc) - timedelta(days=days)
            print(f"Date filter: PRs updated after {since_date}")
        
        # Get pull requests with error handling and pagination limit
        try:
            # Limit initial fetch to avoid timeout - get first 100 PRs max
            pulls = repo.get_pulls(state=state, sort='updated', direction='desc')
            pull_list = []
            count = 0
            max_prs_to_fetch = 100  # Limit to prevent timeout
            
            print(f"Fetching up to {max_prs_to_fetch} pull requests with state '{state}'...")
            for pr in pulls:
                pull_list.append(pr)
                count += 1
                if count >= max_prs_to_fetch:
                    print(f"Reached limit of {max_prs_to_fetch} PRs to prevent timeout")
                    break
            
            print(f"Fetched {len(pull_list)} pull requests for processing")
        except Exception as github_error:
            raise Exception(f"GitHub API error when fetching pull requests: {str(github_error)}")
        
        # If no PRs found, return empty list
        if not pull_list:
            print("No pull requests found in repository")
            return []
        
        # Debug: Print first few PRs to see what branches they have
        print("Sample of PRs found:")
        for i, pr in enumerate(pull_list[:3]):
            try:
                print(f"  PR #{pr.number}: '{pr.title}' - FROM: '{pr.head.ref}' TO: '{pr.base.ref}' - State: {pr.state}")
            except Exception as debug_error:
                print(f"  PR #{pr.number}: Error accessing PR details - {debug_error}")
        
        pull_requests = []
        matched_prs = 0
        date_filtered_prs = 0
        jira_filtered_prs = 0
        
        for pr in pull_list:
            try:
                # Filter by branch (head branch for PRs created from this branch, or base branch for PRs targeting this branch)
                include_pr = False
                pr_type = None
                
                # More flexible branch matching - handle case sensitivity and normalize
                pr_head_branch = pr.head.ref.strip()
                pr_base_branch = pr.base.ref.strip()
                target_branch = branch.strip()
                
                print(f"Checking PR #{pr.number}: head='{pr_head_branch}' base='{pr_base_branch}' target='{target_branch}'")
                
                if pr_head_branch == target_branch:
                    include_pr = True
                    pr_type = "from"  # PR created from this branch
                    print(f"  ✓ Matched as FROM branch")
                elif pr_base_branch == target_branch:
                    include_pr = True
                    pr_type = "to"    # PR targeting this branch
                    print(f"  ✓ Matched as TO branch")
                else:
                    print(f"  ✗ No match")
                
                if include_pr:
                    matched_prs += 1
                    
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
                                date_filtered_prs += 1
                                print(f"  ✗ Filtered out by date: {pr_updated} < {since_date}")
                                continue
                        except Exception as date_error:
                            print(f"  ⚠ Date comparison error for PR #{pr.number}: {date_error}")
                            # If date comparison fails, include the PR to be safe
                            pass
                    
                    # Apply Jira ID filter if specified
                    if jira_id:
                        jira_pattern = jira_id.upper()
                        pr_title = pr.title.upper()
                        pr_body = (pr.body or "").upper()
                        
                        # Check if Jira ID is mentioned in title or body
                        title_match = jira_pattern in pr_title
                        body_match = jira_pattern in pr_body
                        
                        if not title_match and not body_match:
                            jira_filtered_prs += 1
                            print(f"  ✗ Filtered out by Jira ID: '{jira_id}' not found in PR #{pr.number} ('{pr.title[:50]}...')")
                            continue
                        else:
                            match_location = "title" if title_match else "body"
                            print(f"  ✓ Jira ID '{jira_id}' found in {match_location} of PR #{pr.number}: '{pr.title[:50]}...'")
                    
                    pr_info = {
                        'number': pr.number,
                        'title': pr.title,
                        'state': pr.state,
                        'author': pr.user.login if pr.user else 'Unknown',
                        'created_at': pr.created_at.isoformat(),
                        'updated_at': pr.updated_at.isoformat(),
                        'head_branch': pr_head_branch,
                        'base_branch': pr_base_branch,
                        'url': pr.html_url,
                        'type': pr_type,
                        'draft': pr.draft,
                        'mergeable': pr.mergeable,
                        'comments': pr.comments,
                        'review_comments': pr.review_comments,
                        'commits': pr.commits,
                        'additions': pr.additions,
                        'deletions': pr.deletions,
                        'changed_files': pr.changed_files,
                        'body': pr.body  # Include body for Jira ID matching
                    }
                    pull_requests.append(pr_info)
                    print(f"  ✓ Added PR #{pr.number} to results")
                    
            except Exception as pr_error:
                print(f"Error processing PR #{pr.number}: {str(pr_error)}")
                continue  # Skip this PR and continue with others
        
        # Sort by updated_at descending (most recent first)
        pull_requests.sort(key=lambda x: x['updated_at'], reverse=True)
        
        print(f"Summary:")
        print(f"  - Total PRs in repo: {len(pull_list)}")
        print(f"  - PRs matching branch '{branch}': {matched_prs}")
        print(f"  - PRs filtered out by date: {date_filtered_prs}")
        if jira_id:
            print(f"  - PRs filtered out by Jira ID '{jira_id}': {jira_filtered_prs}")
        print(f"  - Final PR count: {len(pull_requests)}")
        
        # If no PRs found for the specific branch, provide helpful information
        if len(pull_requests) == 0 and len(pull_list) > 0:
            print(f"No PRs found for branch '{branch}'. Available branches in existing PRs:")
            unique_branches = set()
            for pr in pull_list[:10]:  # Show first 10 PRs
                try:
                    unique_branches.add(f"HEAD: {pr.head.ref}")
                    unique_branches.add(f"BASE: {pr.base.ref}")
                except:
                    pass
            for branch_info in sorted(unique_branches):
                print(f"  - {branch_info}")
        
        return pull_requests
    except Exception as e:
        print(f"Error in get_pull_requests: {str(e)}")
        raise Exception(f"Error fetching pull requests for {branch}: {str(e)}")

@app.route('/')
def index():
    """Main page with the UI interface."""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        'status': 'ok',
        'message': 'Flask server is running',
        'endpoints': [
            '/api/validate-token',
            '/api/branches',
            '/api/changes', 
            '/api/compare',
            '/api/pull-requests'
        ]
    })

@app.route('/api/branches/<path:repo>')
def get_branches(repo):
    """Get list of branches for a repository."""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'GitHub token is required'}), 401
        
        normalized_repo = normalize_repo_name(repo)
        g = Github(token)
        github_repo = g.get_repo(normalized_repo)
        
        branches = []
        for branch in github_repo.get_branches():
            branches.append({
                'name': branch.name,
                'protected': branch.protected,
                'last_commit': branch.commit.sha[:7]
            })
        
        return jsonify({'branches': branches})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/changes', methods=['POST'])
def get_changes():
    """Get changes for a single branch."""
    try:
        data = request.json
        token = data.get('token')
        repo = data.get('repo')
        branch = data.get('branch', 'main')
        days = data.get('days', 3)
        limit = data.get('limit', 20)
        
        if not token:
            return jsonify({'error': 'GitHub token is required'}), 401
        
        if not repo:
            return jsonify({'error': 'Repository is required'}), 400
        
        normalized_repo = normalize_repo_name(repo)
        g = Github(token)
        github_repo = g.get_repo(normalized_repo)
        
        changes = get_commit_changes(github_repo, branch, days)
        
        # Apply limit
        if limit and len(changes) > limit:
            changes = changes[:limit]
        
        return jsonify({
            'success': True,
            'repository': normalized_repo,
            'branch': branch,
            'days': days,
            'total_commits': len(changes),
            'changes': changes
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare', methods=['POST'])
def compare_branches():
    """Compare two branches."""
    try:
        data = request.json
        token = data.get('token')
        repo = data.get('repo')
        base_branch = data.get('base_branch')
        compare_branch = data.get('compare_branch')
        days = data.get('days', 3)
        limit = data.get('limit', 20)
        
        if not token:
            return jsonify({'error': 'GitHub token is required'}), 401
        
        if not repo:
            return jsonify({'error': 'Repository is required'}), 400
        
        if not base_branch or not compare_branch:
            return jsonify({'error': 'Both base and compare branches are required'}), 400
        
        normalized_repo = normalize_repo_name(repo)
        g = Github(token)
        github_repo = g.get_repo(normalized_repo)
        
        comparison_data = compare_branches_with_time_filter(
            github_repo, base_branch, compare_branch, days
        )
        
        # Apply limits
        if limit:
            comparison_data['unique_to_base'] = comparison_data['unique_to_base'][:limit]
            comparison_data['unique_to_compare'] = comparison_data['unique_to_compare'][:limit]
            comparison_data['common_commits'] = comparison_data['common_commits'][:limit]
        
        return jsonify({
            'success': True,
            'repository': normalized_repo,
            'base_branch': base_branch,
            'compare_branch': compare_branch,
            'days': days,
            'comparison': comparison_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/branches', methods=['POST'])
def get_repository_branches():
    """Get list of branches for a repository via POST."""
    try:
        data = request.json
        token = data.get('token')
        repo = data.get('repo')
        
        if not token:
            return jsonify({'success': False, 'error': 'GitHub token is required'}), 401
        
        if not repo:
            return jsonify({'success': False, 'error': 'Repository is required'}), 400
        
        normalized_repo = normalize_repo_name(repo)
        g = Github(token)
        github_repo = g.get_repo(normalized_repo)
        
        branches = []
        for branch in github_repo.get_branches():
            branches.append(branch.name)
        
        # Sort branches to put master/main first
        branches.sort(key=lambda x: (x not in ['master', 'main'], x))
        
        return jsonify({
            'success': True,
            'branches': branches
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/validate-token', methods=['POST'])
def validate_token():
    """Validate GitHub token."""
    try:
        data = request.json
        token = data.get('token')
        
        if not token:
            return jsonify({'valid': False, 'error': 'Token is required'}), 400
        
        g = Github(token)
        user = g.get_user()
        
        return jsonify({
            'valid': True,
            'user': {
                'login': user.login,
                'name': user.name,
                'avatar_url': user.avatar_url
            }
        })
    
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 401

@app.route('/api/pull-requests', methods=['POST'])
def get_pull_requests_api():
    """Get pull requests for a specific branch."""
    try:
        # Ensure we can parse the JSON request
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        token = data.get('token')
        repo = data.get('repo')
        branch = data.get('branch', 'main')
        state = data.get('state', 'all')
        days = data.get('days')
        limit = data.get('limit', 20)
        jira_id = data.get('jira_id', '').strip() or None
        
        if not token:
            return jsonify({'success': False, 'error': 'GitHub token is required'}), 401
        
        if not repo:
            return jsonify({'success': False, 'error': 'Repository is required'}), 400
        
        if not branch:
            return jsonify({'success': False, 'error': 'Branch is required'}), 400
        
        normalized_repo = normalize_repo_name(repo)
        g = Github(token)
        github_repo = g.get_repo(normalized_repo)
        
        prs = get_pull_requests(github_repo, branch, state, days, jira_id)
        
        # Apply limit
        if limit and len(prs) > limit:
            prs = prs[:limit]
        
        # Calculate statistics
        from_branch_prs = [pr for pr in prs if pr['type'] == 'from']
        to_branch_prs = [pr for pr in prs if pr['type'] == 'to']
        open_prs = [pr for pr in prs if pr['state'] == 'open']
        closed_prs = [pr for pr in prs if pr['state'] == 'closed']
        draft_prs = [pr for pr in prs if pr['draft']]
        
        stats = {
            'total': len(prs),
            'from_branch': len(from_branch_prs),
            'to_branch': len(to_branch_prs),
            'open': len(open_prs),
            'closed': len(closed_prs),
            'draft': len(draft_prs)
        }
        
        return jsonify({
            'success': True,
            'repository': normalized_repo,
            'branch': branch,
            'state': state,
            'days': days,
            'jira_id': jira_id,
            'total_prs': len(prs),
            'stats': stats,
            'pull_requests': prs
        })
    
    except Exception as e:
        print(f"Error in pull-requests API: {str(e)}")  # Server-side logging
        import traceback
        traceback.print_exc()  # Print full traceback for debugging
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 