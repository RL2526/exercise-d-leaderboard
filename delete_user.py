import sqlite3

db_path= "data.db"

def delete_user(name):
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
            DELETE FROM users
            WHERE name = ?;
        """, (name,))
        conn.commit()
        return cur.rowcount  
    

if __name__ == "__main__":
    student_name = "mzeimet"
    delete_user(student_name,)
    print(f"Deleted {student_name}")