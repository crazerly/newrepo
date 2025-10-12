import sqlite3
import json
import time

def create_db():
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()

    # Create decks table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS decks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        parent_deck_id INTEGER,
        FOREIGN KEY (parent_deck_id) REFERENCES decks(id)
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS card_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fields TEXT NOT NULL,
        tags TEXT,
        modified_at INTEGER NOT NULL
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_type_id INTEGER,
        deck_id INTEGER,
        card_ord INTEGER,
        created_at INTEGER NOT NULL,
        next_due INTEGER,
        template_front TEXT,
        template_back TEXT,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (card_type_id) REFERENCES card_types(id),
        FOREIGN KEY (deck_id) REFERENCES decks(id)
    );
    ''')

    conn.commit()
    conn.close()

def add_deck(name, parent_deck_id=None):
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO decks (name, parent_deck_id)
    VALUES (?, ?)
    ''', (name, parent_deck_id))
    conn.commit()
    conn.close()

def add_card_type(fields_dict, tags=None):
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()

    fields_json = json.dumps(fields_dict)
    modified_at = int(time.time())

    cursor.execute('''
    INSERT INTO notes (fields, tags, modified_at)
    VALUES (?, ?, ?)
    ''', (fields_json, tags, modified_at))
    
    card_type_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return card_type_id

def add_card(card_type_id, deck_id, card_ord, template_front, template_back, next_due=None, is_active=True):
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()

    created_at = int(time.time())
    next_due = next_due or created_at + 86400  # default: due in 1 day

    cursor.execute('''
    INSERT INTO cards (
        card_type_id, deck_id, card_ord,
        created_at, next_due, template_front, template_back, is_active
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        card_type_id, deck_id, int(is_active), card_ord,
        created_at, next_due, template_front, template_back
    ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_db()