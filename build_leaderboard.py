import json
from datetime import datetime
from pathlib import Path
import sqlite3

DB_PATH = "data.db"
OUTPUT_FILE = "leaderboard.json"

def upsert_user_score(name, score, ts):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO users (name, current_score, max_score, last_updated)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                current_score = excluded.current_score,
                max_score = MAX(users.max_score, excluded.current_score),
                last_updated = excluded.last_updated;
        """, (name, score, score, ts))
        conn.commit()

def get_score_list():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT name, current_score, last_updated, max_score
            FROM users
            ORDER BY current_score DESC
        """)
        rows = cur.fetchall()

    # hübsch aufbereiten
    return [
        {
            "student": name,
            "avg_return": score,
            "timestamp": datetime.fromtimestamp(ts),
            "max_score": max_score
        }
        for name, score, ts, max_score in rows
    ]


if __name__ == "__main__":
    folder_path = "/out"
    folder = Path(folder_path)

    entries = []

    for file in folder.glob("*.py"):
        repo_name = file.stem
        result = json.loads(file)

        # Compute average over all average_return values
        if result:
            avg_return = sum(p["average_return"] for p in result) / len(result)
        else:
            avg_return = 0.0

        student_name = repo_name.rsplit("-", 1)[-1]

        entries.append({
            "student_name": student_name,
            "avg_return": avg_return,
        })
    
    for e in entries: 
        upsert_user_score(e["student_name"], e["avg_return"], datetime.now())
        print(f"upserted student: {e["student_name"]}")

    entries = get_score_list()

    # sort by score descending
    entries.sort(key=lambda e: (-e["avg_return"], e["student"]))

    with open(OUTPUT_FILE, "w") as f:
        json.dump(
            {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "entries": entries,
            },
            f,
            indent=2,
        )

    print(f"Wrote {OUTPUT_FILE}")