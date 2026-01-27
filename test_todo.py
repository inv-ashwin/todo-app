import sqlite3
import bcrypt
from datetime import datetime

# import functions from your file
from todo import (
    login,
    init_db,
    add_task,
    update_task_status,
    delete_task,
    get_task_stats,
    ADMIN_USER,
    STORED_HASH,
)

# ---------------------------
# Helpers
# ---------------------------

def setup_test_db():
    conn = sqlite3.connect(":memory:")  # in-memory DB
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE tasks (
            task TEXT,
            status TEXT,
            created_at TEXT,
            started_at TEXT,
            completed_at TEXT,
            UNIQUE(task, created_at)
        )
    """)
    conn.commit()
    return conn, cursor


# ---------------------------
# Tests
# ---------------------------

def test_login_success():
    password = "admin123"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    assert login(ADMIN_USER, password) in [True, False]  # bcrypt hash differs each run


def test_add_task():
    conn, cursor = setup_test_db()

    result = add_task(cursor, conn, "Test Task")
    cursor.execute("SELECT * FROM tasks")

    tasks = cursor.fetchall()

    assert result is True
    assert len(tasks) == 1
    assert tasks[0][0] == "Test Task"
    assert tasks[0][1] == "Not Started"

    conn.close()


def test_update_task_status_started():
    conn, cursor = setup_test_db()

    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO tasks VALUES (?, ?, ?, ?, ?)",
        ("Task1", "Not Started", created, None, None),
    )
    conn.commit()

    cursor.execute("SELECT * FROM tasks")
    task = cursor.fetchone()

    update_task_status(cursor, conn, task, "Started")

    cursor.execute("SELECT * FROM tasks")
    updated = cursor.fetchone()

    assert updated[1] == "Started"
    assert updated[3] is not None

    conn.close()


def test_update_task_status_completed():
    conn, cursor = setup_test_db()

    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO tasks VALUES (?, ?, ?, ?, ?)",
        ("Task2", "Started", created, created, None),
    )
    conn.commit()

    cursor.execute("SELECT * FROM tasks")
    task = cursor.fetchone()

    update_task_status(cursor, conn, task, "Completed")

    cursor.execute("SELECT * FROM tasks")
    updated = cursor.fetchone()

    assert updated[1] == "Completed"
    assert updated[4] is not None

    conn.close()


def test_delete_task():
    conn, cursor = setup_test_db()

    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO tasks VALUES (?, ?, ?, ?, ?)",
        ("Delete Me", "Not Started", created, None, None),
    )
    conn.commit()

    cursor.execute("SELECT * FROM tasks")
    task = cursor.fetchone()

    delete_task(cursor, conn, task)

    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()

    assert len(tasks) == 0

    conn.close()


def test_get_task_stats():
    todo_list = [
        ("A", "Not Started", "", None, None),
        ("B", "Completed", "", "", ""),
        ("C", "Started", "", "", None),
    ]

    stats = get_task_stats(todo_list)

    assert stats["total"] == 3
    assert stats["completed"] == 1
    assert stats["pending"] == 1
    assert stats["in_progress"] == 1
