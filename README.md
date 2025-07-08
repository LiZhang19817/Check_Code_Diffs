# Quay QE team GitHub Repository Changes list CLI

A command-line utility to list code changes from a GitHub repository for a specific branch with advanced branch comparison capabilities.

# Example:
Compare the changes of Quay latest branches redhat-3.14 and redhat-3.15
![image](https://github.com/user-attachments/assets/71d9e91b-b27d-40d2-975f-86fc43a3547f)


## Features

- Display recent commits from a specified GitHub repository and branch
- **Time-filtered branch comparison**: Compare two branches within a specific time period
- Show commit details including:
  - Commit hash
  - Author
  - Date
  - Commit message
  - Number of files changed
  - Number of additions and deletions
- **Advanced comparison analytics**:
  - Unique commits per branch
  - Common commits between branches
  - Statistical summaries with visual panels
- Beautiful terminal output with colors and formatting
- Progress tracking while fetching commits
- Configurable display limits

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

You need a GitHub personal access token to use this utility. You can provide it in two ways:

1. Set it as an environment variable:
```bash
export GITHUB_TOKEN=your_github_token
```

2. Create a `.env` file in the project directory:
```
GITHUB_TOKEN=your_github_token
```

To create a GitHub personal access token:
1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token with `repo` scope
3. Copy the token and save it securely

## Usage

The utility accepts repository names in multiple formats and supports both single branch analysis and time-filtered branch comparison:

### Single Branch Mode (Default)

```bash
# Basic usage (defaults to 'main' branch and last 30 days)
python github_changes.py owner/repository

# Using github.com format
python github_changes.py github.com/owner/repository

# Using full URL
python github_changes.py https://github.com/owner/repository

# Specify a different branch
python github_changes.py owner/repository development

# Specify number of days to look back
python github_changes.py --days 7 owner/repository

# Limit number of commits displayed
python github_changes.py --limit 10 owner/repository
```

### Branch Comparison Mode

Compare changes between two branches, optionally within a specific time period:

```bash
# Compare all commits between branches (uses GitHub's native comparison)
python github_changes.py --compare main..feature-branch owner/repository

# Compare branches within last 7 days (time-filtered comparison)
python github_changes.py --compare main..feature-branch --days 7 owner/repository

# Compare with custom display limit
python github_changes.py --compare main..dev --days 14 --limit 15 owner/repository

# Compare with token
python github_changes.py --token YOUR_TOKEN --compare main..feature owner/repository
```

### Advanced Examples

```bash
# Get last 30 days of changes (default)
python github_changes.py microsoft/vscode main

# Get last 7 days of changes
python github_changes.py --days 7 github.com/quay/quay master

# Get last 24 hours of changes
python github_changes.py --days 1 https://github.com/facebook/react

# Compare what changed in last week between main and development
python github_changes.py --compare main..development --days 7 quay/quay

# Compare last 3 days between feature and main branches
python github_changes.py --compare main..feature-auth --days 3 owner/repo

# Show only 5 commits per section in comparison
python github_changes.py --compare main..dev --limit 5 owner/repo
```

## Time-Filtered Branch Comparison Features

When using `--compare` with `--days`, the tool provides comprehensive analysis:

### 📊 **Summary Statistics**
- **Per Branch**: Total commits, unique commits, files changed, additions/deletions
- **Comparison Overview**: Common commits and branch divergence metrics
- **Time Period**: Clear indication of the analysis timeframe

### 🔍 **Detailed Commit Analysis**
- **Unique to Base Branch**: Commits only in the base branch (e.g., hotfixes)
- **Unique to Compare Branch**: Commits only in the compare branch (e.g., new features)
- **Common Commits**: Shared commits between branches (e.g., merged changes)

### 🎨 **Enhanced Visualization**
- **Color-coded sections**: Different colors for each branch and commit type
- **Side-by-side statistics**: Easy comparison of branch metrics
- **Truncated messages**: Clean display with full information preserved
- **Commit limits**: Configurable display limits to avoid overwhelming output

## Use Cases

### 🚀 **Development Workflow**
```bash
# Daily standup: What changed yesterday?
python github_changes.py --days 1 owner/repo

# Weekly review: Compare feature branch progress
python github_changes.py --compare main..feature --days 7 owner/repo

# Sprint review: Last 14 days of development vs main
python github_changes.py --compare main..development --days 14 owner/repo
```

### 🔄 **Release Management**
```bash
# Pre-release: What's new in release branch?
python github_changes.py --compare main..release-v2.0 --days 30 owner/repo

# Hotfix analysis: What changed in production?
python github_changes.py --compare release..hotfix --days 3 owner/repo
```

### 🧪 **Environment Comparison**
```bash
# Staging vs Production differences
python github_changes.py --compare production..staging --days 7 owner/repo

# Development vs Testing environment
python github_changes.py --compare testing..development --days 14 owner/repo
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--token` | GitHub personal access token | From `GITHUB_TOKEN` env var |
| `--days` | Number of days to look back | 30 |
| `--compare` | Compare branches (format: `base..compare`) | None |
| `--limit` | Max commits to display per section | 20 |

## Output

### Single Branch Mode
The utility displays a table with commit information:
- Short commit hash
- Author username
- Commit date and time
- First line of commit message
- Number of files changed
- Number of lines added (green)
- Number of lines deleted (red)

### Branch Comparison Mode
The utility shows:
1. **Side-by-side summary panels** with statistics for each branch
2. **Comparison summary** with common commits and divergence info
3. **Three detailed sections**:
   - 🔵 Commits unique to base branch
   - 🟢 Commits unique to compare branch
   - 🟡 Common commits in both branches

This enhanced comparison mode helps teams understand:
- **Branch divergence**: How much branches have diverged over time
- **Feature progress**: What's been developed in feature branches
- **Integration planning**: What needs to be merged and when
- **Risk assessment**: Scope of changes for releases 
