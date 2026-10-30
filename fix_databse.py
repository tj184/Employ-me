
from sqlalchemy import create_engine, text
from config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

try:
    with engine.begin() as connection:
        connection.execute(text("""
            ALTER TABLE "user"
            ALTER COLUMN password_hash TYPE VARCHAR(256)
        """))

    print("Success! password_hash column is now VARCHAR(256).")

except Exception as e:
    print(f"Database update failed: {e}")

finally:
    engine.dispose()
