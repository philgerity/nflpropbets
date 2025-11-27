DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS props;
DROP TABLE IF EXISTS bets;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    espn_id TEXT UNIQUE,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    game_date TEXT NOT NULL,
    status TEXT DEFAULT 'Scheduled',
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    quarter TEXT,
    clock TEXT
);

CREATE TABLE props (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    result TEXT, -- 'Yes', 'No', or NULL if pending
    FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE
);

CREATE TABLE bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prop_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    selection TEXT NOT NULL, -- 'Yes' or 'No'
    FOREIGN KEY (prop_id) REFERENCES props (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE(prop_id, user_id) -- Prevent duplicate bets on same prop
);
