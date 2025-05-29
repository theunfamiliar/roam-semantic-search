# Roam Semantic Search

A FastAPI service for semantic search over Roam Research graphs.

## First Time Setup

First, check if your system is ready:

```bash
./scripts/setup.sh
```

This will:
- Check if Docker is installed and guide you through installation if needed
- Verify Docker is running
- Ensure Docker Compose is available

## Quick Start

Once setup is complete, run the service with:

```bash
./start.sh
```

This will start the service in development mode. The API will be available at http://localhost:8000

## Usage Options

```bash
./start.sh dev      # Development mode with visible logs (default)
./start.sh prod     # Production mode (detached)
./start.sh logs     # View logs
./start.sh rebuild  # Rebuild and restart containers

# Additional control commands:
./stop.sh          # Stop the service
./restart.sh       # Restart the service (supports same modes as start)
```

## Deployment

To deploy changes to the production server:

```bash
# Deploy with default commit message
./scripts/deploy.sh

# Or with custom commit message
./scripts/deploy.sh "Your commit message here"
```

This will:
1. Commit and push your changes to GitHub
2. Connect to the production server
3. Pull the latest changes
4. Rebuild and restart the Docker containers
5. Verify the service is running

## Docker Details

Under the hood, this uses Docker Compose for consistent environments. If you prefer, you can use docker compose commands directly:

```bash
docker compose up -d      # Run in detached mode
docker compose logs -f    # View logs
docker compose up --build # Rebuild and restart
```

## Development

If you want hot-reload during development, use:
```bash
docker compose up
```
(Remove the -d flag to see logs directly in your terminal)

## Local Development

```bash
# Setup
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.server:app --reload
```

## Useful Commands

```bash
# View logs
journalctl -u semantic-api.service -f

# Restart service
systemctl restart semantic-api.service

# Check status
systemctl status semantic-api.service
``` 