# GitHub Copilot Integration

This document describes the GitHub Copilot integration added to TreeAgent.

## Features

### GitHub Copilot Model Accessor

A new model accessor `github_copilot` has been added that interfaces with GitHub Copilot via the `gh copilot` CLI command. This accessor:

- Uses the GitHub CLI (`gh`) to interact with GitHub Copilot
- Automatically includes GitHub issue tracking tools
- Supports tool usage for enhanced functionality

### GitHub Tools

New tools have been added for GitHub issue tracking:

- `get_github_issue` - Get details of a specific issue
- `create_github_issue` - Create a new issue
- `update_github_issue` - Update an existing issue
- `comment_github_issue` - Add comments to issues
- `list_github_issues` - List issues in a repository
- `close_github_issue` - Close an issue

### Command Line Interface

A new CLI command `gh-copilot-agent-task` provides GitHub Copilot style interface:

#### Create a new task
```bash
gh-copilot-agent-task create "Create a basic Flask app with one GET /hello endpoint returning JSON {'message': 'Hello'}" --repo owner/repo --follow
```

#### Follow an existing task
```bash
gh-copilot-agent-task follow 123 --repo owner/repo
```

#### List tasks
```bash
gh-copilot-agent-task list --repo owner/repo --state open --limit 10
```

## Prerequisites

1. **GitHub CLI**: Install and authenticate with GitHub CLI
   ```bash
   # Install gh CLI (see https://github.com/cli/cli#installation)
   gh auth login
   ```

2. **GitHub Copilot**: Ensure you have GitHub Copilot access and the CLI extension installed
   ```bash
   gh extension install github/gh-copilot
   ```

## Usage Examples

### Using GitHub Copilot accessor programmatically

```python
from src.orchestrator import AgentOrchestrator
from src.dataModel.model import AccessorType

orchestrator = AgentOrchestrator(default_accessor_type=AccessorType.GITHUB_COPILOT)
project = orchestrator.implement_project("Create a REST API server")
```

### Using the CLI with GitHub integration

```bash
# Create a task and track it in a GitHub issue
gh-copilot-agent-task create "Build a React todo app" --repo myorg/myrepo --follow

# Follow up on an existing task
gh-copilot-agent-task follow 42 --repo myorg/myrepo

# List all open tasks
gh-copilot-agent-task list --repo myorg/myrepo --state open
```

### Using GitHub tools directly

```python
from src.tools.github_tools import create_issue, comment_on_issue

# Create an issue
result = create_issue("owner/repo", "New Feature Request", "Description of the feature")

# Add a comment
comment_on_issue("owner/repo", 123, "Implementation completed!")
```

## Architecture

The GitHub Copilot integration consists of:

1. **GitHubCopilotAccessor** (`src/modelAccessors/github_copilot_accessor.py`)
   - Interfaces with `gh copilot` CLI
   - Automatically includes GitHub tools
   - Handles JSON response parsing

2. **GitHub Tools** (`src/tools/github_tools.py`)
   - Complete issue management functionality
   - Uses `gh` CLI for all operations
   - Provides both functions and tool definitions

3. **Copilot CLI** (`src/cli/copilot_cli.py`)
   - GitHub Copilot style command interface
   - Integrates with GitHub issues for task tracking
   - Supports follow-up workflows

## Error Handling

The integration includes robust error handling:

- Checks for `gh` CLI availability
- Validates GitHub authentication
- Provides clear error messages
- Graceful fallbacks for optional GitHub features

## Testing

Comprehensive tests are included:

- `tests/modelAccessors/test_github_copilot_accessor.py` - Accessor tests
- `tests/tools/test_github_tools.py` - GitHub tools tests  
- `tests/cli/test_copilot_cli.py` - CLI tests

Run tests with:
```bash
pytest tests/ -v
```