import requests
from datetime import datetime
import dateutil.parser

def sync_games(conn):
    url = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    try:
        response = requests.get(url)
        data = response.json()
        
        events = data.get('events', [])
        for event in events:
            competitions = event.get('competitions', [])[0]
            espn_id = event.get('id')
            date_str = event.get('date') # ISO format in UTC
            
            # Format date for display - convert to Eastern Time
            try:
                dt = dateutil.parser.parse(date_str)
                # Convert to Eastern Time
                from datetime import timezone, timedelta
                eastern = timezone(timedelta(hours=-5))  # EST (or -4 for EDT, but keeping simple)
                dt_eastern = dt.astimezone(eastern)
                formatted_date = dt_eastern.strftime("%a %I:%M %p")
            except:
                formatted_date = date_str

            status_type = event.get('status', {}).get('type', {})
            status = status_type.get('shortDetail') # e.g. "Final", "1st 10:00"
            
            competitors = competitions.get('competitors', [])
            home_team = "Unknown"
            away_team = "Unknown"
            home_score = 0
            away_score = 0
            
            for comp in competitors:
                team_name = comp.get('team', {}).get('displayName')
                score = int(comp.get('score', 0))
                if comp.get('homeAway') == 'home':
                    home_team = team_name
                    home_score = score
                else:
                    away_team = team_name
                    away_score = score
            
            # Check if game exists
            cur = conn.execute('SELECT id FROM games WHERE espn_id = ?', (espn_id,))
            row = cur.fetchone()
            
            if row:
                # Update
                conn.execute('''
                    UPDATE games 
                    SET status = ?, home_score = ?, away_score = ?, game_date = ?
                    WHERE espn_id = ?
                ''', (status, home_score, away_score, formatted_date, espn_id))
            else:
                # Insert
                conn.execute('''
                    INSERT INTO games (espn_id, home_team, away_team, game_date, status, home_score, away_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (espn_id, home_team, away_team, formatted_date, status, home_score, away_score))
        
        conn.commit()
        return True, "Synced successfully"
    except Exception as e:
        return False, str(e)
