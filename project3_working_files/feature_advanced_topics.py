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

# ============================================
# METHOD 1: Named Entity Recognition (NER)
# ============================================
def analyze_with_ner(platform):
    """Extract named entities (people, organizations, events)."""
    print(f"\n{'='*60}")
    print(f"METHOD 1: Named Entity Recognition (NER) - {platform.upper()}")
    print(f"{'='*60}")
    
    print("Loading spaCy model...")
    nlp = spacy.load('en_core_web_sm')
    
    print("Loading posts...")
    texts = load_platform_text(platform)
    print(f"Loaded {len(texts):,} posts")
    
    # Sample for speed (NER is slow on full dataset)
    sample_size = min(5000, len(texts))
    texts_sample = texts[:sample_size]
    print(f"Processing {sample_size:,} posts for NER...")
    
    # Extract entities
    people = []
    orgs = []
    events = []
    
    for i, text in enumerate(texts_sample):
        if i % 1000 == 0:
            print(f"  Processed {i:,}/{sample_size:,}...")
        
        doc = nlp(text[:1000])  # Limit text length for speed
        
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                people.append(ent.text.lower())
            elif ent.label_ == 'ORG':
                orgs.append(ent.text.lower())
            elif ent.label_ == 'EVENT':
                events.append(ent.text.lower())
    
    print("\n📊 NER RESULTS:")
    print(f"\nTop 20 People/Players:")
    people_counts = Counter(people).most_common(20)
    for name, count in people_counts:
        print(f"  {name}: {count}")
    
    print(f"\nTop 20 Organizations/Teams:")
    org_counts = Counter(orgs).most_common(20)
    for name, count in org_counts:
        print(f"  {name}: {count}")
    
    if events:
        print(f"\nTop Events:")
        event_counts = Counter(events).most_common(10)
        for name, count in event_counts:
            print(f"  {name}: {count}")
    
    return {
        'people': people_counts,
        'orgs': org_counts,
        'events': event_counts if events else []
    }

# ============================================
# METHOD 2: Word2Vec
# ============================================
def analyze_with_word2vec(platform):
    """Train Word2Vec to find similar/related terms."""
    print(f"\n{'='*60}")
    print(f"METHOD 2: Word2Vec - {platform.upper()}")
    print(f"{'='*60}")
    
    print("Loading posts...")
    texts = load_platform_text(platform)
    print(f"Loaded {len(texts):,} posts")
    
    # Tokenize
    print("Tokenizing...")
    sentences = []
    for text in texts:
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        if len(words) > 3:  # Only sentences with 3+ words
            sentences.append(words)
    
    print(f"Created {len(sentences):,} sentences")
    
    # Train Word2Vec
    print("Training Word2Vec model (this takes 1-2 minutes)...")
    model = Word2Vec(
        sentences=sentences,
        vector_size=100,
        window=5,
        min_count=5,
        workers=4,
        epochs=5
    )
    
    print("\n📊 WORD2VEC RESULTS:")
    
    # Find similar words to sports terms
    sport_seeds = ['football', 'basketball', 'baseball', 'soccer', 'game', 'team', 'player']
    
    print("\nSimilar words to key sports terms:")
    for seed in sport_seeds:
        if seed in model.wv:
            similar = model.wv.most_similar(seed, topn=10)
            print(f"\n  '{seed}' is similar to:")
            for word, score in similar:
                print(f"    {word} ({score:.3f})")
    
    # Get most common sport-related words
    print("\n\nMost frequent sport-related vocabulary:")
    vocab_counts = [(word, model.wv.get_vecattr(word, "count")) 
                    for word in model.wv.index_to_key[:100]]
    
    # Filter for likely sports terms
    sport_words = []
    stopwords = {'game', 'team', 'play', 'season', 'year', 'time', 'good', 'better', 'last', 'first'}
    for word, count in vocab_counts:
        if word not in stopwords and len(word) > 4:
            sport_words.append((word, count))
    
    print("\nTop 30 sport-related words:")
    for word, count in sport_words[:30]:
        print(f"  {word}: {count}")
    
    return {
        'model': model,
        'vocab': vocab_counts,
        'sport_words': sport_words
    }

if __name__ == "__main__":
    # Test on /sp/
    print("\n" + "="*60)
    print("ANALYZING /sp/ (Sports Board)")
    print("="*60)
    
    ner_sp = analyze_with_ner('sp')
    w2v_sp = analyze_with_word2vec('sp')
    
    # Test on Bluesky
    print("\n\n" + "="*60)
    print("ANALYZING BLUESKY")
    print("="*60)
    
    ner_bsky = analyze_with_ner('bsky')
    w2v_bsky = analyze_with_word2vec('bsky')
    
    # Comparison
    print("\n\n" + "="*60)
    print("COMPARISON: NER vs Word2Vec")
    print("="*60)
    print("\n✅ NER Advantages:")
    print("  - Finds actual names (Patrick Mahomes, Kansas City Chiefs)")
    print("  - Identifies people vs organizations")
    print("  - Great for 'who/what' analysis")
    
    print("\n✅ Word2Vec Advantages:")
    print("  - Finds semantic relationships (mahomes → brady → quarterback)")
    print("  - Discovers slang and informal terms")
    print("  - Shows how words are used together")
    
    print("\n💡 Recommendation:")
    print("  Use BOTH! NER for entities, Word2Vec for topics/themes")
