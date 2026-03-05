#!/usr/bin/env python3
"""Development server with advanced file watching using watchfiles.

This provides better file watching than uvicorn's --reload flag:
- Faster detection of changes
- More reliable reloads
- Better handling of file system events
- Support for watching specific directories
"""

import asyncio
import os
import signal
import sys
from pathlib import Path

from watchfiles import awatch
from uvicorn import Config, Server


def run_server():
    """Run the FastAPI server with watchfiles monitoring."""
    # Get the app directory
    app_dir = Path(__file__).parent / "app"

    # Configure uvicorn
    config = Config(
        app="app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,  # We'll handle reloading with watchfiles
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )

    server = Server(config)

    # Watch these directories for changes
    watch_dirs = [
        str(app_dir),  # Main app code
        "pyproject.toml",  # Dependencies
        "requirements.txt",  # Alternative dependencies
    ]

    # File patterns to watch (Python files, config files)
    watch_patterns = [
        "*.py",
        "*.toml",
        "*.txt",
        "*.yaml",
        "*.yml",
    ]

    print("🚀 Starting RAG Assistant API with advanced file watching...")
    print(f"📁 Watching directories: {', '.join(watch_dirs)}")
    print(f"📄 Watching patterns: {', '.join(watch_patterns)}")
    print("🔄 Server will auto-reload on file changes")
    print(f"🌐 Server will be available at: http://{config.host}:{config.port}")
    print("📊 API docs at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")

    # Set up signal handling for graceful shutdown
    def signal_handler(signum, frame):
        print("\n👋 Shutting down server...")
        server.should_exit = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    async def run_with_watch():
        """Run server with file watching."""
        # Start the server in a task
        server_task = asyncio.create_task(server.serve())

        # Watch for file changes
        async def watch_files():
            async for changes in awatch(
                *watch_dirs,
                watch_filter=lambda change, path: any(
                    path.endswith(ext) for ext in [".py", ".toml", ".txt", ".yaml", ".yml"]
                )
                if change[0].name in ("modified", "created", "deleted")
                else False,
                debounce=300,  # Wait 300ms after change before reload
                step=50,  # Check for changes every 50ms
            ):
                print(f"🔄 Detected changes in {len(changes)} files, restarting server...")
                server.should_exit = True
                break

        # Run both tasks concurrently
        await asyncio.gather(server_task, watch_files())

    try:
        asyncio.run(run_with_watch())
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
        server.should_exit = True
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_server()
