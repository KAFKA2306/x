import json
import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

def analyze_tweets(tweets):
    texts = [re.sub(r'@\w+|http\S+|\bRT\b|[^a-zA-Z\s]', '', tweet['full_text']).lower().split() for tweet in tweets]
    
    vectorizer = TfidfVectorizer(max_features=30, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([' '.join(text) for text in texts])
    
    return {
        'total_tweets': len(tweets),
        'avg_tweet_length': sum(len(text) for text in texts) / len(tweets),
        'top_words': sorted(zip(vectorizer.get_feature_names_out(), tfidf_matrix.sum(axis=0).tolist()[0]), key=lambda x: x[1], reverse=True),
        'top_hashtags': Counter([tag['text'] for tweet in tweets for tag in tweet.get('entities', {}).get('hashtags', [])]).most_common(30),
        'top_mentioned_users': Counter([mention['screen_name'] for tweet in tweets for mention in tweet.get('entities', {}).get('user_mentions', [])]).most_common(30)
    }

def main(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        tweets = json.loads(f.read().replace('window.YTD.tweets.part0 = ', ''))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analyze_tweets([tweet['tweet'] for tweet in tweets]), f, ensure_ascii=False, indent=2)
    
    print(f"Analysis results saved to {output_file}")

if __name__ == "__main__":
    main(r'C:\Users\100ca\Downloads\twitter-2024-09-19-741b09a4d07b6875e14faaed1104872c99f2c1d9574872876fd3d2342d11756c\data\tweets.js',
         r'C:\Users\100ca\Downloads\twitter-2024-09-19-741b09a4d07b6875e14faaed1104872c99f2c1d9574872876fd3d2342d11756c\data\tfidf.json')
