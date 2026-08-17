import os
import tempfile

# Use a temporary on-disk SQLite database for the test suite so that the
# SQLAlchemy engine can be shared safely across threads (TestClient runs the
# ASGI app in a separate thread). The path is set before any `sentarr` module is
# imported because `sentarr.db` creates the engine at import time from
# `sentarr.config.settings`.
_fd, _test_db_path = tempfile.mkstemp(suffix=".db")
os.close(_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"

# Import the main application module first so that all SQLModel models are
# registered in SQLModel.metadata before creating the tables.
from sentarr import main  # noqa: E402, F401
from sentarr.db import init_db  # noqa: E402

init_db()
