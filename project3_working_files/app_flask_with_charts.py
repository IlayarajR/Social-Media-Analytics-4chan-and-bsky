from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import psycopg2
import pandas as pd
import json
from feature_media_engagement import get_media_engagement_4chan, get_media_engagement_bsky
from feature_event_spike import get_event_comparison, get_hourly_activity
from feature_lda_topics import discover_topics_lda

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="crawler",
        user="postgres",
        password="cs515"
    )

@app.route('/')
def home():
    return '''
    <html>
    <head>
        <title>Sports Social Media Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            h1 { color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
            .container { max-width: 1400px; margin: 0 auto; }
            .stats, .feature { 
                background: white; 
                padding: 25px; 
                margin: 20px 0; 
                border-radius: 15px;
                box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            }
            .tabs {
                display: flex;
                gap: 10px;
                margin: 20px 0;
                flex-wrap: wrap;
            }
            .tab {
                padding: 12px 24px;
                background: rgba(255,255,255,0.9);
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 15px;
                font-weight: 600;
                transition: all 0.3s;
            }
            .tab:hover {
                background: white;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            .tab.active {
                background: #4CAF50;
                color: white;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }
            th, td {
                padding: 14px;
                text-align: left;
                border-bottom: 1px solid #e0e0e0;
            }
            th {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-weight: 600;
            }
            tr:hover {
                background: #f5f5f5;
            }
            select, input {
                padding: 10px;
                margin: 10px 5px;
                border-radius: 6px;
                border: 2px solid #e0e0e0;
                font-size: 14px;
            }
            select:focus, input:focus {
                border-color: #667eea;
                outline: none;
            }
            button {
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                margin: 10px 5px;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.3s;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }
            .metric { 
                font-size: 32px; 
                font-weight: bold; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .insight {
                background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
                padding: 20px;
                border-left: 5px solid #4CAF50;
                border-radius: 8px;
                margin: 20px 0;
            }
            .phase-box {
                display: inline-block;
                padding: 25px;
                margin: 15px;
                background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
                border-radius: 12px;
                text-align: center;
                min-width: 160px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .phase-box h3 { margin: 5px 0; color: #666; font-size: 14px; text-transform: uppercase; }
            .phase-box .num { font-size: 36px; font-weight: bold; color: #667eea; }
            .loading {
                text-align: center;
                padding: 50px;
                color: #666;
                font-style: italic;
                font-size: 16px;
            }
            .chart-container {
                margin: 25px 0;
                padding: 20px;
                background: #fafafa;
                border-radius: 10px;
            }
            .topic-box {
                background: linear-gradient(135deg, #f9f9f9 0%, #f0f0f0 100%);
                padding: 18px;
                margin: 12px 0;
                border-radius: 8px;
                border-left: 5px solid #667eea;
            }
            .topic-words {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: 12px;
            }
            .word-tag {
                background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 500;
            }
            .disclaimer {
                background: #fff3cd;
                border-left: 5px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                font-size: 13px;
                border-radius: 8px;
            }
            .stats h3 {
                color: #333;
                margin-bottom: 15px;
            }
            .stats p {
                margin: 10px 0;
                font-size: 16px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Sports Social Media Analytics Dashboard</h1>
            <p style="color: white; font-size: 18px;">Interactive analysis of 4chan (/sp/, /pol/) and Bluesky sports discussions</p>
            
            <div class="stats" id="stats">Loading stats...</div>
            
            <div class="tabs">
                <button class="tab active" onclick="showFeature(1)">🏈 Event Spike</button>
                <button class="tab" onclick="showFeature(2)">📸 Media vs Text</button>
                <button class="tab" onclick="showFeature(3)">🏆 Sports Topics</button>
            </div>
            
            <!-- Feature 1: Event Spike -->
            <div id="feature1" class="feature">
                <h2>🏈 Event Spike Analyzer</h2>
                <p>Analyze posting patterns around sporting events</p>
                
                <label>Platform:</label>
                <select id="event_platform">
                    <option value="sp">/sp/ (Sports)</option>
                    <option value="bsky">Bluesky</option>
                </select>
                
                <label>Select Date:</label>
                <input type="date" id="event_date" value="2025-11-10">
                
                <button onclick="loadEventData()">📊 Analyze Event Day</button>
                <button onclick="loadHourlyChart()">📈 Show Hourly Trend</button>
                
                <div id="eventResults"></div>
                <div id="eventChart" class="chart-container" style="display:none;"></div>
                <div id="hourlyChart" class="chart-container" style="display:none;"></div>
            </div>
            
            <!-- Feature 2: Media Engagement -->
            <div id="feature2" class="feature" style="display:none;">
                <h2>📸 Media vs Text-Only Engagement</h2>
                <p>Compare engagement between posts with media versus text-only posts</p>
                
                <label>Select Platform:</label>
                <select id="platform" onchange="loadMediaData()">
                    <option value="sp">/sp/ (Sports)</option>
                    <option value="pol">/pol/ (Politics)</option>
                    <option value="bsky">Bluesky</option>
                </select>
                
                <div id="mediaResults"></div>
                <div id="mediaChart" class="chart-container"></div>
            </div>
            
            <!-- Feature 3: Sports Topics -->
            <div id="feature3" class="feature" style="display:none;">
                <h2>🏆 Sports Topic Explorer</h2>
                <p>Discover which sports and topics dominate using unsupervised machine learning (LDA)</p>
                
                <label>Platform:</label>
                <select id="topics_platform">
                    <option value="sp">/sp/ (Sports)</option>
                    <option value="bsky">Bluesky</option>
                </select>
                
                <button onclick="loadTopicsData()">🔬 Analyze Topics (takes 2-3 min)</button>
                
                <div class="disclaimer">
                    ℹ️ <strong>Methodology:</strong> Analysis uses Latent Dirichlet Allocation (LDA) on 50,000 sampled posts 
                    to discover topics without predefined categories. Results reflect major trends during November 1-14, 2025.
                </div>
                
                <div id="topicsResults"></div>
                <div id="topicsChart" class="chart-container" style="display:none;"></div>
            </div>
        </div>
        
        <script>
            // Load stats
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('stats').innerHTML = 
                        '<h3>📡 Live Database Stats</h3>' +
                        '<p>Bluesky: <span class="metric">' + data.bsky.toLocaleString() + '</span> posts</p>' +
                        '<p>/sp/: <span class="metric">' + data.sp.toLocaleString() + '</span> posts</p>' +
                        '<p>/pol/: <span class="metric">' + data.pol.toLocaleString() + '</span> posts</p>' +
                        '<p><strong>Total: <span class="metric">' + data.total.toLocaleString() + '</span> posts</strong></p>';
                });
            
            // Tab switching
            function showFeature(num) {
                ['feature1', 'feature2', 'feature3'].forEach(id => {
                    document.getElementById(id).style.display = 'none';
                });
                document.getElementById('feature' + num).style.display = 'block';
                
                document.querySelectorAll('.tab').forEach((tab, i) => {
                    tab.classList.remove('active');
                    if (i + 1 === num) tab.classList.add('active');
                });
                
                // Load initial data for feature 2
                if (num === 2) {
                    loadMediaData();
                }
            }
            
            // Feature 1: Event comparison
            function loadEventData() {
                const platform = document.getElementById('event_platform').value;
                const date = document.getElementById('event_date').value;
                
                document.getElementById('eventResults').innerHTML = '<div class="loading">Loading...</div>';
                document.getElementById('eventChart').style.display = 'none';
                
                fetch('/api/event-comparison?platform=' + platform + '&date=' + date)
                    .then(r => r.json())
                    .then(data => {
                        // Show boxes
                        let html = '<h3>Activity on ' + date + '</h3>';
                        html += '<div style="text-align: center;">';
                        
                        data.forEach(row => {
                            html += '<div class="phase-box">';
                            html += '<h3>' + row.phase + '</h3>';
                            html += '<div class="num">' + row.post_count.toLocaleString() + '</div>';
                            html += '<p>posts</p>';
                            html += '</div>';
                        });
                        
                        html += '</div>';
                        document.getElementById('eventResults').innerHTML = html;
                        
                        // Create bar chart
                        const chartData = [{
                            x: data.map(d => d.phase),
                            y: data.map(d => d.post_count),
                            type: 'bar',
                            marker: {
                                color: ['#667eea', '#764ba2', '#f093fb']
                            }
                        }];
                        
                        const layout = {
                            title: 'Posts by Event Phase',
                            xaxis: { title: 'Event Phase' },
                            yaxis: { title: 'Number of Posts' },
                            plot_bgcolor: '#fafafa',
                            paper_bgcolor: '#fafafa'
                        };
                        
                        document.getElementById('eventChart').style.display = 'block';
                        Plotly.newPlot('eventChart', chartData, layout);
                        
                        // Add insight
                        if (data.length === 3) {
                            const before = data.find(d => d.phase === 'BEFORE').post_count;
                            const during = data.find(d => d.phase === 'DURING').post_count;
                            const after = data.find(d => d.phase === 'AFTER').post_count;
                            
                            let insight = '<div class="insight"><strong>💡 Insight:</strong> ';
                            if (during < before && during < after) {
                                insight += 'Activity drops DURING events - users are busy watching!';
                            } else if (during > before) {
                                insight += 'Activity spikes DURING events - live discussion happening!';
                            } else {
                                insight += 'Activity is highest BEFORE events - anticipation building!';
                            }
                            insight += '</div>';
                            document.getElementById('eventResults').innerHTML += insight;
                        }
                    })
                    .catch(err => {
                        document.getElementById('eventResults').innerHTML = 
                            '<p style="color:red;">Error: ' + err + '</p>';
                    });
            }
            
            // Feature 1: Hourly chart
            function loadHourlyChart() {
                const platform = document.getElementById('event_platform').value;
                document.getElementById('hourlyChart').innerHTML = '<div class="loading">Loading hourly data...</div>';
                document.getElementById('hourlyChart').style.display = 'block';
                
                fetch('/api/hourly-activity?platform=' + platform + '&start=2025-11-01&end=2025-11-15')
                    .then(r => r.json())
                    .then(data => {
                        const trace = {
                            x: data.map(d => d.hour),
                            y: data.map(d => d.post_count),
                            type: 'scatter',
                            mode: 'lines',
                            line: {
                                color: '#667eea',
                                width: 3
                            },
                            fill: 'tozeroy',
                            fillcolor: 'rgba(102, 126, 234, 0.2)'
                        };
                        
                        const layout = {
                            title: platform.toUpperCase() + ' Hourly Activity (Nov 1-14, 2025)',
                            xaxis: { title: 'Date/Time' },
                            yaxis: { title: 'Posts per Hour' },
                            hovermode: 'closest',
                            plot_bgcolor: '#fafafa',
                            paper_bgcolor: '#fafafa'
                        };
                        
                        Plotly.newPlot('hourlyChart', [trace], layout);
                    })
                    .catch(err => {
                        document.getElementById('hourlyChart').innerHTML = 
                            '<p style="color:red;">Error loading chart</p>';
                    });
            }
            
            // Feature 2: Media engagement
            function loadMediaData() {
                const platform = document.getElementById('platform').value;
                document.getElementById('mediaResults').innerHTML = '<div class="loading">Loading...</div>';
                
                fetch('/api/media-engagement?platform=' + platform)
                    .then(r => r.json())
                    .then(data => {
                        // Table
                        let html = '<table><tr><th>Post Type</th><th>Number of Posts</th>';
                        
                        if (platform === 'bsky') {
                            html += '<th>Avg Likes</th><th>Avg Reposts</th>';
                        } else {
                            html += '<th>Avg Thread Size</th>';
                        }
                        html += '</tr>';
                        
                        data.forEach(row => {
                            html += '<tr>';
                            html += '<td><strong>' + row.post_type + '</strong></td>';
                            html += '<td>' + row.num_posts.toLocaleString() + '</td>';
                            if (platform === 'bsky') {
                                html += '<td>' + row.avg_likes + '</td>';
                                html += '<td>' + row.avg_reposts + '</td>';
                            } else {
                                html += '<td>' + row.avg_thread_size + '</td>';
                            }
                            html += '</tr>';
                        });
                        html += '</table>';
                        
                        // Insight
                        if (data.length === 2) {
                            html += '<div class="insight"><strong>💡 Insight:</strong> ';
                            if (platform === 'bsky') {
                                const ratio = (data[1].avg_likes / data[0].avg_likes).toFixed(2);
                                html += 'Text-only posts get <strong>' + ratio + 'x MORE</strong> likes than media posts on Bluesky!';
                            } else {
                                const media_size = data[0].avg_thread_size;
                                const text_size = data[1].avg_thread_size;
                                const diff = ((media_size / text_size - 1) * 100).toFixed(1);
                                if (diff > 0) {
                                    html += 'Media posts appear in threads ' + diff + '% larger';
                                } else {
                                    html += 'Text-only posts appear in threads ' + Math.abs(diff) + '% larger';
                                }
                            }
                            html += '</div>';
                        }
                        
                        document.getElementById('mediaResults').innerHTML = html;
                        
                        // Bar chart
                        if (data.length === 2) {
                            const metricName = platform === 'bsky' ? 'Avg Likes' : 'Avg Thread Size';
                            const values = platform === 'bsky' 
                                ? data.map(d => d.avg_likes)
                                : data.map(d => d.avg_thread_size);
                            
                            const chartData = [{
                                x: data.map(d => d.post_type),
                                y: values,
                                type: 'bar',
                                marker: {
                                    color: ['#667eea', '#764ba2']
                                },
                                text: values.map(v => v.toFixed(2)),
                                textposition: 'auto'
                            }];
                            
                            const layout = {
                                title: 'Engagement Comparison: Media vs Text-Only',
                                xaxis: { title: 'Post Type' },
                                yaxis: { title: metricName },
                                plot_bgcolor: '#fafafa',
                                paper_bgcolor: '#fafafa'
                            };
                            
                            Plotly.newPlot('mediaChart', chartData, layout);
                        }
                    });
            }
            
            // Feature 3: LDA Topics
            function loadTopicsData() {
                const platform = document.getElementById('topics_platform').value;
                document.getElementById('topicsResults').innerHTML = 
                    '<div class="loading">🔬 Running machine learning analysis...<br>' +
                    'Processing 50,000 posts with LDA topic modeling<br>' +
                    'This takes 2-3 minutes, please wait...</div>';
                
                fetch('/api/lda-topics?platform=' + platform)
                    .then(r => r.json())
                    .then(data => {
                        let html = '<h3>📊 Discovered Topics (Unsupervised ML)</h3>';
                        
                        // Topic boxes
                        data.topics.forEach(topic => {
                            const percentage = topic.prevalence * 100;
                            html += '<div class="topic-box">';
                            html += '<strong>' + topic.label + '</strong> ';
                            html += '<span style="color:#666;">(' + percentage.toFixed(1) + '% of posts)</span>';
                            html += '<div class="topic-words">';
                            topic.top_words.slice(0, 10).forEach(word => {
                                html += '<span class="word-tag">' + word + '</span>';
                            });
                            html += '</div>';
                            html += '</div>';
                        });
                        
                        html += '<div class="insight">';
                        html += '<strong>💡 Key Finding:</strong> ';
                        const topTopic = data.topics[0];
                        html += topTopic.label + ' dominates with ' + (topTopic.prevalence * 100).toFixed(1) + '% of the conversation.';
                        html += '</div>';
                        
                        document.getElementById('topicsResults').innerHTML = html;
                        
                        // Pie chart
                        const pieData = [{
                            labels: data.topics.map(t => t.label),
                            values: data.topics.map(t => t.prevalence * 100),
                            type: 'pie',
                            marker: {
                                colors: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe', '#43e97b']
                            },
                            textinfo: 'label+percent',
                            textposition: 'outside'
                        }];
                        
                        const pieLayout = {
                            title: 'Topic Distribution',
                            plot_bgcolor: '#fafafa',
                            paper_bgcolor: '#fafafa'
                        };
                        
                        document.getElementById('topicsChart').style.display = 'block';
                        Plotly.newPlot('topicsChart', pieData, pieLayout);
                    })
                    .catch(err => {
                        document.getElementById('topicsResults').innerHTML = 
                            '<p style="color:red;">Error: ' + err + '</p>';
                    });
            }
        </script>
    </body>
    </html>
    '''

@app.route('/api/stats')
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM posts_bsky")
    bsky = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM posts_4chan WHERE board_name='sp'")
    sp = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM posts_4chan WHERE board_name='pol'")
    pol = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'bsky': bsky,
        'sp': sp,
        'pol': pol,
        'total': bsky + sp + pol
    })

@app.route('/api/media-engagement')
def media_engagement():
    platform = request.args.get('platform', 'sp')
    
    if platform in ['sp', 'pol']:
        df = get_media_engagement_4chan(platform)
    else:
        df = get_media_engagement_bsky()
    
    return jsonify(df.to_dict('records'))

@app.route('/api/event-comparison')
def event_comparison():
    platform = request.args.get('platform', 'sp')
    date = request.args.get('date', '2025-11-10')
    
    df = get_event_comparison(platform, date)
    return jsonify(df.to_dict('records'))

@app.route('/api/hourly-activity')
def hourly_activity():
    platform = request.args.get('platform', 'sp')
    start = request.args.get('start', '2025-11-01')
    end = request.args.get('end', '2025-11-15')
    
    df = get_hourly_activity(platform, start, end)
    
    result = []
    for _, row in df.iterrows():
        result.append({
            'hour': row['hour'].isoformat(),
            'post_count': int(row['post_count']),
            'hour_of_day': int(row['hour_of_day']),
            'day_of_week': int(row['day_of_week'])
        })
    
    return jsonify(result)

@app.route('/api/lda-topics')
def lda_topics():
    platform = request.args.get('platform', 'sp')
    
    topics_data, lda_model, vectorizer = discover_topics_lda(platform, n_topics=6, n_top_words=10)
    
    from feature_lda_topics import load_platform_text
    import re
    
    texts = load_platform_text(platform, limit=50000)
    cleaned_texts = [re.sub(r'https?://\S+', '', text) for text in texts if len(text) > 20]
    doc_term_matrix = vectorizer.transform(cleaned_texts)
    doc_topic_dist = lda_model.transform(doc_term_matrix)
    topic_prevalence = doc_topic_dist.mean(axis=0)
    
    result = {'topics': []}
    
    for i, topic_info in enumerate(topics_data):
        result['topics'].append({
            'topic_num': topic_info['topic_num'],
            'label': topic_info['label'],
            'top_words': topic_info['top_words'],
            'prevalence': float(topic_prevalence[i])
        })
    
    result['topics'].sort(key=lambda x: x['prevalence'], reverse=True)
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
