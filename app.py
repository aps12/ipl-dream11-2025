from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ipl_betting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'some_secret_key'

db = SQLAlchemy(app)
ADMIN_PASSWORD = "k"

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_date = db.Column(db.Date)
    teams_playing = db.Column(db.String(255))
    
    rank_1st = db.Column(db.String(255))  # Store multiple teams as comma-separated values
    rank_2nd = db.Column(db.String(255))
    rank_3rd = db.Column(db.String(255))
    rank_4th = db.Column(db.String(255))


dream11_teams = [
    "APS Gladiators01", "KHAL-DROGO", "nMnF11", "Beind Baibhav",
    "Sanju Bawa XI", "11 SAFED TIGER", "HammerHeadsx1", "Shubham141193"
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


matches = [
    {"id": idx + 1, "match_date": date, "teams_playing": teams, "ranks": {1: [], 2: [], 3: [], 4: []}}
    for idx, (date, teams) in enumerate(ipl_schedule)
]

teams = [
    "APS Gladiators01", "KHAL-DROGO", "nMnF11", "Beind Baibhav",
    "Sanju Bawa XI", "11 SAFED TIGER", "HammerHeadsx1", "Shubham141193"
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
        ranked_teams = [match.rank_1st, match.rank_2nd, match.rank_3rd, match.rank_4th]
        
        if any(ranked_teams):  
            for team in dream11_teams:
                winnings[team]["Total Bet"] += bet_amount  

        for rank, team in zip(["Rank1", "Rank2", "Rank3", "Rank4"], ranked_teams):
            if team and team in winnings:
                winnings[team][rank] += 1  
                winnings[team]["Total Winnings"] += winnings_amount[rank]

    for team in winnings:
        winnings[team]["Net Winning"] = winnings[team]["Total Winnings"] - winnings[team]["Total Bet"]

    return winnings


@app.route('/')
def index():
    matches = Match.query.all()
    winnings = calculate_winnings()

    # Sort winnings dictionary by "Net Winning" in descending order
    sorted_winnings = dict(sorted(winnings.items(), key=lambda x: x[1]["Net Winning"], reverse=True))

    completed_matches = sum(1 for match in matches if match.rank_1st and match.rank_2nd and match.rank_3rd)
    pending_matches = len(matches) - completed_matches

    return render_template(
        'index.html',
        matches=matches,
        winnings=sorted_winnings,  # Now sorted
        completed_matches=completed_matches,
        pending_matches=pending_matches
    )



@app.route('/input', methods=['GET', 'POST'])
def input_page():
    try:
        # Get all matches for rendering
        matches = Match.query.order_by(Match.match_date).all()

        if request.method == 'POST':
            match_id = request.form.get('match_id')
            match = Match.query.get(match_id)

            if not match:
                flash("Match not found!", "danger")
                return redirect(url_for('input_page'))

            # Process ranks dynamically: Rank 1, 2, 3, 4
            for rank in [1, 2, 3, 4]:
                field_name = f"rank{rank}_{match_id}"
                selected_teams = request.form.getlist(field_name)

                # Dynamically generate rank field attribute name
                rank_field = f"rank_{rank}st"  # Use consistent suffix naming as per the database model
                if rank == 2:
                    rank_field = f"rank_{rank}nd"
                elif rank == 3:
                    rank_field = f"rank_{rank}rd"
                elif rank == 4:
                    rank_field = f"rank_{rank}th"

                # Update the field only if new values are provided
                if selected_teams:
                    setattr(match, rank_field, ','.join(selected_teams))

            # Commit changes to the database
            db.session.commit()
            flash(f"Rankings for Match {match_id} updated successfully!", "success")
            return redirect(url_for('input_page'))

        # Prepare matches for rendering
        match_data = [
            {
                "id": match.id,
                "match_date": match.match_date.strftime('%d %B %Y'),
                "teams_playing": match.teams_playing,
                "rank_1": match.rank_1st.split(',') if match.rank_1st else [],
                "rank_2": match.rank_2nd.split(',') if match.rank_2nd else [],
                "rank_3": match.rank_3rd.split(',') if match.rank_3rd else [],
                "rank_4": match.rank_4th.split(',') if match.rank_4th else [],
            }
            for match in matches
        ]

        return render_template("input.html", matches=match_data, teams=dream11_teams)

    except Exception as e:
        print(f"Error in `/input` route: {e}")
        return "An error occurred", 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)