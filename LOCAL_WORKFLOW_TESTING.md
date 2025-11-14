# Local GitHub Actions Testing Guide

## Quick Start

Test your GitHub Actions workflows locally before pushing to avoid commit spam!

### Using the helper script:

```bash
# Show available options
./test-workflow-locally.sh

# Test just the Python version extraction
act -j get-python-version

# Test the full CI workflow
act -W .github/workflows/ci.yml

# Test just the CI tests job
act -j ci
```

## Common Commands

### List all workflows and jobs

```bash
act -l
```

### Run a specific job

```bash
act -j <job-name>
```

### Run a specific workflow

```bash
act -W .github/workflows/ci.yml
```

### Dry run (see what would execute)

```bash
act -n
```

### Run with verbose output

```bash
act -j ci -v
```

### Run on specific event

```bash
# Simulate a push event
act push

# Simulate a pull request
act pull_request

# Simulate workflow_dispatch (manual trigger)
act workflow_dispatch
```

## Useful Options

- `-n, --dryrun` - Dry run mode (don't actually run)
- `-v, --verbose` - Verbose output
- `-l, --list` - List workflows
- `-j, --job` - Run a specific job
- `-W, --workflows` - Run a specific workflow file
- `--container-architecture` - Set container architecture (e.g., linux/amd64)
- `-P, --platform` - Set custom platform (e.g., ubuntu-latest=node:16-buster)

## Testing Strategy

### 1. **Quick validation** (fast, catches syntax errors)

```bash
act -n  # Dry run to validate workflow syntax
```

### 2. **Test individual jobs** (iterative development)

```bash
act -j get-python-version  # Test just the version extraction
act -j ci                   # Test just the CI job
```

### 3. **Full workflow test** (before pushing)

```bash
act -W .github/workflows/ci.yml
```

## Troubleshooting

### Docker not available in dev container

If running in a dev container, you may need to configure Docker-in-Docker or use the host Docker socket. The workflow will still validate syntax even without Docker.

### Large Docker images

`act` uses Docker images that can be large. Use smaller images for faster testing:

```bash
# Use medium image (faster)
act -P ubuntu-latest=catthehacker/ubuntu:act-latest

# Use micro image (fastest, but may miss some tools)
act -P ubuntu-latest=node:16-buster-slim
```

### Job dependencies

When testing jobs with dependencies (like our CI job depends on get-python-version), you may need to:

1. Test the dependency first: `act -j get-python-version`
2. Then test the dependent job: `act -j ci`
3. Or run the full workflow: `act -W .github/workflows/ci.yml`

## What Gets Tested Locally

✅ Workflow syntax and structure
✅ Job steps and commands
✅ Environment variables
✅ Conditional logic
✅ Script execution
✅ Tool installation

⚠️ **Note:** Some GitHub-specific features may not work exactly the same:

- GitHub API calls
- GitHub-hosted secrets (you can provide with `-s` flag)
- Some actions may behave differently
- Network-dependent steps may fail in isolated environments

## Best Practice Workflow

1. **Edit your workflow** in `.github/workflows/`
2. **Dry run** to check syntax: `act -n`
3. **Test specific job** you changed: `act -j <job-name>`
4. **Full workflow test**: `act -W .github/workflows/ci.yml`
5. **Push to GitHub** with confidence! 🚀

## Examples for This Project

```bash
# Test Python version extraction (fast)
act -j get-python-version

# Test CI without pushing (takes a few minutes)
act -W .github/workflows/ci.yml

# Test with verbose output for debugging
act -j ci -v

# See what would run without running it
act -n -W .github/workflows/ci.yml
```

## Resources

- [act Documentation](https://github.com/nektos/act)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
