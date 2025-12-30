import psycopg2
import pandas as pd
from collections import Counter
import re
from bs4 import BeautifulSoup

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="crawler",
        user="postgres",
        password="cs515"
    )

def strip_html(text):
    """Remove HTML tags from text."""
    if not text or pd.isna(text):
        return ""
    soup = BeautifulSoup(str(text), 'html.parser')
    return soup.get_text()

def extract_top_words(platform, start_date='2025-11-01', end_date='2025-11-15', top_n=50):
    """Extract most frequently used words from posts."""
    conn = get_db_connection()
    
    if platform == 'bsky':
        # Bluesky: Extract text from ALL available fields
        query = f"""
            SELECT 
                COALESCE(data->'record'->>'text', '') as post_text,
                COALESCE(data->'embed'->'external'->>'title', '') as link_title,
                COALESCE(data->'embed'->'external'->>'description', '') as link_desc
            FROM posts_bsky
            WHERE created_at >= '{start_date}'
              AND created_at < '{end_date}'
        """
    else:
        # 4chan
        query = f"""
            SELECT data->>'com' as text
            FROM posts_4chan
            WHERE board_name = '{platform}'
              AND created_at >= '{start_date}'
              AND created_at < '{end_date}'
              AND data->>'com' IS NOT NULL
        """
    
    print(f"Loading posts from {platform}...")
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"Loaded {len(df):,} posts")
    
    # Combine all text fields
    if platform == 'bsky':
        # Combine post_text, link_title, and link_desc
        df['combined_text'] = (
            df['post_text'].fillna('') + ' ' + 
            df['link_title'].fillna('') + ' ' + 
            df['link_desc'].fillna('')
        )
        all_text = ' '.join(df['combined_text'])
    else:
        # Strip HTML for 4chan
        print("Stripping HTML...")
        df['clean_text'] = df['text'].apply(strip_html)
        all_text = ' '.join(df['clean_text'].fillna(''))
    
    # Extract words (3+ characters)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
    
    print(f"Extracted {len(words):,} total words")
    
    # Expanded stopwords
    stopwords = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 
        'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 
        'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 
        'its', 'let', 'put', 'say', 'she', 'too', 'use', 'this', 'that', 'with', 
        'have', 'from', 'they', 'been', 'what', 'will', 'your', 'said', 'each', 
        'tell', 'does', 'very', 'when', 'much', 'some', 'than', 'them', 'time', 
        'into', 'just', 'know', 'take', 'make', 'only', 'over', 'such', 'come',
        'also', 'back', 'even', 'good', 'more', 'most', 'like', 'look', 'would',
        'could', 'should', 'about', 'after', 'being', 'were', 'think', 'really',
        'going', 'still', 'dont', 'cant', 'wont', 'isnt', 'thats', 'there', 'their',
        'doesnt', 'didnt', 'youre', 'hes', 'shes', 'theyre', 'weve', 'theyve',
        'https', 'http', 'www', 'com', 'html', 'utm', 'source', 'campaign', 'medium'
    }
    
    # Count words
    word_counts = Counter([w for w in words if w not in stopwords and len(w) > 3])
    
    top_words = word_counts.most_common(top_n)
    
    return pd.DataFrame(top_words, columns=['word', 'count'])

def categorize_sports(word_df):
    """Categorize discovered words into sports."""
    sport_keywords = {
        'NFL/Football': ['nfl', 'football', 'chiefs', 'eagles', 'cowboys', 'touchdown', 'quarterback', 'superbowl', 'mahomes', 'rams', 'bills'],
        'NBA/Basketball': ['nba', 'basketball', 'lakers', 'celtics', 'warriors', 'lebron', 'curry', 'championship'],
        'Soccer': ['soccer', 'arsenal', 'messi', 'ronaldo', 'barcelona', 'madrid', 'united', 'manchester', 'premier', 'league', 'chelsea', 'liverpool'],
        'MLB/Baseball': ['baseball', 'yankees', 'dodgers', 'pitcher', 'homer'],
        'NHL/Hockey': ['hockey', 'puck', 'stanley'],
        'MMA/Combat': ['ufc', 'fight', 'fighter', 'knockout', 'wrestling', 'joshua', 'boxing']
    }
    
    sport_totals = {}
    for sport, keywords in sport_keywords.items():
        total = word_df[word_df['word'].str.lower().isin(keywords)]['count'].sum()
        sport_totals[sport] = total
    
    return pd.DataFrame(list(sport_totals.items()), columns=['sport', 'mentions']).sort_values('mentions', ascending=False)

if __name__ == "__main__":
    print("\n=== /sp/ - Top Words ===")
    sp_words = extract_top_words('sp', top_n=50)
    print(sp_words.head(20))
    
    print("\n=== /sp/ - Sports Categories ===")
    sp_sports = categorize_sports(sp_words)
    print(sp_sports)
    
    print("\n=== Bluesky - Top Words (with titles & descriptions) ===")
    bsky_words = extract_top_words('bsky', top_n=50)
    print(bsky_words.head(20))
    
    print("\n=== Bluesky - Sports Categories ===")
    bsky_sports = categorize_sports(bsky_words)
    print(bsky_sports)
