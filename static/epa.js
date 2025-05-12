async function plotEPAs(season, team) {
    /**
     * Plots the historical EPAs for a team in the div with id `epaChart` and returns their current EPA.
     * 
     * @param season the season to fetch EPAs for
     * @param team the team to get EPA for
     */
    let response = await fetch(`/api/stats/epa/${season}/${team}`, {
        method: 'GET'
    })
    let packet = await response.json();

    let data = [
        {
            x: Object.keys(packet).map((timestamp) => new Date(timestamp * 1000)),
            y: Object.values(packet),
            type: 'linear'
        }
    ];
      
    Plotly.newPlot('epaChart', data);

    let lastKey = Object.keys(packet).sort().reverse()[0];
    let lastValue = packet[lastKey];

    return lastValue;
}

async function getEPARanks(season) {
    let response = await fetch(`/api/stats/epa/${season}/ranks`, {
        method: 'GET'
    })
    let packet = await response.json();

    return packet;
}

window.onload = async () => {
    window.ranks = await getEPARanks(2024);
};

async function updateEPA() {
    let team = document.getElementById('team').value;
    let currentEPA = await plotEPAs(2024, team);
    document.getElementById('epa').innerText = `EPA: ${Number(currentEPA).toFixed(1)}`
    document.getElementById('rank').innerText = `World Rank: #${window.ranks[team]}`;
}