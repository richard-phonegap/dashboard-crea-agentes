from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Migration: Add skills column to agents table if it doesn't exist
        def run_migrations(connection):
            res = connection.execute(text("PRAGMA table_info(agents)"))
            columns = [row[1] for row in res]
            if "skills" not in columns:
                connection.execute(text("ALTER TABLE agents ADD COLUMN skills TEXT DEFAULT '[]'"))
            if "is_manager" not in columns:
                connection.execute(text("ALTER TABLE agents ADD COLUMN is_manager BOOLEAN DEFAULT 0"))
            if "task_description" not in columns:
                connection.execute(text("ALTER TABLE agents ADD COLUMN task_description TEXT"))
            if "task_expected_output" not in columns:
                connection.execute(text("ALTER TABLE agents ADD COLUMN task_expected_output TEXT"))
            
            # Migration: Add scheduling and publicity to crews table
            res = connection.execute(text("PRAGMA table_info(crews)"))
            crew_columns = [row[1] for row in res]
            if "schedule_type" not in crew_columns:
                connection.execute(text("ALTER TABLE crews ADD COLUMN schedule_type TEXT DEFAULT 'none'"))
            if "schedule_value" not in crew_columns:
                connection.execute(text("ALTER TABLE crews ADD COLUMN schedule_value TEXT"))
            if "is_public" not in crew_columns:
                connection.execute(text("ALTER TABLE crews ADD COLUMN is_public BOOLEAN DEFAULT 0"))
            if "output_email" not in crew_columns:
                connection.execute(text("ALTER TABLE crews ADD COLUMN output_email TEXT"))
            
            # Migration: Add api_key to llm_configs table
            res = connection.execute(text("PRAGMA table_info(llm_configs)"))
            llm_columns = [row[1] for row in res]
            if "api_key" not in llm_columns:
                connection.execute(text("ALTER TABLE llm_configs ADD COLUMN api_key TEXT"))
                
        await conn.run_sync(run_migrations)
