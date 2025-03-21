function updateRank(matchId) {
    const rank1 = document.querySelector(`select[data-match-id="${matchId}"][data-rank="1"]`).value;
    const rank2 = document.querySelector(`select[data-match-id="${matchId}"][data-rank="2"]`).value;
    const rank3 = document.querySelector(`select[data-match-id="${matchId}"][data-rank="3"]`).value;

    fetch('/update_rank', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ match_id: matchId, rank_1st: rank1, rank_2nd: rank2, rank_3rd: rank3 })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        fetchWinnings();
    });
}

function fetchWinnings() {
    fetch('/calculate_winnings')
    .then(response => response.json())
    .then(data => {
        renderChart(data.total_bets, data.total_winnings, data.net_winnings);
    });
}

function renderChart(totalBets, totalWinnings, netWinnings) {
    const ctx = document.getElementById('winningsChart').getContext('2d');

    if (window.winningsChart) {
        window.winningsChart.destroy();
    }

    window.winningsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Total Bets', 'Total Winnings', 'Net Winnings'],
            datasets: [{
                label: 'Amount (INR)',
                data: [totalBets, totalWinnings, netWinnings],
                backgroundColor: ['red', 'green', 'blue']
            }]
        }
    });
}

window.onload = fetchWinnings;
