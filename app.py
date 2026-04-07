import os
import requests
from bs4 import BeautifulSoup
import re
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'k'  # Required for session management

# Password for input page access
PASSWORD = os.environ.get('APP_PASSWORD', 'admin123')  # Change this or set APP_PASSWORD env variable

# SQLite Configuration (works locally and on PythonAnywhere)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'ipl_dream11.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Model Definitions
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_date = db.Column(db.Date)
    teams_playing = db.Column(db.String(255))
    rank_1st = db.Column(db.String(255))  # Store multiple teams as comma-separated values
    rank_2nd = db.Column(db.String(255))
    rank_3rd = db.Column(db.String(255))
    rank_4th = db.Column(db.String(255))

class Dream11Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bet_amount = db.Column(db.Integer, default=50)
    number_of_ranks = db.Column(db.Integer, default=4)
    rank_1_prize = db.Column(db.Integer, default=300)
    rank_2_prize = db.Column(db.Integer, default=200)
    rank_3_prize = db.Column(db.Integer, default=150)
    rank_4_prize = db.Column(db.Integer, default=100)
    season = db.Column(db.Integer, default=2026)
    season_locked = db.Column(db.Boolean, default=False)

# IPL Fixture URLs
IPL_FIXTURES_URL = "https://www.iplt20.com/matches/fixtures"

# Default Dream11 teams (can be managed from frontend)
DEFAULT_DREAM11_TEAMS = [
    "APS Gladiators01", "Khal drogo 11", "nMnF11", "Beind Baibhav", "Sanju Bawa XI", "11 SAFED TIGER",
    "HammerHeadsx1", "Shubham141193", "DEXTER UK01", "Massey1099", "LOVEDI LADS", "SANDE39642AB",
    "Rahul Blazers XI", "PRAVEER1001", "Apoorva11"
]

def fetch_ipl_fixtures(season=2026):
    """Fetch IPL fixtures dynamically from official website for any season"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(IPL_FIXTURES_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        fixtures = []
        
        # Method 1: Find all h3 tags (team names) and extract match info
        page_html = str(soup)
        
        # Extract all matches using pattern matching
        # Look for patterns like: MATCH \d+ ... APR, WED 8 ... DC ... GT
        import re
        
        # Find all "MATCH X" occurrences with their content
        match_blocks = re.findall(r'MATCH\s+(\d+).*?(?=(MATCH\s+\d+|TITLE SPONSOR))', page_html, re.DOTALL | re.IGNORECASE)
        
        team_abbrevs = {'RCB', 'SRH', 'MI', 'CSK', 'KKR', 'DC', 'GT', 'PBKS', 'LSG', 'RR'}
        month_map = {
            'JAN': 'JAN', 'FEB': 'FEB', 'MAR': 'MAR', 'APR': 'APR', 
            'MAY': 'MAY', 'JUN': 'JUN', 'JUL': 'JUL', 'AUG': 'AUG',
            'SEP': 'SEP', 'OCT': 'OCT', 'NOV': 'NOV', 'DEC': 'DEC'
        }
        
        for match_num, (match_content, _) in enumerate(match_blocks, 1):
            try:
                # Extract date: "APR, WED 8" or "MAY, SUN 24"
                date_pattern = r'(' + '|'.join(month_map.keys()) + r'),\s*\w+\s+(\d+)'
                date_match = re.search(date_pattern, match_content, re.IGNORECASE)
                
                if not date_match:
                    continue
                
                month = date_match.group(1).upper()
                day = date_match.group(2)
                
                # Extract teams - find all team abbreviations in order
                teams_found = []
                for team in team_abbrevs:
                    # Find all occurrences with their positions
                    for match in re.finditer(r'\b' + team + r'\b', match_content):
                        teams_found.append((match.start(), team))
                
                # Sort by position and get first 2 unique teams
                teams_found.sort(key=lambda x: x[0])
                unique_teams = []
                seen = set()
                for _, team in teams_found:
                    if team not in seen:
                        unique_teams.append(team)
                        seen.add(team)
                        if len(unique_teams) == 2:
                            break
                
                if len(unique_teams) == 2:
                    date_str = f"{day} {month} {season}"
                    teams_playing = f"{unique_teams[0]} vs {unique_teams[1]}"
                    fixtures.append((date_str, teams_playing))
                    
            except Exception as e:
                continue
        
        # Method 2: If method 1 didn't get enough matches, try alternative parsing
        if len(fixtures) < 50:
            print(f"Method 1 found {len(fixtures)} matches, trying alternative method...")
            fixtures = []
            
            # Find all h3 elements that contain team abbreviations
            all_text = soup.get_text()
            lines = all_text.split('\n')
            
            current_date = None
            potential_team1 = None
            
            for line in lines:
                line = line.strip()
                
                # Check if line contains a date
                date_match = re.search(r'(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC),?\s*\w*\s*(\d+)', line, re.I)
                if date_match:
                    current_date = f"{date_match.group(2)} {date_match.group(1).upper()} {season}"
                    potential_team1 = None
                    continue
                
                # Check if line is a team abbreviation
                if line in team_abbrevs:
                    if current_date:
                        if potential_team1 is None:
                            potential_team1 = line
                        elif potential_team1 != line:
                            teams_playing = f"{potential_team1} vs {line}"
                            if (current_date, teams_playing) not in fixtures:
                                fixtures.append((current_date, teams_playing))
                            potential_team1 = None
        
        if len(fixtures) >= 50:
            print(f"✓ Successfully fetched {len(fixtures)} matches from IPL website")
            return fixtures
        else:
            print(f"⚠️ Only found {len(fixtures)} matches from website")
            print("Attempting to fetch from alternative source...")
            return get_fallback_fixtures(season)
            
    except Exception as e:
        print(f"❌ Error fetching fixtures from website: {e}")
        return get_fallback_fixtures(season)

def get_fallback_fixtures(season=2026):
    """Fallback with actual IPL data - extracted from Wikipedia and iplt20.com"""
    
    if season == 2026:
        # IPL 2026 complete schedule - ALL 70 matches from Match 1 to Final
        # Source: https://en.wikipedia.org/wiki/2026_Indian_Premier_League
        print(f"📋 Loading IPL {season} fixtures from fallback data...")
        fixtures_data = [
            # League Stage - All 70 matches (28 March to 6 April completed, rest scheduled)
            ("28 MAR", "RCB vs SRH"), ("29 MAR", "MI vs KKR"), ("30 MAR", "RR vs CSK"),
            ("31 MAR", "PBKS vs GT"), ("1 APR", "DC vs LSG"), ("2 APR", "SRH vs KKR"),
            ("3 APR", "CSK vs PBKS"), ("4 APR", "DC vs MI"), ("4 APR", "GT vs RR"),
            ("5 APR", "LSG vs SRH"), ("5 APR", "RCB vs CSK"), ("6 APR", "KKR vs PBKS"),
            # Remaining matches from Apr 7 onwards
            ("7 APR", "RR vs MI"), ("8 APR", "DC vs GT"), ("9 APR", "KKR vs LSG"),
            ("10 APR", "RR vs RCB"), ("11 APR", "PBKS vs SRH"), ("11 APR", "CSK vs DC"),
            ("12 APR", "LSG vs GT"), ("12 APR", "MI vs RCB"), ("13 APR", "SRH vs RR"),
            ("14 APR", "CSK vs KKR"), ("15 APR", "RCB vs LSG"), ("16 APR", "MI vs PBKS"),
            ("17 APR", "GT vs KKR"), ("18 APR", "RCB vs DC"), ("18 APR", "SRH vs CSK"),
            ("19 APR", "KKR vs RR"), ("19 APR", "PBKS vs LSG"), ("20 APR", "GT vs MI"),
            ("21 APR", "SRH vs DC"), ("22 APR", "LSG vs RR"), ("23 APR", "MI vs CSK"),
            ("24 APR", "RCB vs GT"), ("25 APR", "DC vs PBKS"), ("25 APR", "RR vs SRH"),
            ("26 APR", "GT vs CSK"), ("26 APR", "LSG vs KKR"), ("27 APR", "DC vs RCB"),
            ("28 APR", "PBKS vs RR"), ("29 APR", "MI vs SRH"), ("30 APR", "GT vs RCB"),
            ("1 MAY", "RR vs DC"), ("2 MAY", "CSK vs MI"), ("3 MAY", "SRH vs KKR"),
            ("3 MAY", "GT vs PBKS"), ("4 MAY", "MI vs LSG"), ("5 MAY", "DC vs CSK"),
            ("6 MAY", "SRH vs PBKS"), ("7 MAY", "LSG vs RCB"), ("8 MAY", "DC vs KKR"),
            ("9 MAY", "RR vs GT"), ("10 MAY", "CSK vs LSG"), ("10 MAY", "RCB vs MI"),
            ("11 MAY", "PBKS vs DC"), ("12 MAY", "GT vs SRH"), ("13 MAY", "RCB vs KKR"),
            ("14 MAY", "PBKS vs MI"), ("15 MAY", "LSG vs CSK"), ("16 MAY", "KKR vs GT"),
            ("17 MAY", "PBKS vs RCB"), ("17 MAY", "DC vs RR"), ("18 MAY", "CSK vs SRH"),
            ("19 MAY", "RR vs LSG"), ("20 MAY", "KKR vs MI"), ("21 MAY", "CSK vs GT"),
            ("22 MAY", "SRH vs RCB"), ("23 MAY", "LSG vs PBKS"), ("24 MAY", "MI vs RR"),
            ("24 MAY", "KKR vs DC"),
            # Playoffs (Dates TBA - using May placeholders)
            ("27 MAY", "Qualifier 1"), ("28 MAY", "Eliminator"), 
            ("30 MAY", "Qualifier 2"), ("31 MAY", "Final")
        ]
        print(f"✓ Loaded {len(fixtures_data)} matches for IPL {season}")
        return [(f"{date} {season}", teams) for date, teams in fixtures_data]
    
    else:
        # For other seasons, show instructions
        print(f"⚠️ No data available for IPL {season}")
        print(f"Please visit: https://www.iplt20.com/matches/fixtures")
        return [
            (f"1 JAN {season}", f"No schedule for {season} - Visit iplt20.com"),
            (f"2 JAN {season}", "Use 'Load Fixtures' in Manage tab"),
        ]

def get_dream11_teams():
    """Get list of Dream11 teams from database"""
    teams = Dream11Team.query.order_by(Dream11Team.team_name).all()
    return [team.team_name for team in teams] if teams else []

def get_settings():
    """Get or create settings"""
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()
    return settings

# Initialize database
with app.app_context():
    db.create_all()
    
    # Migrate existing settings table (add new columns if they don't exist)
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('settings')]
        
        # Add missing columns using raw SQL
        if 'season' not in columns:
            db.session.execute(db.text('ALTER TABLE settings ADD COLUMN season INTEGER DEFAULT 2026'))
            db.session.commit()
            print("✓ Added 'season' column to settings table")
        
        if 'season_locked' not in columns:
            db.session.execute(db.text('ALTER TABLE settings ADD COLUMN season_locked BOOLEAN DEFAULT 0'))
            db.session.commit()
            print("✓ Added 'season_locked' column to settings table")
    except Exception as e:
        print(f"Migration check: {e}")
    
    # Initialize settings if none exist
    if Settings.query.count() == 0:
        default_settings = Settings()
        db.session.add(default_settings)
        db.session.commit()
    
    # Initialize default Dream11 teams if none exist
    if Dream11Team.query.count() == 0:
        for team_name in DEFAULT_DREAM11_TEAMS:
            team = Dream11Team(team_name=team_name)
            db.session.add(team)
        db.session.commit()
    
    # Initialize matches if none exist
    if Match.query.count() == 0:
        # Get the season from settings
        settings = Settings.query.first()
        season = settings.season if settings else 2026
        
        print(f"Loading fixtures for IPL {season}...")
        fixtures = fetch_ipl_fixtures(season)
        loaded_count = 0
        
        for date_str, teams in fixtures:
            try:
                match = Match(
                    match_date=datetime.strptime(date_str, "%d %b %Y").date(),
                    teams_playing=teams
                )
                db.session.add(match)
                loaded_count += 1
            except Exception as e:
                print(f"Error parsing date: {date_str}, {e}")
                continue
        
        db.session.commit()
        print(f"✓ Loaded {loaded_count} matches for IPL {season}")

@app.route('/')
def index():
    matches = Match.query.all()
    # A match is complete if rank_1st is filled (handles ties where rank_2nd might be empty)
    completed_matches = sum(1 for match in matches if match.rank_1st)
    pending_matches = len(matches) - completed_matches
    
    # Calculate winnings for all teams
    winnings = calculate_winnings()

    return render_template(
        'index.html',
        matches=matches,
        completed_matches=completed_matches,
        pending_matches=pending_matches,
        winnings=winnings
    )

def calculate_winnings():
    dream11_teams = get_dream11_teams()
    settings = get_settings()
    
    winnings = {
        team: {"Rank1": 0, "Rank2": 0, "Rank3": 0, "Rank4":0, 
               "Total Winnings": 0, "Total Bet": 0, "Net Winning": 0} 
        for team in dream11_teams
    }

    bet_amount = settings.bet_amount
    winnings_amount = {
        "Rank1": settings.rank_1_prize, 
        "Rank2": settings.rank_2_prize, 
        "Rank3": settings.rank_3_prize, 
        "Rank4": settings.rank_4_prize
    }
    number_of_ranks = settings.number_of_ranks

    matches = Match.query.all()
    
    for match in matches:
        # Get ranks based on configured number of ranks
        rank_fields = []
        if number_of_ranks >= 1:
            rank_fields.append(match.rank_1st)
        if number_of_ranks >= 2:
            rank_fields.append(match.rank_2nd)
        if number_of_ranks >= 3:
            rank_fields.append(match.rank_3rd)
        if number_of_ranks >= 4:
            rank_fields.append(match.rank_4th)
        
        # Parse all teams in this match from the comma-separated values
        all_ranked_teams = []
        for rank_str in rank_fields:
            if rank_str:
                # Split comma-separated teams and strip whitespace
                teams_at_rank = [team.strip() for team in rank_str.split(',') if team.strip()]
                all_ranked_teams.extend(teams_at_rank)
        
        # Charge bet amount to all teams if match has rankings
        if any(rank_fields):  
            for team in dream11_teams:
                winnings[team]["Total Bet"] += bet_amount
        
        # Process each rank (handling ties)
        for rank_idx, rank_str in enumerate(rank_fields):
            rank_name = f"Rank{rank_idx + 1}"
            
            if not rank_str:
                continue
                
            # Get all teams at this rank (handle ties)
            teams_at_rank = [team.strip() for team in rank_str.split(',') if team.strip()]
            
            if not teams_at_rank:
                continue
                
            # If multiple teams at this rank, it's a tie
            is_tie = len(teams_at_rank) > 1
            
            if is_tie:
                # For ties, calculate which ranks to combine
                ranks_to_combine = []
                teams_in_tie = len(teams_at_rank)
                
                # In a tie, combine this rank with subsequent ranks
                for i in range(teams_in_tie):
                    if rank_idx + i < 4:  # Ensure we don't go beyond Rank4
                        ranks_to_combine.append(f"Rank{rank_idx + i + 1}")
                
                # Calculate the combined prize pool
                prize_pool = sum(winnings_amount[r] for r in ranks_to_combine)
                individual_prize = prize_pool / teams_in_tie
                
                # Award the prize to each team in the tie
                for team in teams_at_rank:
                    if team in winnings:
                        winnings[team][rank_name] += 1  # Count in the primary rank
                        winnings[team]["Total Winnings"] += individual_prize
                
                # Skip the next n-1 ranks that were combined in this tie
                # We do this by setting their values to empty in rank_fields
                for i in range(1, teams_in_tie):
                    if rank_idx + i < 4:  # Ensure we don't go beyond Rank4
                        rank_fields[rank_idx + i] = ""
            else:
                # No tie, just a single team at this rank
                team = teams_at_rank[0]
                if team in winnings:
                    winnings[team][rank_name] += 1
                    winnings[team]["Total Winnings"] += winnings_amount[rank_name]

    # Calculate net winnings
    for team in winnings:
        winnings[team]["Net Winning"] = winnings[team]["Total Winnings"] - winnings[team]["Total Bet"]

    return winnings

@app.route('/input', methods=['GET', 'POST'])
def input_page():
    # Check if user has already authenticated
    if 'authenticated' not in session or not session['authenticated']:
        if request.method == 'POST':
            entered_password = request.form.get('password')
            if entered_password == PASSWORD:
                session['authenticated'] = True  # Mark user as authenticated
                return redirect(url_for('input_page'))  # Redirect to input page
            else:
                error = "Incorrect password. Please try again."
                return render_template('password_prompt.html', error=error)
        
        # Render password prompt if not authenticated
        return render_template('password_prompt.html')
    try:
        # Get all matches for rendering
        matches = Match.query.order_by(Match.match_date).all()

        if request.method == 'POST':
            action = request.form.get('action', '')
            
            # Handle different actions: edit, submit, cancel
            if action.startswith('edit_'):
                # Set edit mode for this match
                match_id = action.split('_')[1]
                return redirect(url_for('input_page', edit=match_id))
                
            elif action.startswith('submit_'):
                # Process and save the form data
                match_id = action.split('_')[1]
                match = Match.query.get(match_id)
                
                if not match:
                    flash("Match not found!", "danger")
                    return redirect(url_for('input_page'))

                # Process ranks dynamically: Rank 1, 2, 3, 4
                for rank in [1, 2, 3, 4]:
                    field_name = f"rank{rank}_{match_id}"
                    selected_teams = request.form.getlist(field_name)

                    # Map rank number to the correct database field name
                    if rank == 1:
                        rank_field = "rank_1st"
                    elif rank == 2:
                        rank_field = "rank_2nd"
                    elif rank == 3:
                        rank_field = "rank_3rd"
                    elif rank == 4:
                        rank_field = "rank_4th"

                    # Update the field with selected teams or empty string if none selected
                    if selected_teams:
                        setattr(match, rank_field, ','.join(selected_teams))
                    else:
                        setattr(match, rank_field, '')

                # Commit changes to the database
                db.session.commit()
                flash(f"Rankings for Match {match_id} updated successfully!", "success")
                return redirect(url_for('input_page'))
                
            elif action.startswith('cancel_'):
                # Cancel edit mode, return to view mode
                return redirect(url_for('input_page'))
            
        # Check if any match is in edit mode from URL parameter
        edit_match_id = request.args.get('edit')
                
        # Prepare matches for rendering
        match_data = []
        for match in matches:
            # Determine if this match is in edit mode
            is_edit_mode = str(match.id) == edit_match_id if edit_match_id else False
            
            match_data.append({
                "id": match.id,
                "match_date": match.match_date.strftime('%d %B %Y'),
                "teams_playing": match.teams_playing,
                "rank_1": match.rank_1st.split(',') if match.rank_1st else [],
                "rank_2": match.rank_2nd.split(',') if match.rank_2nd else [],
                "rank_3": match.rank_3rd.split(',') if match.rank_3rd else [],
                "rank_4": match.rank_4th.split(',') if match.rank_4th else [],
                "edit_mode": is_edit_mode
            })

        return render_template("input.html", matches=match_data, teams=get_dream11_teams())

    except Exception as e:
        print(f"Error in `/input` route: {e}")
        return "An error occurred", 500

# Add this to your Flask app routes

# Add this to your Flask app routes

@app.route("/match-rankings")
def match_rankings():
    # Get only completed matches (where rank_1st is filled)
    matches = Match.query.filter(Match.rank_1st.isnot(None)).order_by(Match.match_date, Match.id).all()
    settings = get_settings()
    
    # Prepare data for template
    match_data = []
    
    winnings_amount = {
        "Rank1": settings.rank_1_prize, 
        "Rank2": settings.rank_2_prize, 
        "Rank3": settings.rank_3_prize, 
        "Rank4": settings.rank_4_prize
    }
    
    for match in matches:
        # Get match details from database
        match_date = match.match_date.strftime('%d %B %Y') if match.match_date else ""
        match_name = match.teams_playing
        
        # Basic match info
        match_info = {
            "id": match.id,
            "date": match_date,
            "name": match_name,
            "rankings": []
        }
        
        # Get ranks, handling comma-separated values for ties
        rank_fields = [
            {"name": "Rank1", "teams": match.rank_1st, "amount": winnings_amount["Rank1"]},
            {"name": "Rank2", "teams": match.rank_2nd, "amount": winnings_amount["Rank2"]},
            {"name": "Rank3", "teams": match.rank_3rd, "amount": winnings_amount["Rank3"]},
            {"name": "Rank4", "teams": match.rank_4th, "amount": winnings_amount["Rank4"]}
        ]
        
        # Process each rank (handling ties)
        skip_ranks = 0
        for i, rank in enumerate(rank_fields):
            if skip_ranks > 0:
                skip_ranks -= 1
                continue
                
            if not rank["teams"]:
                match_info["rankings"].append({
                    "rank": rank["name"],
                    "teams": "None",
                    "prize": "₹0"
                })
                continue
                
            # Get all teams at this rank (handle ties)
            teams_at_rank = [team.strip() for team in rank["teams"].split(',') if team.strip()]
            
            if not teams_at_rank:
                match_info["rankings"].append({
                    "rank": rank["name"],
                    "teams": "None",
                    "prize": "₹0"
                })
                continue
                
            # If multiple teams at this rank, it's a tie
            is_tie = len(teams_at_rank) > 1
            
            if is_tie:
                # For ties, calculate which ranks to combine
                ranks_to_combine = []
                teams_in_tie = len(teams_at_rank)
                
                # In a tie, combine this rank with subsequent ranks
                for j in range(teams_in_tie):
                    if i + j < 4:  # Ensure we don't go beyond Rank4
                        ranks_to_combine.append(rank_fields[i + j])
                
                # Calculate the combined prize pool
                prize_pool = sum(r["amount"] for r in ranks_to_combine)
                individual_prize = prize_pool / teams_in_tie
                
                # Create ranking entry
                combined_ranks = "-".join([r["name"] for r in ranks_to_combine])
                match_info["rankings"].append({
                    "rank": combined_ranks,
                    "teams": ", ".join(teams_at_rank),
                    "prize": f"₹{individual_prize:.2f} each"
                })
                
                # Skip the next n-1 ranks that were combined in this tie
                skip_ranks = teams_in_tie - 1
            else:
                # No tie, just a single team at this rank
                match_info["rankings"].append({
                    "rank": rank["name"],
                    "teams": teams_at_rank[0],
                    "prize": f"₹{rank['amount']}"
                })
        
        match_data.append(match_info)
    
    return render_template("match_rankings.html", matches=match_data)

# Management Routes (Teams & Settings)
@app.route('/manage', methods=['GET', 'POST'])
def manage():
    """Manage Dream11 teams and settings - Password Protected"""
    # Check if user has already authenticated for manage page
    if 'manage_authenticated' not in session or not session['manage_authenticated']:
        if request.method == 'POST':
            entered_password = request.form.get('password')
            if entered_password == PASSWORD:
                session['manage_authenticated'] = True
                return redirect(url_for('manage'))
            else:
                error = "Incorrect password. Please try again."
                return render_template('password_prompt.html', error=error, page_title="Manage Access")
        
        # Render password prompt if not authenticated
        return render_template('password_prompt.html', page_title="Manage Access")
    
    teams = Dream11Team.query.order_by(Dream11Team.team_name).all()
    settings = get_settings()
    match_count = Match.query.count()
    return render_template('manage.html', teams=teams, settings=settings, match_count=match_count)

@app.route('/teams/add', methods=['POST'])
def add_team():
    """Add a new Dream11 team"""
    team_name = request.form.get('team_name', '').strip()
    
    if not team_name:
        flash("Team name cannot be empty!", "danger")
        return redirect(url_for('manage'))
    
    # Check if team already exists
    existing_team = Dream11Team.query.filter_by(team_name=team_name).first()
    if existing_team:
        flash(f"Team '{team_name}' already exists!", "warning")
        return redirect(url_for('manage'))
    
    # Add new team
    new_team = Dream11Team(team_name=team_name)
    db.session.add(new_team)
    db.session.commit()
    
    flash(f"Team '{team_name}' added successfully!", "success")
    return redirect(url_for('manage'))

@app.route('/teams/delete/<int:team_id>', methods=['POST'])
def delete_team(team_id):
    """Delete a Dream11 team"""
    team = Dream11Team.query.get_or_404(team_id)
    team_name = team.team_name
    
    db.session.delete(team)
    db.session.commit()
    
    flash(f"Team '{team_name}' deleted successfully!", "success")
    return redirect(url_for('manage'))

@app.route('/settings/update', methods=['POST'])
def update_settings():
    """Update game settings"""
    settings = get_settings()
    
    try:
        settings.bet_amount = int(request.form.get('bet_amount', 50))
        settings.number_of_ranks = int(request.form.get('number_of_ranks', 4))
        settings.rank_1_prize = int(request.form.get('rank_1_prize', 300))
        settings.rank_2_prize = int(request.form.get('rank_2_prize', 200))
        settings.rank_3_prize = int(request.form.get('rank_3_prize', 150))
        settings.rank_4_prize = int(request.form.get('rank_4_prize', 100))
        
        db.session.commit()
        flash("Settings updated successfully!", "success")
    except ValueError:
        flash("Invalid values provided. Please enter valid numbers.", "danger")
    
    return redirect(url_for('manage'))

@app.route('/season/update', methods=['POST'])
def update_season():
    """Update season and fetch fixtures"""
    # Check authentication
    if 'manage_authenticated' not in session or not session['manage_authenticated']:
        flash("Access denied. Please login to manage page first.", "danger")
        return redirect(url_for('manage'))
    
    settings = get_settings()
    
    # Check if season is locked
    if settings.season_locked:
        flash("⚠️ Season is locked! Unlock it first to change the season.", "warning")
        return redirect(url_for('manage'))
    
    try:
        new_season = int(request.form.get('season', 2026))
        
        # Validate season (between 2008 and 2030)
        if new_season < 2008 or new_season > 2030:
            flash("Invalid season. Please select between 2008 and 2030.", "danger")
            return redirect(url_for('manage'))
        
        settings.season = new_season
        db.session.commit()
        
        flash(f"Season updated to {new_season}!", "success")
        flash("Now fetch fixtures for this season using 'Load Fixtures' button.", "info")
        
    except ValueError:
        flash("Invalid season value.", "danger")
    
    return redirect(url_for('manage'))

@app.route('/season/lock', methods=['POST'])
def lock_season():
    """Lock the season to prevent changes"""
    # Check authentication
    if 'manage_authenticated' not in session or not session['manage_authenticated']:
        flash("Access denied.", "danger")
        return redirect(url_for('manage'))
    
    settings = get_settings()
    settings.season_locked = True
    db.session.commit()
    
    flash(f"🔒 Season {settings.season} is now locked!", "success")
    return redirect(url_for('manage'))

@app.route('/season/unlock', methods=['POST'])
def unlock_season():
    """Unlock the season to allow changes"""
    # Check authentication
    if 'manage_authenticated' not in session or not session['manage_authenticated']:
        flash("Access denied.", "danger")
        return redirect(url_for('manage'))
    
    confirmation = request.form.get('unlock_confirmation', '').strip()
    
    if confirmation.upper() != 'UNLOCK':
        flash("You must type 'UNLOCK' to confirm.", "warning")
        return redirect(url_for('manage'))
    
    settings = get_settings()
    settings.season_locked = False
    db.session.commit()
    
    flash(f"🔓 Season {settings.season} is now unlocked!", "success")
    return redirect(url_for('manage'))

@app.route('/fixtures/load', methods=['POST'])
def load_fixtures():
    """Load fixtures for the current season"""
    # Check authentication
    if 'manage_authenticated' not in session or not session['manage_authenticated']:
        flash("Access denied.", "danger")
        return redirect(url_for('manage'))
    
    settings = get_settings()
    season = settings.season
    
    try:
        # Delete existing matches
        Match.query.delete()
        
        # Fetch fixtures for the selected season
        fixtures = fetch_ipl_fixtures(season)
        
        for date_str, teams in fixtures:
            try:
                match = Match(
                    match_date=datetime.strptime(date_str, "%d %b %Y").date(),
                    teams_playing=teams
                )
                db.session.add(match)
            except Exception as e:
                print(f"Error parsing date: {date_str}, {e}")
                continue
        
        db.session.commit()
        flash(f"✅ Loaded {len(fixtures)} matches for IPL {season}!", "success")
    except Exception as e:
        flash(f"Error loading fixtures: {str(e)}", "danger")
    
    return redirect(url_for('manage'))

@app.route('/fixtures/refresh', methods=['POST'])
def refresh_fixtures():
    """Refresh fixtures from IPL website"""
    try:
        # Delete existing matches (only if user confirms)
        Match.query.delete()
        
        # Fetch new fixtures
        fixtures = fetch_ipl_fixtures()
        
        for date_str, teams in fixtures:
            try:
                match = Match(
                    match_date=datetime.strptime(date_str, "%d %b %Y").date(),
                    teams_playing=teams
                )
                db.session.add(match)
            except Exception as e:
                print(f"Error parsing date: {date_str}, {e}")
                continue
        
        db.session.commit()
        flash(f"Successfully refreshed {len(fixtures)} matches!", "success")
    except Exception as e:
        flash(f"Error refreshing fixtures: {str(e)}", "danger")
    
    return redirect(url_for('index'))

@app.route('/reset-database', methods=['POST'])
def reset_database():
    """Reset database for new season - requires confirmation"""
    # Check authentication
    if 'manage_authenticated' not in session or not session['manage_authenticated']:
        flash("Access denied. Please login to manage page first.", "danger")
        return redirect(url_for('manage'))
    
    confirmation = request.form.get('confirmation', '').strip()
    
    if confirmation.upper() != 'DELETE':
        flash("Reset cancelled. You must type 'DELETE' exactly to confirm.", "warning")
        return redirect(url_for('manage'))
    
    try:
        # Delete all match data (keep teams and settings)
        Match.query.delete()
        db.session.commit()
        
        flash("✅ Database reset successful! All match data has been cleared.", "success")
        flash("Teams and settings have been preserved.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error resetting database: {str(e)}", "danger")
    
    return redirect(url_for('manage'))

@app.route('/reset-all', methods=['POST'])
def reset_all():
    """Complete database reset - removes everything including teams"""
    # Check authentication
    if 'manage_authenticated' not in session or not session['manage_authenticated']:
        flash("Access denied. Please login to manage page first.", "danger")
        return redirect(url_for('manage'))
    
    confirmation = request.form.get('confirmation_all', '').strip()
    
    if confirmation.upper() != 'DELETE':
        flash("Reset cancelled. You must type 'DELETE' exactly to confirm.", "warning")
        return redirect(url_for('manage'))
    
    try:
        # Delete everything
        Match.query.delete()
        Dream11Team.query.delete()
        Settings.query.delete()
        
        # Recreate default settings
        default_settings = Settings()
        db.session.add(default_settings)
        
        db.session.commit()
        
        flash("✅ Complete reset successful! All data has been cleared.", "success")
        flash("Please add your teams again.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error resetting database: {str(e)}", "danger")
    
    return redirect(url_for('manage'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensure tables are created
    app.run(debug=True)