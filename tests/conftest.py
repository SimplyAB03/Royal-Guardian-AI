import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os

TEST_DB = Path(__file__).resolve().parent / "test.db"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["RG_DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["RG_SESSION_SECRET"] = "test-secret-not-for-production"
os.environ["RG_ENV"] = "test"
