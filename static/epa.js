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
            type: 'linear',
            line: {
                color: '#F3F4F6',
                shape: 'spline',
                smoothing: 0.3
            }
        }
    ];

    let layout = {
        plot_bgcolor: '#1E2939',
        paper_bgcolor: '#1E2939',
        font: {color: '#ffffff'}
    };

    let config = {
        responsive: true
    };
      
    Plotly.newPlot('epaChart', data, layout, config);

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

function setElementColorForEPA(element, percentile) {
    if (percentile <= 0.01) {
        // blue
        element.classList.remove("bg-gray-700", "text-gray-800", "bg-green-400", "bg-blue-500", "text-white", "bg-green-200", "bg-red-200");
        element.classList.add("bg-blue-500", "text-white");
    } else if (percentile <= 0.10) {
        // dark green
        element.classList.remove("bg-gray-700", "text-gray-800", "bg-green-400", "bg-blue-500", "text-white", "bg-green-200", "bg-red-200");
        element.classList.add("bg-green-400", "text-gray-800");
    } else if (percentile <= 0.25) {
        // light green
        element.classList.remove("bg-gray-700", "text-gray-800", "bg-green-400", "bg-blue-500", "text-white", "bg-green-200", "bg-red-200");
        element.classList.add("bg-green-200", "text-gray-800");
    } else if (percentile <= 0.75) {
        // nothing
        element.classList.remove("bg-gray-700", "text-gray-800", "bg-green-400", "bg-blue-500", "text-white", "bg-green-200", "bg-red-200");
        element.classList.add("bg-gray-700", "text-white");
    } else {
        // red
        element.classList.remove("bg-gray-700", "text-gray-800", "bg-green-400", "bg-blue-500", "text-white", "bg-green-200", "bg-red-200");
        element.classList.add("bg-red-200", "text-gray-800");
    }
}

async function updateEPA() {
    let team = document.getElementById('team').value;
    let currentEPA = await plotEPAs(2024, team);
    document.getElementById('epa').hidden = false;
    document.getElementById('rank').hidden = false;
    document.getElementById('epa').innerText = `EPA: ${Number(currentEPA).toFixed(1)}`;
    let percentile = window.ranks[team][0] / Object.keys(window.ranks).length;
    setElementColorForEPA(document.getElementById("rank"), percentile);
    document.getElementById('rank').innerText = `World Rank: #${window.ranks[team][0]}`;
}