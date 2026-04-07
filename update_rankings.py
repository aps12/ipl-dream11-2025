"""Script to update match rankings"""
from app import app, db, Match

# Name mapping
name_map = {
    'Baibhav': 'AhhhhZorSe',
    'Appu': 'DhurandharX1',
    'Apoorva': 'DhurandharX1',  # Alternative name
    'Himanshu': 'Himanshu',
    'Manik': 'KhalDrogo30',
    'Ankush': 'Mahasaheb11',
    'Praveer': 'Praveer0110',
    'Shubham Tiwari': 'Tiwari_Titans_Reloaded',
    'Abhay': 'aps1cricked',
    'Sanjay': 'czarsanjay',
    'Shubham Bihari': 'kshubham1411',
    'Mayank': 'love.sweat.fitness09',
    'Diggi': 'nMnF',
    'Sandesh': 'sun2692Horse'
}

# Rankings data - match number and ranks
rankings_data = [
    # Match 1: RCB vs SRH
    (1, ['Shubham Bihari', 'Himanshu', 'Mayank', 'Abhay']),
    # Match 2: KKR vs MI
    (2, ['Praveer', 'Manik', 'Sandesh', 'Mayank']),
    # Match 3: CSK vs RR
    (3, ['Baibhav', 'Sandesh', 'Mayank', 'Manik']),
    # Match 4: PK vs GT
    (4, ['Apoorva', 'Mayank', 'Sanjay', 'Manik']),
    # Match 5: LSG vs DC
    (5, ['Himanshu', 'Mayank', 'Shubham Bihari', 'Shubham Tiwari']),
    # Match 6: KKR vs SRH
    (6, ['Shubham Tiwari', 'Praveer', 'Baibhav', 'Ankush']),
    # Match 7: PK vs CSK
    (7, ['Ankush', 'Diggi', 'Mayank', 'Abhay']),
    # Match 8: DEL vs MUM
    (8, ['Mayank', 'Apoorva', 'Praveer', 'Manik']),
    # Match 9: RR vs GT (tied for 1st place - Diggi & Praveer)
    (9, 'TIE', ['Diggi', 'Praveer'], ['Mayank', 'Himanshu']),  # Both tied for 1st, no 2nd rank
    # Match 10: LSG vs SRH
    (10, ['Diggi', 'Sandesh', 'Ankush', 'Shubham Bihari']),
    # Match 11: RCB vs CSK
    (11, ['Manik', 'Shubham Bihari', 'Appu', 'Praveer']),
]

def update_rankings():
    """Update rankings for all matches"""
    with app.app_context():
        updated_count = 0
        
        # Get all matches ordered by date
        all_matches = Match.query.order_by(Match.match_date, Match.id).all()
        
        for item in rankings_data:
            match_num = item[0]
            
            # Check if this is a tie scenario
            if len(item) > 2 and item[1] == 'TIE':
                # TIE format: (match_num, 'TIE', [tied_for_1st], [remaining_ranks])
                tied_1st = item[2]
                remaining = item[3]
                
                # Get the match by position
                if match_num <= len(all_matches):
                    match = all_matches[match_num - 1]
                    
                    # Join tied teams with comma
                    match.rank_1st = ', '.join([name_map.get(name, name) for name in tied_1st])
                    match.rank_2nd = None  # No 2nd rank when there's a tie for 1st
                    match.rank_3rd = name_map.get(remaining[0], remaining[0]) if len(remaining) > 0 else None
                    match.rank_4th = name_map.get(remaining[1], remaining[1]) if len(remaining) > 1 else None
                    
                    print(f"✓ Updated Match {match_num}: {match.teams_playing} [TIE]")
                    print(f"  1st (TIE): {match.rank_1st}")
                    print(f"  2nd: {match.rank_2nd}")
                    print(f"  3rd: {match.rank_3rd}")
                    print(f"  4th: {match.rank_4th}")
                    updated_count += 1
            else:
                # Normal format: (match_num, [rank1, rank2, rank3, rank4])
                ranks = item[1]
                
                # Get the match by position
                if match_num <= len(all_matches):
                    match = all_matches[match_num - 1]
                    
                    # Map friendly names to team names
                    match.rank_1st = name_map.get(ranks[0], ranks[0]) if len(ranks) > 0 else None
                    match.rank_2nd = name_map.get(ranks[1], ranks[1]) if len(ranks) > 1 else None
                    match.rank_3rd = name_map.get(ranks[2], ranks[2]) if len(ranks) > 2 else None
                    match.rank_4th = name_map.get(ranks[3], ranks[3]) if len(ranks) > 3 else None
                    
                    print(f"✓ Updated Match {match_num}: {match.teams_playing}")
                    print(f"  1st: {match.rank_1st}")
                    print(f"  2nd: {match.rank_2nd}")
                    print(f"  3rd: {match.rank_3rd}")
                    print(f"  4th: {match.rank_4th}")
                    updated_count += 1
        
        # Commit all changes
        db.session.commit()
        print(f"\n✅ Successfully updated {updated_count} matches!")

if __name__ == '__main__':
    update_rankings()
