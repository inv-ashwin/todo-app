import sqlite3
import csv
import os
from datetime import datetime
import getpass
import bcrypt
import sys
from dotenv import load_dotenv

load_dotenv() 

ADMIN_USER = os.getenv("ADMIN_USER")
PASSWORD = os.getenv("ADMIN_PASSWORD").encode() 



def init_db(db_name="todo.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks 
                   (task TEXT, status TEXT, created_at TEXT, started_at TEXT, completed_at TEXT,
                   UNIQUE(task, created_at))''')
    conn.commit()
    return conn, cursor

def login(u_input=None, p_input=None):
    if u_input is None:
        print("+------------------------------+")
        print("|            LOGIN             |")
        print("+------------------------------+")
        u_input = input("Username: ")
        p_input = getpass.getpass("Password: ")
    if u_input == ADMIN_USER:
        if bcrypt.checkpw(p_input.encode(), PASSWORD):
            return True
    return False

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_table(todo_list):
    if not todo_list:
        print("\n[!] No tasks found")
        return
    print("-" * 110)
    print("No".ljust(5), "Task".ljust(30), "Status".ljust(15), "Created At".ljust(20), "Duration")
    print("-" * 110)
    for i, item in enumerate(todo_list, start=1):
        duration = "-"
        if item[1] == "Completed" and item[3] and item[4]:
            start = datetime.strptime(item[3], "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(item[4], "%Y-%m-%d %H:%M:%S")
            duration = str(end - start).split(".")[0] 
        print(str(i).ljust(5), item[0][:28].ljust(30), item[1].ljust(15), item[2].ljust(20), duration)
    print("-" * 110)


def add_task(cursor, conn, task_name):

    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", (task_name, "Not Started", created, None, None))
    conn.commit()
    return True


def update_task_status(cursor, conn, task_data, new_status):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if new_status == "Started":
        cursor.execute("UPDATE tasks SET status='Started', started_at=? WHERE task=? AND created_at=?", 
                    (now, task_data[0], task_data[2]))
    elif new_status == "Completed":
        cursor.execute("UPDATE tasks SET status='Completed', completed_at=? WHERE task=? AND created_at=?", 
                    (now, task_data[0], task_data[2]))
    conn.commit()

def delete_task(cursor, conn, task_data):
    cursor.execute("DELETE FROM tasks WHERE task=? AND created_at=?", (task_data[0], task_data[2]))
    conn.commit()

def export_to_csv(todo_list, filename):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["task", "status", "created_at", "started_at", "completed_at"])
        writer.writerows(todo_list)

def import_from_csv(cursor, conn, filename):
    with open(filename, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("INSERT OR IGNORE INTO tasks VALUES (?, ?, ?, ?, ?)",
                        (row['task'], row['status'], row['created_at'], row['started_at'], row['completed_at']))
        conn.commit()

def handle_add_task(todo_list, cursor, conn):
    task = input("Enter task: ")
    if add_task(cursor, conn, task):
        print("Task Added")
    input("Press Enter...")
    clear_screen()

def handle_view_tasks(todo_list, *_):
    print("\n1.All\n2.Pending\n3.Completed\n4.In Progress")
    ch = int(input("Enter choice: "))

    if ch == 1:
        print_table(todo_list)
    elif ch == 2:
        print_table([t for t in todo_list if t[1] == "Not Started"])
    elif ch == 3:
        print_table([t for t in todo_list if t[1] == "Completed"])
    elif ch == 4:
        print_table([t for t in todo_list if t[1] == "Started"])

    input("Press Enter...")
    clear_screen()

def handle_mark_started(todo_list, cursor, conn):
    pending = [t for t in todo_list if t[1] == "Not Started"]

    for i, t in enumerate(pending, 1):
        print(f"{i}. {t[0]}")

    if pending:
        n = int(input("Number to start: "))
        update_task_status(cursor, conn, pending[n - 1], "Started")
        print("Task Started")

    input("Press Enter...")
    clear_screen()

def handle_mark_completed(todo_list, cursor, conn):
    started = [t for t in todo_list if t[1] == "Started"]

    for i, t in enumerate(started, 1):
        print(f"{i}. {t[0]}")

    if started:
        n = int(input("Number to complete: "))
        update_task_status(cursor, conn, started[n - 1], "Completed")
        print("Task Completed")

    input("Press Enter...")
    clear_screen()

def handle_delete_task(todo_list, cursor, conn):
    for i, t in enumerate(todo_list, 1):
        print(f"{i}. {t[0]}")

    if todo_list:
        n = int(input("Number to delete: "))
        delete_task(cursor, conn, todo_list[n - 1])

    clear_screen()

def handle_export_csv(todo_list, *_):
    path = input("Path (Enter for default): ").strip()
    filename = path if path else "todo_export.csv"
    export_to_csv(todo_list, filename)
    print(f"Exported to {filename}")
    input("Press Enter...")
    clear_screen()

def handle_import_csv(_, cursor, conn):
    path = input("Path (Enter for default): ").strip()
    filename = path if path else "todo_export.csv"

    if os.path.exists(filename):
        import_from_csv(cursor, conn, filename)
        print("Imported.")

    input("Press Enter...")
    clear_screen()

def get_task_stats(todo_list):
    return {
        "total": len(todo_list),
        "completed": sum(1 for t in todo_list if t[1] == "Completed"),
        "pending": sum(1 for t in todo_list if t[1] == "Not Started"),
        "in_progress": sum(1 for t in todo_list if t[1] == "Started"),
    }

def show_menu(stats):
    print(f"""
+------------------------------+
|         TASK MANAGER         |
+------------------------------+
| Total Tasks     : {stats['total']:<10} |
| Completed       : {stats['completed']:<10} |
| Pending         : {stats['pending']:<10} |
| In Progress     : {stats['in_progress']:<10} |
+------------------------------+
| 1. Add Task                  |
| 2. View Tasks                |
| 3. Mark Started              |
| 4. Mark Completed            |
| 5. Delete                    |
| 6. Export CSV                |
| 7. Import CSV                |
| 8. Logout                    |
+------------------------------+""")

# --- MAIN INTERFACE ---

def main():
    print()
    if not login():
        print("Invalid Credentials")
        sys.exit()

    clear_screen()
    print("Access Granted! Welcome,", ADMIN_USER)

    conn, cursor = init_db()

    actions = {
        1: handle_add_task,
        2: handle_view_tasks,
        3: handle_mark_started,
        4: handle_mark_completed,
        5: handle_delete_task,
        6: handle_export_csv,
        7: handle_import_csv,
    }

    while True:
        cursor.execute("SELECT * FROM tasks")
        todo_list = cursor.fetchall()

        stats = get_task_stats(todo_list)
        show_menu(stats)

        try:
            choice = int(input("Enter choice: "))
        except ValueError:
            continue

        if choice == 8:
            print("Goodbye!")
            break

        handler = actions.get(choice)
        if handler:
            handler(todo_list, cursor, conn)

    conn.close()


if __name__ == "__main__":
    main()