# Read the current file
with open('app_flask_fast.py', 'r') as f:
    content = f.read()

# Find and replace the topics display section
old_section = """                let html = '<h3>📊 Discovered Topics</h3>';
                        
                        // Topic boxes
                        data.forEach(topic => {
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
                        
                        document.getElementById('topicsResults').innerHTML = html;"""

new_section = """                // Just show the chart - no detailed topic boxes
                        let html = '<h3>📊 Topic Distribution</h3>';
                        document.getElementById('topicsResults').innerHTML = html;"""

content = content.replace(old_section, new_section)

# Write back
with open('app_flask_fast.py', 'w') as f:
    f.write(content)

print("✅ Updated Feature 3 to be cleaner!")
