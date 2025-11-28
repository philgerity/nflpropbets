import requests
from datetime import datetime
import dateutil.parser
import os

def sync_games(conn):
    # Check if using PostgreSQL or SQLite
    USE_POSTGRES = os.environ.get('DATABASE_URL') is not None
    placeholder = '%s' if USE_POSTGRES else '?'
    
    url = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    try:
        response = requests.get(url)
        data = response.json()
        
        cur = conn.cursor()
        
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
            cur.execute(f'SELECT id FROM games WHERE espn_id = {placeholder}', (espn_id,))
            row = cur.fetchone()
            
            if row:
                # Update
                cur.execute(f'''
                    UPDATE games 
                    SET status = {placeholder}, home_score = {placeholder}, away_score = {placeholder}, game_date = {placeholder}
                    WHERE espn_id = {placeholder}
                ''', (status, home_score, away_score, formatted_date, espn_id))
            else:
                # Insert
                cur.execute(f'''
                    INSERT INTO games (espn_id, home_team, away_team, game_date, status, home_score, away_score)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                ''', (espn_id, home_team, away_team, formatted_date, status, home_score, away_score))
        
        conn.commit()
        cur.close()
        return True, "Synced successfully"
    except Exception as e:
        return False, str(e)
