# Twitter Data Analysis Tool

A Python-based tool for extracting, analyzing, and visualizing Twitter data.

## Structure

```
twitter-analysis/
│
├── extract.py     # Extracts data from Twitter JSON file
├── feature.py     # Generates features from extracted data
├── plot.py        # Creates visualizations
│
├── data/
│   ├── tweet_features_comprehensive.csv
│   ├── tweet_length_distribution_by_type.png
│   ├── tweet_type_proportion_by_hour.png
│   └── tweets_by_weekday_and_time.png
│
└── README.md
```

## Usage

1. Run `extract.py` to process the Twitter JSON file.
2. Execute `feature.py` to generate comprehensive tweet features.
3. Use `plot.py` to create visualizations.

## Sample Visualizations

### Tweet Length Distribution By Type
![Tweet Length Distribution By Type](/tweet_length_distribution_by_type.png)

### Tweet Type Proportion By Hour
![Tweet Type Proportion By Hour](/tweet_type_proportion_by_hour.png)

### Tweets By Weekday And Time
![Tweets By Weekday And Time](/tweets_by_weekday_and_time.png)

