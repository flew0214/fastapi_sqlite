"""
Database migration script: Add channel and soft delete features
Columns added:
- messages.channel: Channel name (default "default")
- messages.is_deleted: Soft delete flag (default False)
"""

import sqlite3
import os

DB_FILE = "chat.db"

def migrate():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(messages)")
        columns = [row[1] for row in cursor.fetchall()]

        # Add channel column if not exists
        if 'channel' not in columns:
            print("Adding channel column...")
            cursor.execute("ALTER TABLE messages ADD COLUMN channel TEXT DEFAULT 'default'")
            print("[OK] channel column added")
        else:
            print("channel column already exists, skipping")

        # Add is_deleted column if not exists
        if 'is_deleted' not in columns:
            print("Adding is_deleted column...")
            cursor.execute("ALTER TABLE messages ADD COLUMN is_deleted BOOLEAN DEFAULT 0")
            print("[OK] is_deleted column added")
        else:
            print("is_deleted column already exists, skipping")

        # Set default values for existing records
        cursor.execute("UPDATE messages SET channel = 'default' WHERE channel IS NULL")
        print("[OK] Set default channel for existing records")

        conn.commit()
        print("\nMigration completed!")

        # Show updated table structure
        print("\nCurrent messages table structure:")
        cursor.execute("PRAGMA table_info(messages)")
        for row in cursor.fetchall():
            print(f"  {row[1]} ({row[2]})")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
