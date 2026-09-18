from sqlalchemy import inspect, text

from core.database import Base, engine
from models.research_project import ResearchProject
from models.user import User


def migrate_research_projects():
    inspector = inspect(engine)

    if "research_projects" not in inspector.get_table_names():
        return

    existing = {
        column["name"]
        for column in inspector.get_columns("research_projects")
    }

    additions = {
        "question_index": "INTEGER NOT NULL DEFAULT 0",
        "current_question": "TEXT",
        "answers": "JSON NOT NULL DEFAULT '[]'",
        "profile": "JSON NOT NULL DEFAULT '{}'",
        "research_plan": "JSON NOT NULL DEFAULT '{}'",
        "report": "TEXT",
        "sources": "JSON NOT NULL DEFAULT '[]'",
        "report_status": "VARCHAR NOT NULL DEFAULT 'not_started'",
        "messages": "JSON NOT NULL DEFAULT '[]'",
    }

    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(
                    text(
                        f"ALTER TABLE research_projects "
                        f"ADD COLUMN {name} {definition}"
                    )
                )


def main():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    migrate_research_projects()
    print("Database tables created/migrated successfully.")


if __name__ == "__main__":
    main()
