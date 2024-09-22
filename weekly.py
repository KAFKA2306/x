import json
import os
import re
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# Load tweets from a file
def load_tweets(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.loads(f.read().replace('window.YTD.tweets.part0 = ', ''))

# Clean tweet text
def clean_text(text):
    return re.sub(r'http\S+|\s+', ' ', text).strip()

# Format timestamp
def format_timestamp(timestamp_str):
    return datetime.strptime(timestamp_str, '%a %b %d %H:%M:%S +0000 %Y')

# Process tweets into a DataFrame
def process_tweets(tweets):
    df = pd.DataFrame([{
        'created_at': format_timestamp(tweet['tweet']['created_at']),
        'is_original': not tweet['tweet']['full_text'].startswith(('RT @', '@')),
        'is_retweet': tweet['tweet']['full_text'].startswith('RT @'),
        'is_reply': tweet['tweet']['full_text'].startswith('@')
    } for tweet in tweets if 'full_text' in tweet['tweet']])
    return df

# Analyze tweets on a weekly basis
def weekly_analysis(df):
    # Group by week and sum up the different types of tweets
    df = df.set_index('created_at').resample('W').sum()
    df['total_tweets'] = df.sum(axis=1)
    return df

# Analyze tweets on a monthly basis
def monthly_analysis(df):
    # Group by month and sum up the different types of tweets
    df = df.set_index('created_at').resample('M').sum()
    df['total_tweets'] = df.sum(axis=1)
    return df

# Plot stacked bar chart with custom axis labels
def plot_stats(df, output_dir, title, filename, freq='W'):
    # Plotting
    ax = df[['is_original', 'is_retweet', 'is_reply']].plot(
        kind='bar', 
        stacked=True, 
        figsize=(10, 6),
        color=['#1f77b4', '#ff7f0e', '#2ca02c']
    )

    # Set title and axis labels
    ax.set_title(title)
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Tweets')

    # Set x-axis ticks to display every nth label (adjust for readability)
    num_labels = len(df.index)  # Total number of periods
    step = max(1, num_labels // 10)  # Show 1 label per 10 periods (adjust as necessary)
    ax.set_xticks(range(0, num_labels, step))
    
    # Formatting dates based on the frequency (Weekly or Monthly)
    date_format = '%Y-%m-%d' if freq == 'W' else '%Y-%m'
    ax.set_xticklabels(df.index[::step].strftime(date_format), rotation=45, ha='right')

    # Add a legend
    ax.legend(['Original', 'Retweet', 'Reply'], loc='upper right')

    # Save the plot to a file
    output_image_file = os.path.join(output_dir, filename)
    plt.tight_layout()
    plt.savefig(output_image_file)
    print(f"Plot saved to {output_image_file}")
    plt.close()

# Main function
def main(input_file, output_dir):
    tweets = load_tweets(input_file)
    df = process_tweets(tweets)
    
    # Weekly analysis
    weekly_stats = weekly_analysis(df)
    output_weekly_file = os.path.join(output_dir, 'weekly_twitter_stats.csv')
    weekly_stats.to_csv(output_weekly_file)
    print(f"Weekly statistics saved to {output_weekly_file}")
    
    # Plot weekly stats
    plot_stats(weekly_stats, output_dir, 'Weekly Tweet Activity', 'weekly_tweet_activity.png', freq='W')
    
    # Monthly analysis
    monthly_stats = monthly_analysis(df)
    output_monthly_file = os.path.join(output_dir, 'monthly_twitter_stats.csv')
    monthly_stats.to_csv(output_monthly_file)
    print(f"Monthly statistics saved to {output_monthly_file}")
    
    # Plot monthly stats
    plot_stats(monthly_stats, output_dir, 'Monthly Tweet Activity', 'monthly_tweet_activity.png', freq='M')

if __name__ == "__main__":
    input_file = r'C:\Users\100ca\Downloads\twitter-2024-09-19-741b09a4d07b6875e14faaed1104872c99f2c1d9574872876fd3d2342d11756c\data\tweets.js'
    output_dir = os.path.dirname(input_file)
    main(input_file, output_dir)
