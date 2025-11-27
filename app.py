from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from espn_sync import sync_games

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_for_simple_app')

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if DATABASE_URL:
        # Production: Use PostgreSQL
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = RealDictCursor
        return conn
    else:
        # Local development: Use SQLite
        conn = sqlite3.connect('prop_bets.db')
        conn.row_factory = sqlite3.Row
        return conn

@app.route('/')
def index():
    conn = get_db_connection()
    games = conn.execute('SELECT * FROM games ORDER BY game_date').fetchall()
    conn.close()
    
    # Group games by day of week
    from collections import defaultdict
    from datetime import datetime
    import dateutil.parser
    
    games_by_day = defaultdict(list)
    
    for game in games:
        # Parse the date to extract day of week
        # The game_date from ESPN is formatted like "Thu 8:20 PM"
        try:
            # Try to parse the date - we'll group by the day name prefix
            day_name = game['game_date'].split()[0]  # e.g., "Thu", "Sun"
            games_by_day[day_name].append(game)
        except:
            # If parsing fails, put in "Unknown" group
            games_by_day['Unknown'].append(game)
    
    # Define day order for sorting - Thu, Fri, Sun, Mon
    day_order = {'Thu': 1, 'Fri': 2, 'Sat': 3, 'Sun': 4, 'Mon': 5, 'Tue': 6, 'Wed': 7}
    
    # Sort the days
    sorted_days = sorted(games_by_day.keys(), key=lambda x: day_order.get(x, 99))
    
    return render_template('index.html', games_by_day=games_by_day, sorted_days=sorted_days)

@app.route('/sync')
def sync_route():
    conn = get_db_connection()
    success, msg = sync_games(conn)
    conn.close()
    if success:
        flash('Successfully synced with ESPN!')
    else:
        flash(f'Error syncing: {msg}')
    
    # Check if we should redirect back to a specific game
    redirect_game = request.args.get('redirect_game')
    if redirect_game:
        return redirect(url_for('game', game_id=redirect_game))
    return redirect(url_for('index'))

@app.route('/admin', methods=('GET', 'POST'))
def admin():
    conn = get_db_connection()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_prop':
            game_id = request.form['game_id']
            description = request.form['description']
            conn.execute('INSERT INTO props (game_id, description) VALUES (?, ?)',
                         (game_id, description))
            conn.commit()
            flash('Prop added!')

        elif action == 'resolve_prop':
            prop_id = request.form['prop_id']
            result = request.form['result']
            # If reset, set to NULL, otherwise set to Yes/No
            if result == 'Reset':
                conn.execute('UPDATE props SET result = NULL WHERE id = ?', (prop_id,))
                flash('Prop reset to pending!')
            else:
                conn.execute('UPDATE props SET result = ? WHERE id = ?', (result, prop_id))
                flash('Prop resolved!')
            conn.commit()
            
        elif action == 'edit_prop':
            prop_id = request.form['prop_id']
            description = request.form['description']
            conn.execute('UPDATE props SET description = ? WHERE id = ?', (description, prop_id))
            conn.commit()
            flash('Prop updated!')
            
        elif action == 'delete_prop':
            prop_id = request.form['prop_id']
            conn.execute('DELETE FROM props WHERE id = ?', (prop_id,))
            conn.commit()
            flash('Prop deleted!')
            
        elif action == 'delete_game':
             game_id = request.form['game_id']
             conn.execute('DELETE FROM games WHERE id = ?', (game_id,))
             conn.commit()
             flash('Game deleted')

    games = conn.execute('SELECT * FROM games ORDER BY game_date').fetchall()
    
    props = conn.execute('''
        SELECT props.id, props.description, props.result, games.home_team, games.away_team 
        FROM props 
        JOIN games ON props.game_id = games.id
        ORDER BY games.game_date
    ''').fetchall()
    
    # Group games by day of week (same logic as index)
    from collections import defaultdict
    games_by_day = defaultdict(list)
    
    for game in games:
        try:
            day_name = game['game_date'].split()[0]
            games_by_day[day_name].append(game)
        except:
            games_by_day['Unknown'].append(game)
    
    # Define day order - Thu, Fri, Sun, Mon
    day_order = {'Thu': 1, 'Fri': 2, 'Sat': 3, 'Sun': 4, 'Mon': 5, 'Tue': 6, 'Wed': 7}
    sorted_days = sorted(games_by_day.keys(), key=lambda x: day_order.get(x, 99))
    
    conn.close()
    return render_template('admin.html', games_by_day=games_by_day, sorted_days=sorted_days, props=props)

@app.route('/admin/users', methods=('GET', 'POST'))
def manage_users():
    conn = get_db_connection()
    
    if request.method == 'POST':
        if 'add_user' in request.form:
            name = request.form['name']
            if name:
                try:
                    conn.execute('INSERT INTO users (name) VALUES (?)', (name,))
                    conn.commit()
                    flash(f'User {name} added.')
                except sqlite3.IntegrityError:
                    flash('User already exists.')
        elif 'delete_user' in request.form:
            user_id = request.form['user_id']
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            flash('User deleted.')
            
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('users.html', users=users)

@app.route('/game/<int:game_id>')
def game(game_id):
    conn = get_db_connection()
    game = conn.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    props = conn.execute('SELECT * FROM props WHERE game_id = ?', (game_id,)).fetchall()
    users = conn.execute('SELECT * FROM users').fetchall()
    
    # Get bets for each prop with user information
    bets = conn.execute('''
        SELECT bets.prop_id, bets.selection, users.name
        FROM bets
        JOIN users ON bets.user_id = users.id
        WHERE bets.prop_id IN (SELECT id FROM props WHERE game_id = ?)
    ''', (game_id,)).fetchall()
    
    # Organize bets by prop_id
    bets_by_prop = {}
    for bet in bets:
        prop_id = bet['prop_id']
        if prop_id not in bets_by_prop:
            bets_by_prop[prop_id] = []
        bets_by_prop[prop_id].append({'name': bet['name'], 'selection': bet['selection']})
    
    conn.close()
    if game is None:
        return "Game not found", 404
    return render_template('game.html', game=game, props=props, users=users, bets_by_prop=bets_by_prop)

@app.route('/place_bet', methods=['POST'])
def place_bet():
    prop_id = request.form['prop_id']
    game_id = request.form['game_id']
    user_id = request.form['user_id']
    selection = request.form['selection']
    
    if not user_id:
        flash('Please select a user!')
        return redirect(url_for('game', game_id=game_id))

    conn = get_db_connection()
    
    # Check for existing bet
    existing_bet = conn.execute('SELECT * FROM bets WHERE prop_id = ? AND user_id = ?', (prop_id, user_id)).fetchone()
    
    if existing_bet:
        conn.execute('UPDATE bets SET selection = ? WHERE id = ?', (selection, existing_bet['id']))
        flash(f'Updated bet.')
    else:
        conn.execute('INSERT INTO bets (prop_id, user_id, selection) VALUES (?, ?, ?)',
                     (prop_id, user_id, selection))
        flash(f'Bet placed!')
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('game', game_id=game_id))

@app.route('/leaderboard')
def leaderboard():
    conn = get_db_connection()
    
    # Updated query to join users table
    results = conn.execute('''
        SELECT users.name, bets.selection, props.result
        FROM bets
        JOIN props ON bets.prop_id = props.id
        JOIN users ON bets.user_id = users.id
        WHERE props.result IS NOT NULL
    ''').fetchall()
    
    scores = {}
    total_bets = {}
    
    # Initialize all users with 0
    all_users = conn.execute('SELECT name FROM users').fetchall()
    for user_row in all_users:
        scores[user_row['name']] = 0
        total_bets[user_row['name']] = 0
    
    for row in results:
        user = row['name']
        total_bets[user] += 1
        if row['selection'] == row['result']:
            scores[user] += 1
            
    leaderboard_data = []
    
    for user, score in scores.items():
        total = total_bets[user]
        leaderboard_data.append({
            'name': user,
            'score': score,
            'total': total,
            'percentage': int((score / total) * 100) if total > 0 else 0
        })
    
    leaderboard_data.sort(key=lambda x: x['score'], reverse=True)
    
    conn.close()
    return render_template('leaderboard.html', leaderboard=leaderboard_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
