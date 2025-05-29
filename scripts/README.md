# Scripts Directory

This directory contains utility scripts for development, deployment, and maintenance.

## Overview

- `deploy.sh` - Deploy changes to production server
- `setup.sh` - First-time setup and dependency checks
- `setup_logs.sh` - Create log directories with proper permissions
- `verify_search_response.py` - Health check for search endpoint

## Usage

Most scripts can be run directly:

```bash
./scripts/deploy.sh
./scripts/setup.sh
```

## Development

The main application entry point is `app/server.py`. These scripts are supplementary tools for data processing and maintenance. 