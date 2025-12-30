from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import psycopg2
import pandas as pd
from feature_media_engagement import get_media_engagement_4chan, get_media_engagement_bsky
from feature_event_spike import get_event_comparison, get_hourly_activity
from feature_sports_topics import extract_top_words, categorize_sports

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
        <style>
            body { 
                font-family: Arial, sans-serif; 
                padding: 20px; 
                background: #f5f5f5;
            }
            h1 { color: #333; }
            .container { max-width: 1400px; margin: 0 auto; }
            .stats, .feature { 
                background: white; 
                padding: 20px; 
                margin: 15px 0; 
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .tabs {
                display: flex;
                gap: 10px;
                margin: 20px 0;
            }
            .tab {
                padding: 10px 20px;
                background: #e0e0e0;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
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
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background: #4CAF50;
                color: white;
            }
            select, input {
                padding: 8px;
                margin: 10px 5px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }
            button {
                padding: 10px 20px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin: 10px 5px;
            }
            button:hover {
                background: #45a049;
            }
            .metric { font-size: 24px; font-weight: bold; color: #4CAF50; }
            .insight {
                background: #e8f5e9;
                padding: 15px;
                border-left: 4px solid #4CAF50;
                margin: 15px 0;
            }
            .phase-box {
                display: inline-block;
                padding: 20px;
                margin: 10px;
                background: #f0f0f0;
                border-radius: 8px;
                text-align: center;
                min-width: 150px;
            }
            .phase-box h3 { margin: 5px 0; color: #666; }
            .phase-box .num { font-size: 32px; font-weight: bold; color: #4CAF50; }
            .word-cloud {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin: 20px 0;
            }
            .word-item {
                padding: 8px 15px;
                background: #e8f5e9;
                border-radius: 20px;
                font-size: 14px;
            }
            .loading {
                text-align: center;
                padding: 40px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Sports Social Media Analytics Dashboard</h1>
            <p>Interactive analysis of 4chan (/sp/, /pol/) and Bluesky sports discussions</p>
            
            <div class="stats" id="stats">Loading stats...</div>
            
            <div class="tabs">
                <button class="tab active" onclick="showFeature(1)">🏈 Event Spike</button>
                <button class="tab" onclick="showFeature(2)">📸 Media vs Text</button>
                <button class="tab" onclick="showFeature(3)">🏆 Sports Topics</button>
                <button class="tab" onclick="showFeature(4)">☣️ Toxicity</button>
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
                
                <button onclick="loadEventData()">Analyze Event Day</button>
                
                <div id="eventResults">Click "Analyze Event Day" to see before/during/after breakdown</div>
            </div>
            
            <!-- Feature 2: Media Engagement -->
            <div id="feature2" class="feature" style="display:none;">
                <h2>📸 Media vs Text-Only Engagement</h2>
                <p>Compare engagement between posts with media versus text-only posts</p>
                
                <label>Select Platform:</label>
                <select id="platform" onchange="loadMediaData()">
                    <option value="sp">/sp/ (Sports)</option>
                    <option value="bsky">Bluesky</option>
                    <option value="bsky">Bluesky</option>
                </select>
                
                <div id="mediaResults">Loading...</div>
            </div>
            
            <!-- Feature 3: Sports Topics -->
            <div id="feature3" class="feature" style="display:none;">
                <h2>🏆 Sports Topic Explorer</h2>
                <p>Discover which sports and topics dominate the conversation</p>
                
                <label>Platform:</label>
                <select id="topics_platform">
                    <option value="sp">/sp/ (Sports)</option>
                    <option value="bsky">Bluesky</option>
                </select>
                
                <button onclick="loadTopicsData()">Analyze Topics</button>
                
                <div id="topicsResults">
                    <div class="loading">Click "Analyze Topics" to discover what people are talking about</div>
                </div>
            </div>
            
            <!-- Feature 4: Toxicity -->
            <div id="feature4" class="feature" style="display:none;">
                <h2>☣️ Toxicity Deep Dive</h2>
                <p>🚧 Coming soon - Explore toxicity patterns</p>
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
                        '<p><strong>Total: ' + data.total.toLocaleString() + ' posts</strong></p>';
                });
            
            // Tab switching
            function showFeature(num) {
                ['feature1', 'feature2', 'feature3', 'feature4'].forEach(id => {
                    document.getElementById(id).style.display = 'none';
                });
                document.getElementById('feature' + num).style.display = 'block';
                
                document.querySelectorAll('.tab').forEach((tab, i) => {
                    tab.classList.remove('active');
                    if (i + 1 === num) tab.classList.add('active');
                });
            }
            
            // Feature 1: Event comparison
            function loadEventData() {
                const platform = document.getElementById('event_platform').value;
                const date = document.getElementById('event_date').value;
                
                document.getElementById('eventResults').innerHTML = '<div class="loading">Loading...</div>';
                
                fetch('/api/event-comparison?platform=' + platform + '&date=' + date)
                    .then(r => r.json())
                    .then(data => {
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
                        
                        if (data.length === 3) {
                            const before = data.find(d => d.phase === 'BEFORE').post_count;
                            const during = data.find(d => d.phase === 'DURING').post_count;
                            const after = data.find(d => d.phase === 'AFTER').post_count;
                            
                            html += '<div class="insight">';
                            html += '<strong>💡 Insight:</strong> ';
                            
                            if (during < before && during < after) {
                                html += 'Activity drops DURING events - users are busy watching!';
                            } else if (during > before) {
                                html += 'Activity spikes DURING events - live discussion happening!';
                            } else {
                                html += 'Activity is highest BEFORE events - anticipation building!';
                            }
                            html += '</div>';
                        }
                        
                        document.getElementById('eventResults').innerHTML = html;
                    })
                    .catch(err => {
                        document.getElementById('eventResults').innerHTML = 
                            '<p style="color:red;">Error: ' + err + '</p>';
                    });
            }
            
            // Feature 2: Media engagement
            function loadMediaData() {
                const platform = document.getElementById('platform').value;
                document.getElementById('mediaResults').innerHTML = '<div class="loading">Loading...</div>';
                
                fetch('/api/media-engagement?platform=' + platform)
                    .then(r => r.json())
                    .then(data => {
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
                    });
            }
            
            // Feature 3: Sports topics
            function loadTopicsData() {
                const platform = document.getElementById('topics_platform').value;
                document.getElementById('topicsResults').innerHTML = '<div class="loading">Analyzing topics... This may take 30-60 seconds...</div>';
                
                fetch('/api/sports-topics?platform=' + platform + '&top_n=50')
                    .then(r => r.json())
                    .then(data => {
                        let html = '<h3>Sport Categories</h3>';
                        html += '<table><tr><th>Sport</th><th>Mentions</th></tr>';
                        data.sports.forEach(row => {
                            html += '<tr><td><strong>' + row.sport + '</strong></td><td>' + row.mentions.toLocaleString() + '</td></tr>';
                        });
                        html += '</table>';
                        
                        html += '<h3>Top 30 Most Used Words</h3>';
                        html += '<div class="word-cloud">';
                        data.top_words.slice(0, 30).forEach(word => {
                            const size = Math.min(20, 10 + (word.count / 500));
                            html += '<div class="word-item" style="font-size: ' + size + 'px;">';
                            html += word.word + ' (' + word.count.toLocaleString() + ')';
                            html += '</div>';
                        });
                        html += '</div>';
                        
                        // Add insight
                        if (data.sports.length > 0) {
                            const topSport = data.sports[0];
                            html += '<div class="insight">';
                            html += '<strong>💡 Insight:</strong> ';
                            html += topSport.sport + ' dominates the conversation with ' + topSport.mentions.toLocaleString() + ' mentions!';
                            html += '</div>';
                        }
                        
                        document.getElementById('topicsResults').innerHTML = html;
                    })
                    .catch(err => {
                        document.getElementById('topicsResults').innerHTML = 
                            '<p style="color:red;">Error: ' + err + '</p>';
                    });
            }
            
            // Load initial data
            loadMediaData();
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

@app.route('/api/sports-topics')
def sports_topics():
    platform = request.args.get('platform', 'sp')
    top_n = int(request.args.get('top_n', 50))
    
    words_df = extract_top_words(platform, top_n=top_n)
    sports_df = categorize_sports(words_df)
    
    return jsonify({
        'top_words': words_df.to_dict('records'),
        'sports': sports_df.to_dict('records')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
