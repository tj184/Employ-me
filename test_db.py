from sqlalchemy import create_engine, text
from config import Config

try:
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), current_user")
        )

        database, user = result.fetchone()

        print("PostgreSQL connection successful!")
        print("Database:", database)
        print("User:", user)

except Exception as e:
    print("Database connection failed!")
    print("Error:", e)