from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ipl_betting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'some_secret_key'
db = SQLAlchemy(app)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_date = db.Column(db.String(50), nullable=False)
    teams_playing = db.Column(db.String(100), nullable=False)
    rank_1st = db.Column(db.String(50), nullable=True)
    rank_2nd = db.Column(db.String(50), nullable=True)
    rank_3rd = db.Column(db.String(50), nullable=True)

dream11_teams = [
    "APS Gladiators01", "KHAL-DROGO", "nMnF11", "Beind Baibhav",
    "Sanju Bawa XI", "11 SAFED TIGER", "HammerHeadsx1", "Shubham141193"
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
                winnings[team]["Total Bet"] += bet_amount
        
        for rank, team in zip(["Rank1", "Rank2", "Rank3"], [match.rank_1st, match.rank_2nd, match.rank_3rd]):
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
    if request.method == 'POST':
        for match in Match.query.all():
            rank1 = request.form.get(f'rank1_{match.id}', None)
            rank2 = request.form.get(f'rank2_{match.id}', None)
            rank3 = request.form.get(f'rank3_{match.id}', None)
            
            filled_ranks = sum(bool(r) for r in [rank1, rank2, rank3])
            if 0 < filled_ranks < 3:
                flash("Please fill all three ranks for each match before submitting.", "error")
                return redirect(url_for('input_page'))
            
            match.rank_1st = rank1
            match.rank_2nd = rank2
            match.rank_3rd = rank3
        db.session.commit()
        return redirect(url_for('index'))
    matches = Match.query.all()
    return render_template('input.html', matches=matches, teams=dream11_teams)

if __name__ == '__main__':
    app.run(debug=True)
