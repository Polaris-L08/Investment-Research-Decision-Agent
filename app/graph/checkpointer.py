from pathlib import Path
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
CHECKPOINT_DB_PATH = DATA_DIR / "checkpoints.sqlite"


def create_checkpointer(
    db_path: str | Path = CHECKPOINT_DB_PATH,
) -> SqliteSaver:
    """Create a SQLite-backed LangGraph checkpointer.

    Persistence infrastructure is created explicitly by the runtime layer.
    Importing the application graph must not create directories, open database
    connections, or otherwise perform infrastructure side effects.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        path,
        check_same_thread=False,
    )

    return SqliteSaver(connection)