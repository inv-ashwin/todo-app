import pytest
import sqlite3
import os
import csv
from datetime import datetime
from todo import (
    init_db, add_task, update_task_status, 
    delete_task, export_to_csv, import_from_csv, login
)


@pytest.fixture
def db():
    """Sets up an in-memory database for clean testing."""
    conn, cursor = init_db(":memory:")
    yield conn, cursor
    conn.close()

@pytest.fixture
def sample_task(db):
    """Adds a single task and returns its data."""
    conn, cursor = db
    add_task(cursor, conn, "Initial Task")
    cursor.execute("SELECT * FROM tasks")
    return cursor.fetchone()

# --- TEST CASES ---

## 1. Authentication Tests
def test_login_success():
    assert login("admin", "Inn0v@tur3") is True

def test_login_failure():
    assert login("admin", "wrong_password") is False
    assert login("hacker", "admin123") is False

## 2. Task Management Tests
def test_add_task(db):
    conn, cursor = db
    add_task(cursor, conn, "New Task")
    cursor.execute("SELECT task, status FROM tasks WHERE task='New Task'")
    row = cursor.fetchone()
    assert row is not None
    assert row[1] == "Not Started"

def test_update_to_started(db, sample_task):
    conn, cursor = db
    update_task_status(cursor, conn, sample_task, "Started")
    cursor.execute("SELECT status, started_at FROM tasks WHERE task='Initial Task'")
    row = cursor.fetchone()
    assert row[0] == "Started"
    assert row[1] is not None

def test_update_to_completed(db, sample_task):
    conn, cursor = db
    update_task_status(cursor, conn, sample_task, "Started")
    cursor.execute("SELECT * FROM tasks")
    current_data = cursor.fetchone()
    update_task_status(cursor, conn, current_data, "Completed")
    cursor.execute("SELECT status, completed_at FROM tasks WHERE task='Initial Task'")
    row = cursor.fetchone()
    assert row[0] == "Completed"
    assert row[1] is not None

def test_delete_task(db, sample_task):
    conn, cursor = db
    delete_task(cursor, conn, sample_task)
    cursor.execute("SELECT * FROM tasks")
    assert cursor.fetchone() is None

## 3. Edge Cases
def test_duplicate_task_error(db):
    conn, cursor = db
    add_task(cursor, conn, "Unique Task")
    cursor.execute("SELECT created_at FROM tasks")
    ts = cursor.fetchone()[0]
    
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", 
                       ("Unique Task", "Not Started", ts, None, None))

## 4. File I/O Tests
def test_csv_workflow(db, tmp_path):
    conn, cursor = db
    add_task(cursor, conn, "CSV Task")
    cursor.execute("SELECT * FROM tasks")
    data = cursor.fetchall()
    
    # Create temp path for CSV
    file_path = tmp_path / "test.csv"
    
    # Test Export
    export_to_csv(data, str(file_path))
    assert os.path.exists(file_path)
    
    # Test Import
    cursor.execute("DELETE FROM tasks") 
    import_from_csv(cursor, conn, str(file_path))
    cursor.execute("SELECT task FROM tasks")
    assert cursor.fetchone()[0] == "CSV Task"