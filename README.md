# Quay QE Team Changes Analyzer

A comprehensive tool to analyze and compare code changes from GitHub repositories, available as both a command-line utility and a modern web interface.

## Examples
<img width="1066" alt="image" src="https://github.com/user-attachments/assets/177417df-f825-4ef3-a0be-8e10958bf542" />
<img width="1066" alt="image" src="https://github.com/user-attachments/assets/3257d7ef-0818-4678-9975-9a1fcd00fa38" />


## Features

### 🖥️ **Command Line Interface (CLI)**
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

### 🌐 **Web Interface**
- **Modern, responsive UI** with Bootstrap styling
- **Interactive forms** for easy repository and branch selection
- **Real-time GitHub token validation** with user info display
- **Dual-mode operation**:
  - Single branch analysis
  - Time-filtered branch comparison
- **Rich data visualization**:
  - Side-by-side statistics panels
  - Color-coded commit tables
  - Interactive commit links to GitHub
- **Persistent token storage** in browser localStorage
- **Mobile-friendly design** that works on all devices

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

You need a GitHub personal access token to use this utility. You can provide it in several ways:

### For CLI:
1. Set it as an environment variable:
```bash
export GITHUB_TOKEN=your_github_token
```

2. Create a `.env` file in the project directory:
```
GITHUB_TOKEN=your_github_token
```

### For Web Interface:
- Enter your token directly in the web interface
- The token is validated in real-time and stored securely in your browser

### Creating a GitHub Token:
1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Generate a new token with `repo` scope
3. Copy the token and save it securely

## Usage

### 🌐 Web Interface (Recommended)

Start the web interface:
```bash
python start_web.py
```

The web interface will automatically open in your browser at `http://localhost:5000`

**Features:**
- **Token Management**: Validate and store your GitHub token
- **Single Branch Analysis**: Analyze commits from a specific branch
- **Branch Comparison**: Compare two branches with time filtering
- **Interactive Results**: Click commit hashes to view on GitHub
- **Responsive Design**: Works on desktop, tablet, and mobile

### 🖥️ Command Line Interface

The CLI accepts repository names in multiple formats and supports both single branch analysis and time-filtered branch comparison:

#### Single Branch Mode (Default)

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

#### Branch Comparison Mode

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

#### Advanced Examples

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

## API Endpoints (Web Interface)

The web interface provides these REST API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/api/validate-token` | POST | Validate GitHub token |
| `/api/branches/<repo>` | GET | Get repository branches |
| `/api/changes` | POST | Get single branch changes |
| `/api/compare` | POST | Compare two branches |

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--token` | GitHub personal access token | From `GITHUB_TOKEN` env var |
| `--days` | Number of days to look back | 30 |
| `--compare` | Compare branches (format: `base..compare`) | None |
| `--limit` | Max commits to display per section | 20 |

## Output

### CLI Output

#### Single Branch Mode
The utility displays a table with commit information:
- Short commit hash
- Author username
- Commit date and time
- First line of commit message
- Number of files changed
- Number of lines added (green)
- Number of lines deleted (red)

#### Branch Comparison Mode
The utility shows:
1. **Side-by-side summary panels** with statistics for each branch
2. **Comparison summary** with common commits and divergence info
3. **Three detailed sections**:
   - 🔵 Commits unique to base branch
   - 🟢 Commits unique to compare branch
   - 🟡 Common commits in both branches

### Web Interface Output

The web interface provides:
- **Interactive statistics cards** with color-coded metrics
- **Sortable, clickable commit tables** with GitHub links
- **Responsive design** that adapts to screen size
- **Real-time loading indicators** and error handling
- **Persistent user session** with token storage

## Development

### Running the Web Interface for Development

```bash
# Start development server
python start_web.py

# Or run Flask directly
python app.py
```

### Production Deployment

For production deployment, use a WSGI server like Gunicorn:

```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Security Notes

- GitHub tokens are handled securely and never logged
- Web interface stores tokens only in browser localStorage
- All API requests require valid authentication
- CORS is configured for local development

## Troubleshooting

### Common Issues

1. **"GitHub token is required"**: Ensure your token is set in environment variables or entered in the web interface
2. **"Repository not found"**: Check the repository name format and your token permissions
3. **"Rate limit exceeded"**: GitHub API has rate limits; wait a few minutes and try again
4. **Web interface not loading**: Ensure all dependencies are installed and port 5000 is available

### Getting Help

- Check the GitHub token has appropriate permissions (`repo` scope)
- Verify the repository name format: `owner/repository`
- Ensure the branch names exist in the repository
- For web interface issues, check browser console for errors

This enhanced tool helps teams understand:
- **Branch divergence**: How much branches have diverged over time
- **Feature progress**: What's been developed in feature branches
- **Integration planning**: What needs to be merged and when
- **Risk assessment**: Scope of changes for releases 
