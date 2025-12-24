import sqlite3

db_path= "data.db"


def create_user(name):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            INSERT INTO users (name)
            VALUES (?)
            ON CONFLICT(name) DO NOTHING;
        """, (name,))
        conn.commit()

if __name__ == "__main__":
    student_name = "LDarg"
    create_user(student_name,)
    print(f"Created {student_name}")
