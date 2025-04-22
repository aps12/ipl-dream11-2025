import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'k'  # Required for session management

# PostgreSQL Configuration
# app.config['SQLALCHEMY_DATABASE_URI'] = (
#     'postgresql://ipl_pg_db_user:ouTA3DieDxXwVMxg0VIfoRWMlwhZf8Gk'
#     '@dpg-cvh737jv2p9s7382os50-a.oregon-postgres.render.com/ipl_pg_db'
# )

app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql://neondb_owner:npg_6gywkml8XSri@ep-holy-wildflower-a54woyks-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require'
)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 280,
    'connect_args': {'sslmode': 'require'}
}

# app.config['SQLALCHEMY_DATABASE_URI'] = (
#     'sqlite:///ipl_db.sqlite'
# )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

PASSWORD  = 'k'  # Password for editing match rankings

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Model Definition
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_date = db.Column(db.Date)
    teams_playing = db.Column(db.String(255))
    rank_1st = db.Column(db.String(255))  # Store multiple teams as comma-separated values
    rank_2nd = db.Column(db.String(255))
    rank_3rd = db.Column(db.String(255))
    rank_4th = db.Column(db.String(255))


# Dream11 Teams and IPL Schedule
dream11_teams = [
    "APS Gladiators01", "Khal drogo 11", "nMnF11", "Beind Baibhav", "Sanju Bawa XI", "11 SAFED TIGER",
    "HammerHeadsx1", "Shubham141193", "DEXTER UK01", "Massey1099", "LOVEDI LADS", "SANDE39642AB",
    "Rahul Blazers XI", "PRAVEER1001", "Apoorva11"
]

ipl_schedule = [
    ("22 March 2025", "KKR vs RCB"), ("23 March 2025", "SRH vs RR"), ("23 March 2025", "MI vs CSK"),
    ("24 March 2025", "DC vs LSG"), ("25 March 2025", "GT vs PBKS"), ("26 March 2025", "RR vs KKR"),
    ("27 March 2025", "SRH vs LSG"), ("28 March 2025", "RCB vs CSK"), ("29 March 2025", "GT vs MI"),
    ("30 March 2025", "DC vs SRH"), ("30 March 2025", "RR vs CSK"), ("31 March 2025", "MI vs KKR"),
    ("1 April 2025", "LSG vs PBKS"), ("2 April 2025", "RCB vs GT"), ("3 April 2025", "KKR vs SRH"),
    ("4 April 2025", "LSG vs MI"), ("5 April 2025", "CSK vs DC"), ("5 April 2025", "PBKS vs RR"),
    ("6 April 2025", "KKR vs LSG"), ("6 April 2025", "SRH vs GT"), ("7 April 2025", "MI vs RCB"),
    ("8 April 2025", "PBKS vs CSK"), ("9 April 2025", "GT vs RR"), ("10 April 2025", "RCB vs DC"),
    ("11 April 2025", "CSK vs KKR"), ("12 April 2025", "LSG vs GT"), ("12 April 2025", "SRH vs PBKS"),
    ("13 April 2025", "RR vs RCB"), ("13 April 2025", "DC vs MI"), ("14 April 2025", "LSG vs CSK"),
    ("15 April 2025", "PBKS vs KKR"), ("16 April 2025", "DC vs RR"), ("17 April 2025", "MI vs SRH"),
    ("18 April 2025", "RR vs PBKS"), ("19 April 2025", "GT vs DC"), ("19 April 2025", "RR vs LSG"),
    ("20 April 2025", "PBKS vs RCB"), ("20 April 2025", "MI vs CSK"), ("21 April 2025", "KKR vs GT"),
    ("22 April 2025", "LSG vs DC"), ("23 April 2025", "SRH vs MI"), ("24 April 2025", "RCB vs RR"),
    ("25 April 2025", "CSK vs SRH"), ("26 April 2025", "KKR vs PBKS"), ("27 April 2025", "MI vs LSG"),
    ("27 April 2025", "DC vs RCB"), ("28 April 2025", "RR vs GT"), ("29 April 2025", "DC vs KKR"),
    ("30 April 2025", "CSK vs PBKS"), ("1 May 2025", "RR vs MI"), ("2 May 2025", "GT vs SRH"),
    ("3 May 2025", "RR vs CSK"), ("4 May 2025", "KKR vs RR"), ("4 May 2025", "PBKS vs CSK"),
    ("5 May 2025", "SRH vs DC"), ("6 May 2025", "MI vs GT"), ("7 May 2025", "KKR vs CSK"),
    ("8 May 2025", "PBKS vs DC"), ("9 May 2025", "LSG vs RCB"), ("10 May 2025", "SRH vs KKR"),
    ("11 May 2025", "PBKS vs MI"), ("11 May 2025", "DC vs GT"), ("12 May 2025", "CSK vs RR"),
    ("13 May 2025", "RCB vs SRH"), ("14 May 2025", "GT vs LSG"), ("15 May 2025", "MI vs DC"),
    ("16 May 2025", "RR vs PBKS"), ("17 May 2025", "RCB vs KKR"), ("18 May 2025", "GT vs CSK"),
    ("18 May 2025", "LSG vs SRH"), ("20 May 2025", "Qualifier 1"), ("21 May 2025", "Eliminator"),
    ("23 May 2025", "Qualifier 2"), ("25 May 2025", "Final")
]

# Ensure database and matches are created
with app.app_context():
    db.create_all()
    if Match.query.count() == 0:
        for date, teams in ipl_schedule:
            match = Match(match_date=datetime.strptime(date, "%d %B %Y").date(), teams_playing=teams)
            db.session.add(match)
        db.session.commit()

def calculate_winnings():
    winnings = {
        team: {"Rank1": 0, "Rank2": 0, "Rank3": 0, "Rank4": 0, 
               "Total Winnings": 0, "Total Bet": 0, "Net Winning": 0} 
        for team in dream11_teams
    }

    bet_amount = 50  
    winnings_amount = {"Rank1": 300, "Rank2": 200, "Rank3": 150, "Rank4": 100}

    matches = Match.query.all()
    
    for match in matches:
        # Get ranks, handling potential comma-separated values for ties
        rank_fields = [match.rank_1st, match.rank_2nd, match.rank_3rd, match.rank_4th]
        
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

@app.route('/')
def index():
    matches = Match.query.all()
    winnings = calculate_winnings()  # Calculate the winnings

    # Sort winnings and pass data to the Jinja2 template
    sorted_winnings = dict(sorted(winnings.items(), key=lambda x: x[1]["Net Winning"], reverse=True))

    completed_matches = sum(1 for match in matches if match.rank_1st and match.rank_2nd and match.rank_3rd and match.rank_4th)
    pending_matches = len(matches) - completed_matches

    return render_template(
        'index.html',
        matches=matches,
        winnings=sorted_winnings,  # Pass winnings to template
        completed_matches=completed_matches,
        pending_matches=pending_matches
    )


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
            
            # Handle different actions: edit, submit, cancel, submit_all
            if action.startswith('edit_'):
                # Set edit mode for this match
                match_id = action.split('_')[1]
                return redirect(url_for('input_page', edit=match_id))
                
            elif action.startswith('submit_') and action != 'submit_all':
                # Process and save the form data for a single match
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
                
            elif action == 'submit_all':
                # Get all matches that are editable (don't have rankings or are in edit mode)
                editable_matches = []
                edit_match_id = request.args.get('edit')
                
                for match in matches:
                    is_edit_mode = str(match.id) == edit_match_id if edit_match_id else False
                    
                    # Check if this match is editable (has no rankings or is in edit mode)
                    if not match.rank_1st or is_edit_mode:
                        editable_matches.append(match.id)
                
                # Process each editable match
                updated_matches = 0
                for match_id in editable_matches:
                    match = Match.query.get(match_id)
                    if not match:
                        continue
                    
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
                    
                    updated_matches += 1
                
                # Commit all changes to the database
                db.session.commit()
                
                if updated_matches > 0:
                    flash(f"Rankings for {updated_matches} matches updated successfully!", "success")
                else:
                    flash("No matches were updated.", "warning")
                    
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

        return render_template("input.html", matches=match_data, teams=dream11_teams)

    except Exception as e:
        print(f"Error in `/input` route: {e}")
        return "An error occurred", 500


@app.route("/match-rankings")
def match_rankings():
    # Get all matches with rankings
    matches = Match.query.filter(
        (Match.rank_1st.isnot(None) & (Match.rank_1st != '')) |
        (Match.rank_2nd.isnot(None) & (Match.rank_2nd != '')) |
        (Match.rank_3rd.isnot(None) & (Match.rank_3rd != '')) |
        (Match.rank_4th.isnot(None) & (Match.rank_4th != ''))
    ).order_by(Match.match_date).all()
    
    # Winnings amounts for each rank
    winnings_amount = {"Rank1": 300, "Rank2": 200, "Rank3": 150, "Rank4": 100}
    
    # Prepare data for template
    match_data = []
    
    for match in matches:
        # Get match details from IPL schedule
        match_date = ""
        match_name = ""
        
        # Try to match the match with the schedule list
        for schedule_date, schedule_match in ipl_schedule:
            if match.teams_playing == schedule_match and match.match_date == datetime.strptime(schedule_date, "%d %B %Y").date():
                match_date = schedule_date
                match_name = schedule_match
                break
        
        # Prepare match info
        match_info = {
            "id": match.id,
            "date": match_date,
            "name": match_name,
            "rankings": []
        }
        
        # Get ranks, handling potential comma-separated values for ties
        rank_fields = [
            {"name": "Rank 1", "teams": match.rank_1st, "amount": winnings_amount["Rank1"]},
            {"name": "Rank 2", "teams": match.rank_2nd, "amount": winnings_amount["Rank2"]},
            {"name": "Rank 3", "teams": match.rank_3rd, "amount": winnings_amount["Rank3"]},
            {"name": "Rank 4", "teams": match.rank_4th, "amount": winnings_amount["Rank4"]}
        ]
        
        # Process each rank (handling ties)
        skip_ranks = 0
        for rank_idx, rank in enumerate(rank_fields):
            if skip_ranks > 0:
                skip_ranks -= 1
                continue
                
            if not rank["teams"]:
                continue
                
            # Get all teams at this rank (handle ties)
            teams_at_rank = [team.strip() for team in rank["teams"].split(',') if team.strip()]
            
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
                        ranks_to_combine.append(rank_fields[rank_idx + i])
                
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
        
        # Only add match to data if it has rankings
        if match_info["rankings"]:
            match_data.append(match_info)
    
    return render_template("match_rankings.html", matches=match_data)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensure tables are created
    app.run(debug=True)
    # app.run(debug=True, host='127.0.0.1', port=5000)
