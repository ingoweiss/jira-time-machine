# Docker Setup for Jira Time Machine

This guide explains how to run the Jira Time Machine Dash application using Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) installed (usually included with Docker Desktop)
- Jira API credentials (email and API token)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ingoweiss/jira-time-machine.git
cd jira-time-machine
```

### 2. Configure Environment (Optional)

You can pre-configure your Jira credentials using environment variables:

```bash
cp .env.example .env
```

Edit `.env` and fill in your Jira credentials:

```env
JIRA_SERVER=https://your-company.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
```

**Note:** If you don't configure the `.env` file, you can enter your credentials through the web interface after starting the application.

### 3. Start the Application

```bash
docker-compose up -d
```

This command will:
- Build the Docker image (first time only)
- Start the application container
- Make the app available at http://localhost:8050

### 4. Access the Application

Open your web browser and navigate to:

```
http://localhost:8050
```

You should see the Jira Time Machine interface where you can:
- Enter your Jira credentials (if not configured via .env)
- Specify a JQL query to select issues
- Choose which fields to track
- View historical data and snapshots

## Usage

### Stopping the Application

```bash
docker-compose down
```

### Viewing Logs

```bash
docker-compose logs -f
```

### Rebuilding the Image

If you make changes to the application code:

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Running on a Different Port

Edit the `docker-compose.yml` file and change the port mapping:

```yaml
ports:
  - "8080:8050"  # Change 8080 to your desired port
```

Or set the PORT environment variable in your `.env` file (note: this changes the internal port, you'll also need to update the docker-compose.yml port mapping).

## Getting Your Jira API Token

1. Log in to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "Jira Time Machine")
4. Copy the generated token and use it in your `.env` file or the web interface

## Troubleshooting

### Container won't start

Check the logs:
```bash
docker-compose logs
```

### Port already in use

If port 8050 is already in use, change the port mapping in `docker-compose.yml`:
```yaml
ports:
  - "8051:8050"  # Use port 8051 instead
```

### Permission issues

On Linux, you may need to run Docker commands with `sudo` or add your user to the docker group:
```bash
sudo usermod -aG docker $USER
```
Then log out and log back in.

### Jira connection errors

- Verify your Jira server URL is correct (including https://)
- Ensure your API token is valid
- Check that your email is associated with your Jira account
- Verify network connectivity to your Jira instance

## Development

To run the application in development mode with auto-reload:

1. Edit `docker-compose.yml` and set:
   ```yaml
   environment:
     - DEBUG=true
   ```

2. Rebuild and restart:
   ```bash
   docker-compose up --build
   ```

## Security Notes

- Never commit your `.env` file with real credentials
- The `.env` file is already in `.gitignore` to prevent accidental commits
- API tokens should be treated as passwords
- Consider using Docker secrets for production deployments

## Support

For issues and questions:
- [GitHub Issues](https://github.com/ingoweiss/jira-time-machine/issues)
- [Project README](../README.md)
