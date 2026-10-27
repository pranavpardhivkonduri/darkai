from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Build engine with SQLite-specific pragmas for WAL mode and FK enforcement
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    poolclass=StaticPool if settings.DATABASE_URL.startswith("sqlite") else None,
    echo=settings.DEBUG,
)

if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and seed default data."""
    from app.models import user_models, analysis_models, audit_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    _seed_default_users()


def _seed_default_users():
    """Seed demo admin, analyst and normal user if they don't exist."""
    from app.models.user_models import User, Role
    from app.auth.security import get_password_hash
    db = SessionLocal()
    try:
        if db.query(User).first():
            return  # already seeded

        users_to_seed = [
            {
                "username": "admin",
                "email": "admin@darkai.local",
                "full_name": "DarkAI Administrator",
                "role": Role.ADMIN,
                "password": "Admin@1234",
            },
            {
                "username": "analyst",
                "email": "analyst@darkai.local",
                "full_name": "Security Analyst",
                "role": Role.ANALYST,
                "password": "Analyst@1234",
            },
            {
                "username": "user",
                "email": "user@darkai.local",
                "full_name": "Normal User",
                "role": Role.USER,
                "password": "User@1234",
            },
        ]

        for u in users_to_seed:
            db_user = User(
                username=u["username"],
                email=u["email"],
                full_name=u["full_name"],
                role=u["role"],
                hashed_password=get_password_hash(u["password"]),
                is_active=True,
                mfa_enabled=False,
            )
            db.add(db_user)
        db.commit()
        logger.info("Demo users seeded: admin / analyst / user")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding users: {e}")
    finally:
        db.close()
