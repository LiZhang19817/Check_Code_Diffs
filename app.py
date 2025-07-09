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

@app.route('/')
def index():
    """Main page with the UI interface."""
    return render_template('index.html')

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
        days = data.get('days', 30)
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
        days = data.get('days', 30)
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 