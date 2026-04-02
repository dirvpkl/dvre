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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

log = logging.getLogger(__name__)


def main() -> None:
    """Run the DVRE server."""
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    log.info(f"Starting DVRE server on {host}:{port}")
    log.info("API documentation available at http://localhost:8000/docs")
    
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
