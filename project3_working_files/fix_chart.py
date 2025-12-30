# Read the current app
with open('app_flask.py', 'r') as f:
    content = f.read()

# Find and replace the loadHourlyChart function
old_func = """            // Load hourly trend chart
            function loadHourlyChart() {
                const platform = document.getElementById('event_platform').value;
                document.getElementById('hourlyChart').innerHTML = 'Loading chart...';
                
                fetch('/api/hourly-activity?platform=' + platform + '&start=2025-11-01&end=2025-11-15')
                    .then(r => r.json())
                    .then(data => {
                        const trace = {
                            x: data.map(d => d.hour),
                            y: data.map(d => d.post_count),
                            type: 'scatter',
                            mode: 'lines',
                            line: {color: '#4CAF50', width: 2}
                        };
                        
                        const layout = {
                            title: platform.toUpperCase() + ' Hourly Activity (Nov 1-14, 2025)',
                            xaxis: {title: 'Date/Time'},
                            yaxis: {title: 'Posts per Hour'},
                            hovermode: 'closest'
                        };
                        
                        Plotly.newPlot('hourlyChart', [trace], layout);
                    });
            }"""

new_func = """            // Load hourly trend chart
            let isLoadingChart = false;
            function loadHourlyChart() {
                if (isLoadingChart) {
                    console.log('Chart already loading...');
                    return;
                }
                
                isLoadingChart = true;
                const platform = document.getElementById('event_platform').value;
                const chartDiv = document.getElementById('hourlyChart');
                chartDiv.innerHTML = '<p>Loading chart...</p>';
                
                fetch('/api/hourly-activity?platform=' + platform + '&start=2025-11-01&end=2025-11-15')
                    .then(r => r.json())
                    .then(data => {
                        if (data.length === 0) {
                            chartDiv.innerHTML = '<p style="color:red;">No data available for this period</p>';
                            isLoadingChart = false;
                            return;
                        }
                        
                        const trace = {
                            x: data.map(d => d.hour),
                            y: data.map(d => d.post_count),
                            type: 'scatter',
                            mode: 'lines',
                            line: {color: '#4CAF50', width: 2},
                            name: platform.toUpperCase()
                        };
                        
                        const layout = {
                            title: platform.toUpperCase() + ' Hourly Activity (Nov 1-14, 2025)',
                            xaxis: {title: 'Date/Time'},
                            yaxis: {title: 'Posts per Hour'},
                            hovermode: 'closest',
                            showlegend: false
                        };
                        
                        Plotly.newPlot(chartDiv, [trace], layout);
                        isLoadingChart = false;
                    })
                    .catch(err => {
                        chartDiv.innerHTML = '<p style="color:red;">Error loading chart: ' + err + '</p>';
                        isLoadingChart = false;
                    });
            }"""

content = content.replace(old_func, new_func)

with open('app_flask.py', 'w') as f:
    f.write(content)

print("✅ Fixed!")
