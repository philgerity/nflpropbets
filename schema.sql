DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS props;
DROP TABLE IF EXISTS bets;

CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    game_date TEXT NOT NULL,
    status TEXT DEFAULT 'Scheduled'
);

CREATE TABLE props (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    result TEXT, -- 'Yes', 'No', or NULL if pending
    FOREIGN KEY (game_id) REFERENCES games (id)
);

CREATE TABLE bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prop_id INTEGER NOT NULL,
    user_name TEXT NOT NULL,
    selection TEXT NOT NULL, -- 'Yes' or 'No'
    FOREIGN KEY (prop_id) REFERENCES props (id)
);
