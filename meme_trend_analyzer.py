import tweepy
import os
from textblob import TextBlob
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Function to authenticate with Twitter API
def authenticate():
    # Replace with your actual API keys and tokens
    API_KEY = os.getenv("TWITTER_API_KEY")
    API_SECRET = os.getenv("TWITTER_API_SECRET")
    ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
    ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    return tweepy.API(auth)

# Function to fetch tweets from a list
def fetch_list_tweets(api, list_id):
    try:
        tweets = []
        for tweet in tweepy.Cursor(api.list_timeline, list_id=list_id, tweet_mode="extended").items(100):
            tweets.append(tweet.full_text)
        return tweets
    except Exception as e:
        print(f"Error fetching tweets: {e}")
        return []

# Function to analyze popular terms in tweets
def analyze_popular_terms(tweets):
    word_list = []
    for tweet in tweets:
        words = tweet.split()
        word_list.extend(words)

    counter = Counter(word_list)
    return counter.most_common(20)

# Function to generate a word cloud
def generate_word_cloud(tweets):
    text = " ".join(tweets)
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)

    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.show()

# Function to analyze sentiment of tweets
def analyze_sentiment(tweets):
    sentiment_scores = [TextBlob(tweet).sentiment.polarity for tweet in tweets]
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    return avg_sentiment

# Main function
def main():
    # Authenticate and initialize API
    api = authenticate()

    # Replace with the actual list ID from the provided link
    list_id = "1654276583606177793"

    print("Fetching tweets from the list...")
    tweets = fetch_list_tweets(api, list_id)

    if not tweets:
        print("No tweets found. Please check the list ID or API credentials.")
        return

    print("Analyzing popular terms...")
    popular_terms = analyze_popular_terms(tweets)
    print("Popular terms:")
    for term, count in popular_terms:
        print(f"{term}: {count}")

    print("Generating word cloud...")
    generate_word_cloud(tweets)

    print("Analyzing sentiment...")
    avg_sentiment = analyze_sentiment(tweets)
    print(f"Average sentiment score: {avg_sentiment:.2f}")

if __name__ == "__main__":
    main()
