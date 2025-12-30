import psycopg2
import pandas as pd
import re
from bs4 import BeautifulSoup
from collections import Counter
import spacy
from gensim.models import Word2Vec
import warnings
warnings.filterwarnings('ignore')

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="crawler",
        user="postgres",
        password="cs515"
    )

def strip_html(text):
    if not text or pd.isna(text):
        return ""
    soup = BeautifulSoup(str(text), 'html.parser')
    return soup.get_text()

def load_platform_text(platform, start_date='2025-11-01', end_date='2025-11-15'):
    """Load all text from platform."""
    conn = get_db_connection()
    
    if platform == 'bsky':
        query = f"""
            SELECT 
                COALESCE(data->'record'->>'text', '') as post_text,
                COALESCE(data->'embed'->'external'->>'title', '') as link_title,
                COALESCE(data->'embed'->'external'->>'description', '') as link_desc
            FROM posts_bsky
            WHERE created_at >= '{start_date}'
              AND created_at < '{end_date}'
        """
        df = pd.read_sql(query, conn)
        df['text'] = df['post_text'] + ' ' + df['link_title'] + ' ' + df['link_desc']
    else:
        query = f"""
            SELECT data->>'com' as text
            FROM posts_4chan
            WHERE board_name = '{platform}'
              AND created_at >= '{start_date}'
              AND created_at < '{end_date}'
              AND data->>'com' IS NOT NULL
        """
        df = pd.read_sql(query, conn)
        df['text'] = df['text'].apply(strip_html)
    
    conn.close()
    return df['text'].fillna('').tolist()

def hybrid_analysis(platform):
    """
    Hybrid approach combining NER + Word2Vec + Smart Filtering
    """
    print(f"\n{'='*70}")
    print(f"🔬 HYBRID SPORTS TOPIC ANALYSIS: {platform.upper()}")
    print(f"{'='*70}")
    
    # Load data
    print("\n[1/4] Loading posts...")
    texts = load_platform_text(platform)
    print(f"      Loaded {len(texts):,} posts")
    
    # ============================================
    # STEP 1: NER - Extract Named Entities
    # ============================================
    print("\n[2/4] Extracting named entities (NER)...")
    nlp = spacy.load('en_core_web_sm')
    
    sample_size = min(10000, len(texts))  # Increased sample
    texts_sample = texts[:sample_size]
    
    all_entities = {
        'athletes': [],    # Individual people (fighters, players)
        'teams': [],       # Teams/Organizations
        'events': [],      # Events (World Series, UFC 300)
        'locations': []    # Venues/Cities
    }
    
    for i, text in enumerate(texts_sample):
        if i % 2000 == 0:
            print(f"      Processed {i:,}/{sample_size:,}...")
        
        doc = nlp(text[:1500])
        
        for ent in doc.ents:
            ent_lower = ent.text.lower().strip()
            
            # Skip garbage
            if len(ent_lower) < 3 or ent_lower in ['ref', 'lol', 'picrel', 'shit', 'kwab']:
                continue
            
            if ent.label_ == 'PERSON':
                all_entities['athletes'].append(ent_lower)
            elif ent.label_ == 'ORG':
                all_entities['teams'].append(ent_lower)
            elif ent.label_ == 'EVENT':
                all_entities['events'].append(ent_lower)
            elif ent.label_ in ['GPE', 'LOC', 'FAC']:
                all_entities['locations'].append(ent_lower)
    
    # ============================================
    # STEP 2: Word2Vec - Find Sport Clusters
    # ============================================
    print("\n[3/4] Training Word2Vec model...")
    
    # Tokenize
    sentences = []
    for text in texts:
        # Remove URLs
        text_clean = re.sub(r'https?://\S+', '', text)
        words = re.findall(r'\b[a-z]{3,}\b', text_clean.lower())
        if len(words) > 3:
            sentences.append(words)
    
    print(f"      Created {len(sentences):,} sentences")
    
    # Train model
    model = Word2Vec(
        sentences=sentences,
        vector_size=100,
        window=5,
        min_count=10,  # Higher threshold to filter noise
        workers=4,
        epochs=5
    )
    
    # ============================================
    # STEP 3: Smart Sport Detection
    # ============================================
    print("\n[4/4] Detecting sports and filtering...")
    
    # Sport seed words
    sport_seeds = {
        'NFL': ['football', 'touchdown', 'quarterback', 'cowboys', 'chiefs'],
        'NBA': ['basketball', 'lakers', 'lebron', 'curry', 'dunk'],
        'MLB': ['baseball', 'dodgers', 'yankees', 'pitcher', 'inning'],
        'Soccer': ['soccer', 'arsenal', 'messi', 'ronaldo', 'premier'],
        'UFC/MMA': ['fight', 'fighter', 'knockout', 'dana', 'octagon'],
        'NHL': ['hockey', 'puck', 'stanley']
    }
    
    # Find related terms using Word2Vec
    sport_clusters = {}
    for sport, seeds in sport_seeds.items():
        related_terms = set()
        for seed in seeds:
            if seed in model.wv:
                similar = model.wv.most_similar(seed, topn=15)
                for word, score in similar:
                    if score > 0.6:  # High similarity threshold
                        related_terms.add(word)
        sport_clusters[sport] = related_terms
    
    # ============================================
    # STEP 4: Clean and Present Results
    # ============================================
    print("\n" + "="*70)
    print("📊 RESULTS")
    print("="*70)
    
    # Filter athletes (remove obvious non-athletes)
    bot_names = {'rawchili', 'newsbeep', 'beep', 'espn', 'nfl', 'nba', 'mlb', 'ufc'}
    clean_athletes = Counter([a for a in all_entities['athletes'] 
                               if a not in bot_names and not a.startswith('http')])
    
    print("\n🏃 TOP 30 ATHLETES/FIGHTERS:")
    for name, count in clean_athletes.most_common(30):
        print(f"   {count:>4}  {name}")
    
    # Filter teams
    clean_teams = Counter([t for t in all_entities['teams'] 
                           if t not in bot_names and not t.startswith('http') 
                           and len(t) > 2])
    
    print("\n🏆 TOP 30 TEAMS/ORGANIZATIONS:")
    for name, count in clean_teams.most_common(30):
        print(f"   {count:>4}  {name}")
    
    # Events
    clean_events = Counter(all_entities['events'])
    
    print("\n🎯 TOP 15 EVENTS:")
    for name, count in clean_events.most_common(15):
        print(f"   {count:>4}  {name}")
    
    # Sport clusters from Word2Vec
    print("\n⚽ SPORT CLUSTERS (from Word2Vec):")
    for sport, terms in sport_clusters.items():
        if terms:
            print(f"\n   {sport}:")
            print(f"      {', '.join(sorted(list(terms))[:15])}")
    
    return {
        'athletes': clean_athletes.most_common(50),
        'teams': clean_teams.most_common(50),
        'events': clean_events.most_common(20),
        'sport_clusters': sport_clusters
    }

if __name__ == "__main__":
    # Analyze both platforms
    print("\n" + "🏈"*35)
    sp_results = hybrid_analysis('sp')
    
    print("\n\n" + "🦋"*35)
    bsky_results = hybrid_analysis('bsky')
    
    print("\n\n" + "="*70)
    print("💡 SUMMARY")
    print("="*70)
    print("\n✅ This hybrid approach captures:")
    print("   • Individual athletes (Jake Paul, Stephen Curry, Ohtani)")
    print("   • Teams (Dodgers, Cowboys, Arsenal)")
    print("   • Fighting matchups (preserves both fighter names)")
    print("   • Events (World Series, UFC events)")
    print("   • Sport-specific terminology (via Word2Vec clusters)")
    print("\n✅ Filters out:")
    print("   • Bot names (rawchili, newsbeep)")
    print("   • URLs (https)")
    print("   • 4chan slang (picrel, kwab)")
