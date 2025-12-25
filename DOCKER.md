# Docker Usage Guide

This guide explains how to use Jira Time Machine with Docker.

## Quick Start

1. **Build and start the container:**
   ```bash
   docker compose up -d
   ```

2. **Run the example script:**
   ```bash
   docker compose exec jira-time-machine python examples/example.py
   ```

3. **Or access a Python shell:**
   ```bash
   docker compose exec jira-time-machine python
   ```

## Running with Your Jira Instance

To use the library with your own Jira instance, you'll need to provide credentials via environment variables:

```bash
docker compose run \
  -e JIRA_SERVER="https://your-instance.atlassian.net" \
  -e JIRA_EMAIL="your@email.com" \
  -e JIRA_API_TOKEN="your-api-token" \
  -e JIRA_PROJECT="YOUR_PROJECT" \
  jira-time-machine python examples/example.py
```

### Getting a Jira API Token

1. Log in to your Atlassian account
2. Go to https://id.atlassian.com/manage-profile/security/api-tokens
3. Click "Create API token"
4. Give it a name and copy the token

## Using the Library Interactively

Start an interactive Python shell:

```bash
docker compose exec jira-time-machine python
```

Then use the library:

```python
from jira import JIRA
from jira_time_machine import JiraTimeMachine

# Initialize JIRA
jira = JIRA(
    server='https://your-instance.atlassian.net',
    basic_auth=('your@email.com', 'your-api-token')
)

# Initialize JiraTimeMachine
jtm = JiraTimeMachine(jira)

# Get history
history = jtm.history("project = MYPROJECT", ["Status", "Assignee"])

# Get snapshot
snapshot = jtm.snapshot(history, pd.Timestamp('2024-01-01'))
```

## Development

For development, the current directory is mounted as a volume in the container. Any changes you make to the code will be reflected inside the container.

### Running Tests

```bash
docker compose exec jira-time-machine pytest
```

### Installing Additional Dependencies

```bash
docker compose exec jira-time-machine pip install <package-name>
```

## Output Files

Any files saved to `/app/output` inside the container will be available in the `./output` directory on your host machine.

## Stopping the Container

```bash
docker compose down
```

## Troubleshooting

### Container won't start
- Make sure Docker is running
- Check if port conflicts exist
- Try rebuilding: `docker compose build --no-cache`

### Permission issues with output files
- The output directory may need appropriate permissions
- Try: `chmod 777 output` (or adjust as needed for your security requirements)

### Connection issues to Jira
- Verify your API token is correct
- Check that your Jira server URL is correct
- Ensure your firewall allows outbound connections
