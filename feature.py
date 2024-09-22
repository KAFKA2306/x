import json
import os
import csv
import re
from datetime import datetime
import pandas as pd
import numpy as np

def clean_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'http\S+', '', text)
    return text

def format_timestamp(timestamp_str):
    dt = datetime.strptime(timestamp_str, '%a %b %d %H:%M:%S +0000 %Y')
    return dt

def extract_features(input_file):
    input_dir = os.path.dirname(input_file)
    output_file = os.path.join(input_dir, 'tweet_features_comprehensive.csv')
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read().replace('window.YTD.tweets.part0 = ', '')
    
    tweets = json.loads(content)
    
    features = []
    for tweet in tweets:
        if 'full_text' in tweet['tweet']:
            dt = format_timestamp(tweet['tweet']['created_at'])
            text = clean_text(tweet['tweet']['full_text'])
            
            feature = {
                'created_at': dt.strftime('%Y-%m-%d %H:%M'),
                'year': dt.year,
                'month': dt.month,
                'day': dt.day,
                'hour': dt.hour,
                'minute': dt.minute,
                'weekday': dt.weekday(),
                'text': text,
                'char_count': len(text),
                'word_count': len(text.split()),
                'mention_count': text.count('@'),
                'hashtag_count': text.count('#'),
                'url_count': text.count('http'),
                'exclamation_count': text.count('!'),
                'question_count': text.count('?'),
                'is_retweet': 1 if text.startswith('RT @') else 0,
                'is_reply': 1 if text.startswith('@') else 0,
            }
            
            features.append(feature)
    
    df = pd.DataFrame(features)
    
    # Time-related features
    df['is_weekend'] = df['weekday'].apply(lambda x: 1 if x >= 5 else 0)
    df['day_type'] = df['weekday'].apply(lambda x: 'weekend' if x >= 5 else 'weekday')
    df['time_category'] = pd.cut(df['hour'], 
                                 bins=[-0.1, 6, 12, 18, 23.1], 
                                 labels=['night', 'morning', 'afternoon', 'evening'])
    df['season'] = pd.cut(df['month'], 
                          bins=[-0.1, 3, 6, 9, 12.1], 
                          labels=['winter', 'spring', 'summer', 'autumn'])
    
    # Tweet content features
    df['tweet_length_category'] = pd.cut(df['char_count'], 
                                         bins=[-0.1, 20, 50, 100, 277.1], 
                                         labels=['short', 'medium', 'long', 'very_long'])
    df['tweet_type'] = df.apply(lambda row: 'retweet' if row['is_retweet'] else ('reply' if row['is_reply'] else 'original'), axis=1)
    df['has_mention'] = df['mention_count'].apply(lambda x: 1 if x > 0 else 0)
    df['has_hashtag'] = df['hashtag_count'].apply(lambda x: 1 if x > 0 else 0)
    df['has_url'] = df['url_count'].apply(lambda x: 1 if x > 0 else 0)
    df['text_without_mentions'] = df['text'].apply(lambda x: re.sub(r'@\w+', '', x).strip())
    df['capital_letter_ratio'] = df['text'].apply(lambda x: sum(1 for c in x if c.isupper()) / len(x) if len(x) > 0 else 0)
    df['unique_word_ratio'] = df['text'].apply(lambda x: len(set(x.split())) / len(x.split()) if len(x.split()) > 0 else 0)
    
    # Engagement features
    df['mention_category'] = pd.cut(df['mention_count'], 
                                    bins=[-0.1, 0, 1, 2, float('inf')], 
                                    labels=['none', 'single', 'double', 'multiple'])
    df['hashtag_category'] = pd.cut(df['hashtag_count'], 
                                    bins=[-0.1, 0, 1, float('inf')], 
                                    labels=['none', 'single', 'multiple'])
    df['punctuation_intensity'] = df.apply(lambda row: 'high' if row['exclamation_count'] + row['question_count'] > 1 else 'low', axis=1)
    
    # Activity features
    df['date'] = pd.to_datetime(df['created_at']).dt.date
    tweet_frequency = df.groupby('date')['text'].count()
    df['tweet_frequency'] = df['date'].map(tweet_frequency)
    df['tweet_frequency_category'] = pd.cut(df['tweet_frequency'], 
                                            bins=[0, 5, 10, float('inf')], 
                                            labels=['low', 'medium', 'high'])
    
    hourly_tweet_count = df.groupby('hour')['text'].count()
    df['tweet_density'] = df['hour'].map(hourly_tweet_count)
    df['tweet_density_category'] = pd.cut(df['tweet_density'], 
                                          bins=[0, hourly_tweet_count.quantile(0.33), 
                                                hourly_tweet_count.quantile(0.67), float('inf')], 
                                          labels=['low', 'medium', 'high'])
    
    # Derived features
    df['engagement_score'] = df['mention_count'] + df['hashtag_count']
    df['engagement_category'] = pd.cut(df['engagement_score'], 
                                       bins=[-0.1, 0, 1, 2, float('inf')], 
                                       labels=['none', 'low', 'medium', 'high'])
    df['tweet_complexity'] = df.apply(lambda row: 'complex' if row['char_count'] > 50 and row['unique_word_ratio'] > 0.8 else 'simple', axis=1)
    
    df.to_csv(output_file, index=False, encoding='utf-8')
    return df, output_file

def print_statistics(df):
    print("Feature Statistics:")
    print("-" * 50)
    
    numeric_columns = ['year', 'month', 'day', 'hour', 'minute', 'weekday', 'char_count', 'word_count', 
                       'mention_count', 'hashtag_count', 'url_count', 'exclamation_count', 'question_count', 
                       'tweet_frequency', 'tweet_density', 'engagement_score']
    for column in numeric_columns:
        stats = df[column].describe()
        print(f"{column}:")
        print(f"  Mean: {stats['mean']:.2f}")
        print(f"  Median: {df[column].median():.2f}")
        print(f"  Std Dev: {stats['std']:.2f}")
        print(f"  Min: {stats['min']:.2f}")
        print(f"  Max: {stats['max']:.2f}")
        print()
    
    categorical_columns = ['is_weekend', 'is_retweet', 'is_reply', 'has_mention', 'has_hashtag', 'has_url',
                           'day_type', 'time_category', 'season', 'tweet_length_category', 'tweet_type',
                           'mention_category', 'hashtag_category', 'punctuation_intensity',
                           'tweet_frequency_category', 'tweet_density_category', 'engagement_category',
                           'tweet_complexity']
    for column in categorical_columns:
        value_counts = df[column].value_counts(normalize=True)
        print(f"{column}:")
        for value, count in value_counts.items():
            print(f"  {value}: {count:.2%}")
        print()

# Usage example
input_file = r'C:\Users\100ca\Downloads\twitter-2024-09-19-741b09a4d07b6875e14faaed1104872c99f2c1d9574872876fd3d2342d11756c\data\tweets.js'

df, output_file = extract_features(input_file)
print(f"Feature extraction completed. Data saved to {output_file}")
print_statistics(df)
