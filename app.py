from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ipl_betting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'some_secret_key'
ADMIN_PASSWORD = "k"
db = SQLAlchemy(app)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_date = db.Column(db.String(50))
    teams_playing = db.Column(db.String(100))
    rank_1st = db.Column(db.String(50), nullable=True)
    rank_2nd = db.Column(db.String(50), nullable=True)
    rank_3rd = db.Column(db.String(50), nullable=True)
    common_rank = db.Column(db.String(10), nullable=True)
    common_rank_team = db.Column(db.String(50), nullable=True)



dream11_teams = [
    "APS Gladiators01", "Khal drogo 11", "nMnF11", "Beind Baibhav", "Sanju Bawa XI", "11 SAFED TIGER",
    "HammerHeadsx1", "Shubham141193", "DEXTER UK01", "Massey1099", "LOVEDI LADS", "SANDE39642AB", 
    "Rahul Blazers XI", "PRAVEER1001", "Apoorva11"
]

ipl_schedule = [
    ("22nd March", "KKR vs RCB"), ("23rd March", "SRH vs RR"), ("23rd March", "MI vs CSK"),
    ("24th March", "DC vs LSG"), ("25th March", "GT vs PBKS"), ("26th March", "RR vs KKR"),
    ("27th March", "SRH vs LSG"), ("28th March", "RCB vs CSK"), ("29th March", "GT vs MI"),
    ("30th March", "DC vs SRH"), ("30th March", "RR vs CSK"), ("31st March", "MI vs KKR"),
    ("1st April", "LSG vs PBKS"), ("2nd April", "RCB vs GT"), ("3rd April", "KKR vs SRH"),
    ("4th April", "LSG vs MI"), ("5th April", "CSK vs DC"), ("5th April", "PBKS vs RR"),
    ("6th April", "KKR vs LSG"), ("6th April", "SRH vs GT"), ("7th April", "MI vs RCB"),
    ("8th April", "PBKS vs CSK"), ("9th April", "GT vs RR"), ("10th April", "RCB vs DC"),
    ("11th April", "CSK vs KKR"), ("12th April", "LSG vs GT"), ("12th April", "SRH vs PBKS"),
    ("13th April", "RR vs RCB"), ("13th April", "DC vs MI"), ("14th April", "LSG vs CSK"),
    ("15th April", "PBKS vs KKR"), ("16th April", "DC vs RR"), ("17th April", "MI vs SRH"),
    ("18th April", "RR vs PBKS"), ("19th April", "GT vs DC"), ("19th April", "RR vs LSG"),
    ("20th April", "PBKS vs RCB"), ("20th April", "MI vs CSK"), ("21st April", "KKR vs GT"),
    ("22nd April", "LSG vs DC"), ("23rd April", "SRH vs MI"), ("24th April", "RCB vs RR"),
    ("25th April", "CSK vs SRH"), ("26th April", "KKR vs PBKS"), ("27th April", "MI vs LSG"),
    ("27th April", "DC vs RCB"), ("28th April", "RR vs GT"), ("29th April", "DC vs KKR"),
    ("30th April", "CSK vs PBKS"), ("1st May", "RR vs MI"), ("2nd May", "GT vs SRH"),
    ("3rd May", "RR vs CSK"), ("4th May", "KKR vs RR"), ("4th May", "PBKS vs CSK"),
    ("5th May", "SRH vs DC"), ("6th May", "MI vs GT"), ("7th May", "KKR vs CSK"),
    ("8th May", "PBKS vs DC"), ("9th May", "LSG vs RCB"), ("10th May", "SRH vs KKR"),
    ("11th May", "PBKS vs MI"), ("11th May", "DC vs GT"), ("12th May", "CSK vs RR"),
    ("13th May", "RCB vs SRH"), ("14th May", "GT vs LSG"), ("15th May", "MI vs DC"),
    ("16th May", "RR vs PBKS"), ("17th May", "RCB vs KKR"), ("18th May", "GT vs CSK"),
    ("18th May", "LSG vs SRH"), ("20th May 2025", "Qualifier 1"), ("21st May 2025", "Eliminator"),
    ("23rd May 2025", "Qualifier 2"), ("25th May 2025", "Final")
]

with app.app_context():
    db.create_all()
    if Match.query.count() == 0:
        for date, teams in ipl_schedule:
            match = Match(match_date=date, teams_playing=teams)
            db.session.add(match)
        db.session.commit()

def calculate_winnings():
    winnings = {team: {"Rank1": 0, "Rank2": 0, "Rank3": 0, "Total Winnings": 0, "Total Bet": 0, "Net Winning": 0} for team in dream11_teams}
    bet_amount = 50
    winnings_amount = {"Rank1": 300, "Rank2": 200, "Rank3": 100}

    matches = Match.query.all()

    for match in matches:
        if match.rank_1st and match.rank_2nd and match.rank_3rd:
            for team in dream11_teams:
                winnings[team]["Total Bet"] += bet_amount  # Add bet amount for all teams

        for rank, team in zip(["Rank1", "Rank2", "Rank3"], [match.rank_1st, match.rank_2nd, match.rank_3rd]):
            if team and team in winnings:
                winnings[team][rank] += 1  # Increase rank count
                winnings[team]["Total Winnings"] += winnings_amount[rank]  # Add full winnings initially

                # If there's a Common Rank and it's different from the current ranked team
                if match.common_rank_team and match.common_rank_team in winnings and match.common_rank_team != team:
                    split_winnings = winnings_amount[rank] // 2  # Divide winnings into half

                    # Reduce the original team's winnings by half
                    winnings[team]["Total Winnings"] -= split_winnings
                    
                    # Add the split winnings to the common rank team
                    winnings[match.common_rank_team]["Total Winnings"] += split_winnings

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


@app.route("/input", methods=["GET", "POST"])
def input_page():
    if request.method == "POST":
        entered_password = request.form.get("password_submit", "").strip()
        match_id = request.form.get("match_id")  # Get match ID if updating a single row

        if entered_password != ADMIN_PASSWORD:
            flash("Incorrect password!", "error")
            return redirect(url_for("input_page"))

        errors = 0  # Counter for incomplete rows
        updated_count = 0  # Counter for successfully updated rows

        if match_id:  # Row-level submission
            match = Match.query.get(int(match_id))  # Ensure it's an integer
            if match:
                rank_1st = request.form.get(f"rank1_{match_id}", None)
                rank_2nd = request.form.get(f"rank2_{match_id}", None)
                rank_3rd = request.form.get(f"rank3_{match_id}", None)
                
                if not (rank_1st and rank_2nd and rank_3rd):
                    flash(f"Error: All ranks (1st, 2nd, 3rd) must be filled for Match {match_id}!", "error")
                    return redirect(url_for("input_page"))

                match.rank_1st = rank_1st
                match.rank_2nd = rank_2nd
                match.rank_3rd = rank_3rd
                match.common_rank = request.form.get(f"common_rank_{match_id}", None)
                match.common_rank_team = request.form.get(f"common_rank_team_{match_id}", None)

                db.session.commit()
                flash(f"Match {match_id} updated successfully!", "success")
                return redirect(url_for("input_page"))

        # Bulk submission logic
        matches = Match.query.all()
        for match in matches:
            rank_1st = request.form.get(f"rank1_{match.id}", None)
            rank_2nd = request.form.get(f"rank2_{match.id}", None)
            rank_3rd = request.form.get(f"rank3_{match.id}", None)

            if not (rank_1st and rank_2nd and rank_3rd):  
                errors += 1  # Count the missing rank rows
                continue  # Skip updating this row

            match.rank_1st = rank_1st
            match.rank_2nd = rank_2nd
            match.rank_3rd = rank_3rd
            match.common_rank = request.form.get(f"common_rank_{match.id}", None)
            match.common_rank_team = request.form.get(f"common_rank_team_{match.id}", None)

            updated_count += 1  # Count successful updates

        if updated_count > 0:
            db.session.commit()
            flash(f"Successfully updated {updated_count} matches!", "success")

        if errors > 0:
            flash(f"Error: {errors} matches were not updated because ranks (1st, 2nd, 3rd) were not filled!", "error")

        return redirect(url_for("input_page"))

    matches = Match.query.all()
    return render_template("input.html", matches=matches, teams=dream11_teams)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)