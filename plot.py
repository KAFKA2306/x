import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os
import json
from datetime import datetime

input_file = r'C:\Users\100ca\Downloads\twitter-2024-09-19-741b09a4d07b6875e14faaed1104872c99f2c1d9574872876fd3d2342d11756c\data\tweets.js'
output_dir = os.path.dirname(input_file)

with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read().replace('window.YTD.tweets.part0 = ', '')
tweets = json.loads(content)

df = pd.DataFrame([{
    'created_at': datetime.strptime(tweet['tweet']['created_at'], '%a %b %d %H:%M:%S +0000 %Y'),
    'text': tweet['tweet']['full_text'],
    'tweet_type': 'retweet' if tweet['tweet']['full_text'].startswith('RT @') else 'reply' if tweet['tweet']['full_text'].startswith('@') else 'original',
    'char_count': len(tweet['tweet']['full_text'])
} for tweet in tweets if 'full_text' in tweet['tweet']])

df['hour'] = df['created_at'].dt.hour
df['weekday'] = df['created_at'].dt.weekday
df['weekday_name'] = df['weekday'].map({0:'Mon', 1:'Tue', 2:'Wed', 3:'Thu', 4:'Fri', 5:'Sat', 6:'Sun'})
df['time_of_day'] = pd.cut(df['hour'], bins=[0, 6, 12, 18, 24], labels=['Night', 'Morning', 'Afternoon', 'Evening'])

plots = [
    ('tweets_by_hour.png', lambda: df.groupby('hour').size().plot(kind='bar')),
    ('tweets_by_hour_and_type.png', lambda: df.groupby(['hour', 'tweet_type']).size().unstack().plot(kind='bar', stacked=True)),
    ('tweets_by_weekday.png', lambda: df.groupby('weekday_name').size().plot(kind='bar')),
    ('tweets_by_weekday_and_time.png', lambda: df.groupby(['weekday_name', 'time_of_day']).size().unstack().plot(kind='bar', stacked=True)),
    ('tweet_length_distribution.png', lambda: sns.histplot(data=df, x='char_count', bins=50)),
    ('tweet_length_distribution_by_type.png', lambda: sns.histplot(data=df, x='char_count', hue='tweet_type', multiple='stack', bins=50)),
    ('tweet_type_proportion_by_hour.png', lambda: df.groupby(['hour', 'tweet_type']).size().unstack().plot(kind='bar', stacked=True))
]

for filename, plot_func in plots:
    plt.figure(figsize=(12, 6))
    ax = plot_func()
    plt.title(filename.replace('.png', '').replace('_', ' ').title())
    if isinstance(ax, plt.Axes):
        if 'tweet_type' in filename or 'time' in filename:
            ax.legend(title='Tweet Type' if 'type' in filename else 'Time of Day')
        plt.xlabel('Hour' if 'hour' in filename else 'Weekday')
        plt.ylabel('Number of Tweets')
    else:
        plt.xlabel('Tweet Length (characters)')
        plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()

print(f"Visualizations saved to {output_dir}")
