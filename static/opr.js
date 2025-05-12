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
            type: 'bar'
        }
    ];
      
    Plotly.newPlot('oprChart', data);
}