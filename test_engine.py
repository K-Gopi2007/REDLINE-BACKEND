import sys
from app.core.config import settings

# Override the url for testing
settings.DATABASE_URL = "postgresql://redline_db_si09_user:fake_password@dpg-dar4m9s9v7es739fp3o0-a/redline_db_si09"

from sqlalchemy import create_engine
print("Testing URL:", settings.sync_database_url)

try:
    engine = create_engine(settings.sync_database_url)
    print("Engine created successfully with dialect:", engine.dialect.name, "and driver:", engine.dialect.driver)
except Exception as e:
    print("Error:", e)
    sys.exit(1)
