CREATE TABLE IF NOT EXISTS decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_deck_id INTEGER,
    FOREIGN KEY (parent_deck_id) REFERENCES decks(id)
);

CREATE TABLE IF NOT EXISTS card_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fields TEXT NOT NULL,
    tags TEXT,
    modified_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id INTEGER,
    FOREIGN KEY (note_id) REFERENCES notes(id),
    deck_id INTEGER,
    FOREIGN KEY (deck_id) REFERENCES deck(id),
    is_active BOOLEAN DEFAULT 1,
    card_ord INTEGER,
    created_at INTEGER NOT NULL,
    next_due INTEGER,
    template_front TEXT,
    template_back TEXT
);