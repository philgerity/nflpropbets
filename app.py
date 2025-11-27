from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_simple_app'
DB_NAME = 'prop_bets.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    games = conn.execute('SELECT * FROM games ORDER BY game_date').fetchall()
    conn.close()
    return render_template('index.html', games=games)

@app.route('/admin', methods=('GET', 'POST'))
def admin():
    conn = get_db_connection()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_game':
            home = request.form['home_team']
            away = request.form['away_team']
            date = request.form['game_date']
            conn.execute('INSERT INTO games (home_team, away_team, game_date) VALUES (?, ?, ?)',
                         (home, away, date))
            conn.commit()
            flash('Game added!')
            
        elif action == 'add_prop':
            game_id = request.form['game_id']
            description = request.form['description']
            conn.execute('INSERT INTO props (game_id, description) VALUES (?, ?)',
                         (game_id, description))
            conn.commit()
            flash('Prop added!')

        elif action == 'resolve_prop':
            prop_id = request.form['prop_id']
            result = request.form['result'] # 'Yes' or 'No'
            conn.execute('UPDATE props SET result = ? WHERE id = ?', (result, prop_id))
            conn.commit()
            flash('Prop resolved!')
            
        elif action == 'delete_game':
             game_id = request.form['game_id']
             conn.execute('DELETE FROM games WHERE id = ?', (game_id,))
             # Should probably cascade delete props and bets but keeping it simple
             conn.commit()
             flash('Game deleted')

    games = conn.execute('SELECT * FROM games ORDER BY game_date').fetchall()
    
    # Fetch props for all games to show in a resolution list
    # We join with games to show "Game: Prop Description"
    props = conn.execute('''
        SELECT props.id, props.description, props.result, games.home_team, games.away_team 
        FROM props 
        JOIN games ON props.game_id = games.id
        ORDER BY games.game_date
    ''').fetchall()
    
    conn.close()
    return render_template('admin.html', games=games, props=props)

@app.route('/game/<int:game_id>')
def game(game_id):
    conn = get_db_connection()
    game = conn.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    props = conn.execute('SELECT * FROM props WHERE game_id = ?', (game_id,)).fetchall()
    
    # We might want to see who bet what? Or just list props?
    # For simplicity, just list props and a form to bet.
    
    conn.close()
    if game is None:
        return "Game not found", 404
    return render_template('game.html', game=game, props=props)

@app.route('/place_bet', methods=['POST'])
def place_bet():
    prop_id = request.form['prop_id']
    game_id = request.form['game_id']
    user_name = request.form['user_name']
    selection = request.form['selection'] # 'Yes' or 'No'
    
    if not user_name:
        flash('Please enter your name!')
        return redirect(url_for('game', game_id=game_id))

    conn = get_db_connection()
    
    # Check if user already bet on this prop? Maybe. 
    # For now, let's just insert. If they bet twice, they bet twice. 
    # Or we can enforce one bet per user per prop.
    existing_bet = conn.execute('SELECT * FROM bets WHERE prop_id = ? AND user_name = ?', (prop_id, user_name)).fetchone()
    
    if existing_bet:
        conn.execute('UPDATE bets SET selection = ? WHERE id = ?', (selection, existing_bet['id']))
        flash(f'Updated bet for {user_name} on this prop.')
    else:
        conn.execute('INSERT INTO bets (prop_id, user_name, selection) VALUES (?, ?, ?)',
                     (prop_id, user_name, selection))
        flash(f'Bet placed for {user_name}!')
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('game', game_id=game_id))

@app.route('/leaderboard')
def leaderboard():
    conn = get_db_connection()
    
    # Get all bets joined with their prop result
    # We only care about resolved props
    results = conn.execute('''
        SELECT bets.user_name, bets.selection, props.result
        FROM bets
        JOIN props ON bets.prop_id = props.id
        WHERE props.result IS NOT NULL
    ''').fetchall()
    
    scores = {}
    total_bets = {}
    
    for row in results:
        user = row['user_name']
        if user not in scores:
            scores[user] = 0
            total_bets[user] = 0
        
        total_bets[user] += 1
        if row['selection'] == row['result']:
            scores[user] += 1
            
    # Convert to list for sorting
    leaderboard_data = []
    # Include users who have placed bets but maybe none resolved yet? 
    # The query above only gets resolved ones. 
    # Let's do a separate query to find all unique users if we want to show 0-0 records.
    # For now, sticking to the query above is simple enough.
    
    for user, score in scores.items():
        leaderboard_data.append({
            'name': user,
            'score': score,
            'total': total_bets[user],
            'percentage': int((score / total_bets[user]) * 100) if total_bets[user] > 0 else 0
        })
    
    leaderboard_data.sort(key=lambda x: x['score'], reverse=True)
    
    conn.close()
    return render_template('leaderboard.html', leaderboard=leaderboard_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
