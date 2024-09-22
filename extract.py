import json
import os
import csv
import re
from datetime import datetime

def clean_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'http\S+', '', text)
    return text

def format_timestamp(timestamp_str):
    dt = datetime.strptime(timestamp_str, '%a %b %d %H:%M:%S +0000 %Y')
    return dt.strftime('%Y-%m-%d %H:%M')

def extract_full_text(input_file):
    input_dir = os.path.dirname(input_file)
    output_file = os.path.join(input_dir, 'extracted_tweets.csv')
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read().replace('window.YTD.tweets.part0 = ', '')
    
    tweets = json.loads(content)
    
    with open(output_file, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['created_at', 'full_text']) 
        
        for tweet in tweets:
            if 'full_text' in tweet['tweet']:
                created_at = format_timestamp(tweet['tweet']['created_at'])
                full_text = clean_text(tweet['tweet']['full_text'])
                writer.writerow([created_at, full_text])

    return output_file

# 使用例
input_file = r'C:\Users\100ca\Downloads\twitter-2024-09-19-741b09a4d07b6875e14faaed1104872c99f2c1d9574872876fd3d2342d11756c\data\tweets.js'

output_file = extract_full_text(input_file)
print(output_file)
