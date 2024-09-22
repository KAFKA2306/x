import json
import os
import re
from datetime import datetime
from collections import Counter
import numpy as np
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer

def clean_text(text):
    text = re.sub(r'http\S+|@\S+|#\S+', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def format_timestamp(ts):
    return datetime.strptime(ts, '%a %b %d %H:%M:%S +0000 %Y').strftime('%Y-%m-%d %H:%M')

def simple_tokenize(text):
    return [word for word in re.findall(r'\w+', text) if len(word) > 1]

def extract_summary(texts, num_sentences=3):
    if not texts or all(len(text.strip()) == 0 for text in texts):
        return ''
    
    vectorizer = TfidfVectorizer(tokenizer=simple_tokenize)
    X = vectorizer.fit_transform(texts).sum(axis=1)
    
    if X.size == 0:
        return ' '.join(texts[:num_sentences])
    
    return ' '.join([s for _, s in sorted(zip(X.tolist(), texts), key=lambda x: x[0], reverse=True)[:num_sentences]])

def extract_full_text(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        tweets = json.loads(f.read().replace('window.YTD.tweets.part0 = ', ''))
    
    all_texts = []
    tweet_data = []
    
    for tweet in tweets:
        text = tweet['tweet'].get('full_text')
        if text:
            full_text = clean_text(text)
            if len(full_text) > 50:
                all_texts.append(full_text)
                summary = extract_summary([full_text])
                tweet_data.append({
                    'created_at': format_timestamp(tweet['tweet']['created_at']),
                    'full_text': full_text,
                    'summary': summary
                })
    
    df = pd.DataFrame(tweet_data)
    return df, all_texts

def analyze_tweets(df, texts):
    total_tweets = len(texts)
    avg_length = np.mean([len(text) for text in texts])
    avg_words = np.mean([len(simple_tokenize(text)) for text in texts])
    
    # 単語頻度の計算
    word_freq = Counter([word for text in texts for word in simple_tokenize(text) if len(word) > 1])
    top_words = word_freq.most_common(20)
    
    # 時系列分析
    df['created_at'] = pd.to_datetime(df['created_at'])
    tweets_per_day = df.resample('D', on='created_at').size()
    
    # ワードクラウドの作成
    wordcloud = WordCloud(width=800, height=400, background_color='white', font_path=r'C:\Windows\Fonts\meiryo.ttc').generate_from_frequencies(word_freq)
    
    return {
        'total_tweets': total_tweets,
        'avg_length': avg_length,
        'avg_words': avg_words,
        'top_words': top_words,
        'tweets_per_day': tweets_per_day,
        'wordcloud': wordcloud
    }

def print_analysis_summary(analysis):
    print(f"ツイート総数: {analysis['total_tweets']}")
    print(f"平均文字数: {analysis['avg_length']:.2f}")
    print(f"平均単語数: {analysis['avg_words']:.2f}")
    
    print("\n頻出単語トップ20:")
    for word, count in analysis['top_words']:
        print(f"{word}: {count}")
    
    print("\n日別ツイート数:")
    print(analysis['tweets_per_day'].to_string())
    
    # ワードクラウドの保存
    plt.figure(figsize=(10, 5))
    plt.imshow(analysis['wordcloud'], interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig('wordcloud.png')
    print("\nワードクラウドを 'wordcloud.png' として保存しました。")

def main():
    input_file = r'C:\Users\100ca\Downloads\twitter-2024-09-19-741b09a4d07b6875e14faaed1104872c99f2c1d9574872876fd3d2342d11756c\data\tweets.js'
    
    if not os.path.exists(input_file):
        print(f"Error: File not found at {input_file}")
        return
    
    df, all_tweets = extract_full_text(input_file)
    analysis = analyze_tweets(df, all_tweets)
    print_analysis_summary(analysis)
    
    print("\n処理が完了しました。")

if __name__ == "__main__":
    main()
