"""
DVRE - DaVinci Resolve Video Editor Server

Main entry point for running the DVRE server.
"""

import logging
import os

import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from dvre.utils.logger import setup_logging

setup_logging()
log = logging.getLogger(__name__)


def main() -> None:
    """Run the DVRE server."""
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    log.info(f"Starting DVRE server on {host}:{port}")
    log.info(f"API documentation available at http://{host}:{port}/docs")

    from dvre.server import create_app

    app = create_app()

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
