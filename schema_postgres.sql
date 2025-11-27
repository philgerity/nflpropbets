-- PostgreSQL schema for NFL Prop Bets

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    game_date TEXT NOT NULL,
    status TEXT DEFAULT 'Scheduled',
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    espn_id TEXT UNIQUE,
    quarter TEXT,
    clock TEXT
);

CREATE TABLE IF NOT EXISTS props (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    result TEXT
);

CREATE TABLE IF NOT EXISTS bets (
    id SERIAL PRIMARY KEY,
    prop_id INTEGER NOT NULL REFERENCES props(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    selection TEXT NOT NULL CHECK(selection IN ('Yes', 'No')),
    UNIQUE(prop_id, user_id)
);
