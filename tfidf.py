import json, os, csv, re, sqlite3
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import pandas as pd  # Import pandas for data handling

# Clean tweet text: remove URLs, mentions, hashtags
def clean_text(text):
    text = re.sub(r'http\S+|@\S+|#\S+', '', text)  # Remove URLs, mentions, hashtags
    return re.sub(r'\s+', ' ', text).strip()

# Format timestamp
def format_timestamp(ts):
    return datetime.strptime(ts, '%a %b %d %H:%M:%S +0000 %Y').strftime('%Y-%m-%d %H:%M')

# TF-IDF-based summary extraction
def extract_summary(texts, num_sentences=3):
    if not texts or all(len(text.strip()) == 0 for text in texts):
        return ''
    
    vectorizer = TfidfVectorizer(stop_words='english')  # Use English stop words filtering
    X = vectorizer.fit_transform(texts).sum(axis=1)
    
    if X.size == 0:
        return ' '.join(texts[:num_sentences])  # Fallback to first few sentences
    
    # Sort by TF-IDF scores and return top-ranked sentences
    return ' '.join([s for _, s in sorted(zip(X, texts), reverse=True)[:num_sentences]])

# Save to SQLite database
def save_to_db(db_path, data):
    with sqlite3.connect(db_path) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS summaries (id INTEGER PRIMARY KEY, summary TEXT)')
        conn.executemany('INSERT INTO summaries (summary) VALUES (?)', [(s,) for s in data])
        conn.commit()

# Extract full text and summarize tweets
def extract_full_text(input_file):
    # Get the directory of the input file to save the output there
    output_dir = os.path.dirname(input_file)

    # Paths for CSV and database output
    csv_file = os.path.join(output_dir, 'tweets.csv')
    db_file = os.path.join(output_dir, 'summaries.db')

    with open(input_file, 'r', encoding='utf-8') as f:
        tweets = json.loads(f.read().replace('window.YTD.tweets.part0 = ', ''))
    
    all_texts = []
    tweet_data = []

    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['created_at', 'full_text', 'summary'])

        for tweet in tweets:
            text = tweet['tweet'].get('full_text')
            if text:
                full_text = clean_text(text)
                if len(full_text) > 50:  # Filter tweets with more than 50 characters
                    all_texts.append(full_text)
                    summary = extract_summary([full_text])
                    writer.writerow([format_timestamp(tweet['tweet']['created_at']), full_text, summary])
                    tweet_data.append({
                        'created_at': format_timestamp(tweet['tweet']['created_at']),
                        'full_text': full_text,
                        'summary': summary
                    })

    save_to_db(db_file, all_texts)
    
    # Create a DataFrame for the results and print it
    df = pd.DataFrame(tweet_data)
    print(df)  # Display the DataFrame
    return all_texts

# Function to print statistics
def tweet_stats(texts):
    total_tweets = len(texts)
    avg_length = np.mean([len(text.split()) for text in texts])
    
    print(f"Total tweets processed: {total_tweets}")
    print(f"Average tweet length: {avg_length:.2f} words")

# Example usage
input_file = r'C:\Users\100ca\Downloads\twitter-2024-09-19-741b09a4d07b6875e14faaed1104872c99f2c1d9574872876fd3d2342d11756c\data\tweets.js'
all_tweets = extract_full_text(input_file)
tweet_stats(all_tweets)

#            created_at                                          full_text                                            summary
#0     2024-09-19 14:29  複雑怪奇ですねー。 米ターミナルレート3%で下げ幅余地が意外と少ないシナリオ… 米株とゴール...  複雑怪奇ですねー。 米ターミナルレート3%で下げ幅余地が意外と少ないシナリオ… 米株とゴール...
#2789  2024-05-25 20:51  RT 第1回大会終わりました！すごい良い戦い見れてよかったです！ぼくは寝ます！他のことは明日...  RT 第1回大会終わりました！すごい良い戦い見れてよかったです！ぼくは寝ます！他のことは明日...
