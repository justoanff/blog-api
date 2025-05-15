from sqlmodel import create_engine, SQLModel as SQLModelBase, Session

from app.config.settings import get_settings

engine = create_engine(
    str(get_settings().DATABASE_URL),
    echo=True,
)

def create_db_and_tables():
    print("Creating tables...")
    try:
        from app.models.user_model import User
        from app.models.post_model import Post
        print("Model imported")
    except ImportError as e:
        print(f"Error importing models: {e}")
    print("Creating database tables if not exists...")
    SQLModelBase.metadata.create_all(engine)
    print("Database tables created")

def get_session():
    with Session(engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        