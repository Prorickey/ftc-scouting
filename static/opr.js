function sortedDictionaryKeysByValue(dict) {
    const items = Object.entries(dict);
  
    items.sort(([, valueA], [, valueB]) => valueB - valueA); // Sort in descending order
  
    return items.map(([k, ]) => k);
}

async function plotOPR(season, eventCode, statistic) {
    let response = await fetch(`/api/stats/opr/${season}/${eventCode}/${statistic}`, {
        method: 'GET'
    })
    let packet = await response.json();
    

    let data = [
        {
            x: sortedDictionaryKeysByValue(packet).map((val) => `team ${val}`),
            y: sortedDictionaryKeysByValue(packet).map((key) => packet[key]),
            type: 'bar',
            marker: {
                color: sortedDictionaryKeysByValue(packet).map(() => '#F3F4F6')
            }
        }
    ];

    let layout = {
        plot_bgcolor: '#1E2939',
        paper_bgcolor: '#1E2939',
        barcornerradius: '5',
        font: {color: '#ffffff'}
    };

    let config = {
        responsive: true
    };
      
    Plotly.newPlot('oprChart', data, layout, config);
}