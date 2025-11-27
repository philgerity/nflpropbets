# NFL Prop Bets

A simple Flask application for managing and betting on NFL proposition bets.

## Features

- **Admin Interface**: Add games, add props to games, and resolve props.
- **User Interface**: View upcoming games and place bets on props.
- **Leaderboard**: View user rankings based on correct predictions.

## Prerequisites

- Python 3.x
- Flask

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    cd nflpropbets
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Initialize the database:
    ```bash
    python -c "from app import init_db; init_db()"
    ```
    *Note: You may need to add an `init_db` function to `app.py` or run the schema manually if it's not exposed.*
    
    Alternatively, you can manually initialize the database using sqlite3:
    ```bash
    sqlite3 prop_bets.db < schema.sql
    ```

## Usage

1.  Run the application:
    ```bash
    python app.py
    ```

2.  Open your browser and navigate to `http://localhost:5000`.

3.  **Admin Access**: Go to `http://localhost:5000/admin` to manage games and props.

## Project Structure

- `app.py`: Main Flask application file.
- `schema.sql`: Database schema.
- `requirements.txt`: Python dependencies.
- `templates/`: HTML templates for the application.
