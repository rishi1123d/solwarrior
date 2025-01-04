#!/usr/bin/env python3

import os
import time
import json
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Tweepy for Twitter
import tweepy

# Web3 for EVM
from web3 import Web3
from eth_utils import to_wei

# Telegram
from telegram import Bot
from telegram.ext import Updater

# ----------------------------------------------------------
# 1. Configuration & Environment Variables
# ----------------------------------------------------------

# --- Twitter ---
CONSUMER_KEY = os.getenv('TWITTER_API_KEY')
CONSUMER_SECRET = os.getenv('TWITTER_API_SECRET')
ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_SECRET')
BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# --- GMGN & Pumpfun (Placeholder URLs) ---
GMGN_URL = os.getenv('GMGN_URL', 'https://example.com/gmgn/new-tokens')
PUMPFUN_URL = os.getenv('PUMPFUN_URL', 'https://example.com/pumpfun/new-coins')

# --- TweetScout (Placeholder) ---
TWEETSCOUT_TOKEN = os.getenv('TWEETSCOUT_TOKEN', None)
TWEETSCOUT_BASE_URL = "https://app.tweetscout.io"
TWEETSCOUT_SEARCH_URL = f"{TWEETSCOUT_BASE_URL}/search"

# --- RugCheck (Placeholder) ---
RUGCHECK_URL = os.getenv('RUGCHECK_URL', 'https://rugcheck.xyz/check')

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# --- Web3 DEX Purchase (Example: Uniswap-like) ---
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("RPC_URL", "https://mainnet.infura.io/v3/your-project-id")

# Router address & ABI are placeholders
DEX_ROUTER_ADDRESS = "0x1111111254EEB25477B68fb85Ed929f73A960582"  # Example only
DEX_ROUTER_ABI = """
[
  {
    "name": "swapExactTokensForTokens",
    "type": "function",
    "inputs": [
      {"name":"amountIn","type":"uint256"},
      {"name":"amountOutMin","type":"uint256"},
      {"name":"path","type":"address[]"},
      {"name":"to","type":"address"},
      {"name":"deadline","type":"uint256"}
    ],
    "outputs": [{"name":"","type":"uint256[]"}],
    "stateMutability": "nonpayable"
  }
]
"""

# For demonstration, we swap from WETH to the target token
TOKEN_IN = "0xC02aaa39b223FE8D0A0e5C4F27ead9083C756Cc2"  # WETH mainnet example

# Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Initialize Twitter Client (if credentials exist)
client = None
if BEARER_TOKEN:
    client = tweepy.Client(
        bearer_token=BEARER_TOKEN,
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET
    )

# Initialize Telegram
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(RPC_URL)) if RPC_URL else None

# ----------------------------------------------------------
# 2. Helper Functions
# ----------------------------------------------------------

############################
# 2.1 - Twitter Meme Search
############################

def get_tweet_popularity(tweet_data):
    """
    Simple popularity score from public_metrics.
    """
    metrics = tweet_data.get('public_metrics', {})
    retweet_count = metrics.get('retweet_count', 0)
    reply_count = metrics.get('reply_count', 0)
    like_count = metrics.get('like_count', 0)
    quote_count = metrics.get('quote_count', 0)

    popularity_score = (2 * retweet_count) + like_count + reply_count + (2 * quote_count)
    return popularity_score

def references_news(tweet_data):
    """
    Very naive approach to detecting news links.
    """
    NEWS_DOMAINS = [
        'cnn.com', 'nytimes.com', 'bbc.co', 'foxnews.com', 'washingtonpost.com',
        'theguardian.com', 'reuters.com', 'nbcnews.com', 'abcnews.go.com'
    ]
    if 'entities' in tweet_data and 'urls' in tweet_data['entities']:
        for url_info in tweet_data['entities']['urls']:
            expanded_url = url_info.get('expanded_url', '')
            for domain in NEWS_DOMAINS:
                if domain in expanded_url.lower():
                    return True
    return False

def search_memes(query="meme OR memes -is:retweet", max_results=20):
    """
    Search for tweets about memes.
    """
    if not client:
        print("Twitter client not initialized. Check your credentials.")
        return []

    tweets_data = []
    response = client.search_recent_tweets(
        query=query,
        tweet_fields=["public_metrics", "entities", "created_at"],
        expansions=["author_id"],
        max_results=max_results
    )

    if response.data:
        for tweet in response.data:
            popularity = get_tweet_popularity(tweet.data)
            is_news = references_news(tweet.data)
            tweets_data.append({
                "id": tweet.id,
                "text": tweet.text,
                "created_at": tweet.created_at,
                "popularity_score": popularity,
                "is_news": is_news
            })

    return tweets_data

############################
# 2.2 - GMGN & Pumpfun
############################

def get_new_tokens_from_gmgn():
    """
    Retrieve newly listed tokens from GMGN (placeholder).
    """
    try:
        r = requests.get(GMGN_URL, headers=HEADERS, timeout=10)
        r.raise_for_status()
        # If JSON:
        # data = r.json()
        # parse accordingly
        soup = BeautifulSoup(r.text, "html.parser")

        new_tokens = []
        # Example placeholder parsing
        token_cards = soup.find_all("div", class_="token-card")
        for card in token_cards:
            name_tag = card.find("h3", class_="token-name")
            symbol_tag = card.find("span", class_="token-symbol")
            contract_link = card.find("a", class_="contract-link")
            if name_tag and contract_link:
                new_tokens.append({
                    "source": "GMGN",
                    "name": name_tag.get_text(strip=True),
                    "symbol": symbol_tag.get_text(strip=True) if symbol_tag else "",
                    "contract": contract_link.get("href", "")
                })
        return new_tokens

    except Exception as e:
        print(f"[GMGN] Error: {e}")
        return []

def get_new_tokens_from_pumpfun():
    """
    Retrieve newly listed tokens from Pumpfun (placeholder).
    """
    try:
        r = requests.get(PUMPFUN_URL, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        new_tokens = []
        coin_listings = soup.find_all("div", class_="coin-listing")
        for listing in coin_listings:
            name_tag = listing.find("h4", class_="coin-name")
            symbol_tag = listing.find("span", class_="coin-symbol")
            contract_link = listing.find("a", class_="contract-address")
            if name_tag and contract_link:
                new_tokens.append({
                    "source": "Pumpfun",
                    "name": name_tag.get_text(strip=True),
                    "symbol": symbol_tag.get_text(strip=True) if symbol_tag else "",
                    "contract": contract_link.get("href", "")
                })
        return new_tokens

    except Exception as e:
        print(f"[Pumpfun] Error: {e}")
        return []

def aggregate_tokens():
    """
    Combined new tokens from GMGN & Pumpfun.
    """
    gmgn = get_new_tokens_from_gmgn()
    pumpfun = get_new_tokens_from_pumpfun()
    return gmgn + pumpfun

############################
# 2.3 - TweetScout Memecoin Search
############################

def search_memecoin_account_on_tweetscout(memecoin_handle):
    """
    Searches for a memecoin X account on TweetScout (placeholder).
    """
    if not TWEETSCOUT_TOKEN:
        print("No TweetScout token provided. This is placeholder logic.")
        return []

    session = requests.Session()
    session.headers.update(HEADERS)
    # Possibly add Bearer or cookie if needed:
    session.headers.update({"Authorization": f"Bearer {TWEETSCOUT_TOKEN}"})

    payload = {"query": memecoin_handle}

    try:
        # Hypothetical GET request
        resp = session.get(TWEETSCOUT_SEARCH_URL, params=payload, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        items = soup.find_all("div", class_="search-result-item")
        for item in items:
            handle_tag = item.find("span", class_="account-handle")
            followers_tag = item.find("span", class_="account-followers")
            tweets_tag = item.find("span", class_="account-tweets")

            if handle_tag and memecoin_handle.lower() in handle_tag.text.lower():
                results.append({
                    "handle": handle_tag.text.strip(),
                    "followers": followers_tag.text.strip() if followers_tag else "N/A",
                    "tweets": tweets_tag.text.strip() if tweets_tag else "N/A"
                })

        return results

    except Exception as e:
        print(f"[TweetScout Error]: {e}")
        return []

############################
# 2.4 - RugCheck
############################

def check_contract_rugcheck(contract_address):
    """
    Checks the contract via rugcheck.xyz (placeholder).
    """
    try:
        params = {"contract": contract_address}
        r = requests.get(RUGCHECK_URL, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()

        # If JSON is returned, parse it. If HTML, parse with BS4.
        soup = BeautifulSoup(r.text, "html.parser")
        score_tag = soup.find("div", id="result-score")
        status_tag = soup.find("span", id="result-status")
        additional_info_tag = soup.find("div", class_="additional-info")

        score_text = score_tag.get_text(strip=True) if score_tag else "N/A"
        status_text = status_tag.get_text(strip=True) if status_tag else "N/A"
        details_text = additional_info_tag.get_text(strip=True) if additional_info_tag else "N/A"

        return {
            "contract_address": contract_address,
            "score": score_text,
            "status": status_text,
            "details": details_text
        }

    except Exception as e:
        print(f"[RugCheck Error] for {contract_address}: {e}")
        return {
            "contract_address": contract_address,
            "error": str(e)
        }

############################
# 2.5 - Automatic Purchase & Telegram Notification
############################

def send_telegram_message(message: str):
    """
    Sends a message to the configured Telegram chat.
    """
    if not telegram_bot:
        print("Telegram bot not configured. Skipping message send.")
        return
    try:
        telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def buy_token(contract_address: str, amount_in_wei: int):
    """
    Executes a token purchase on a DEX (placeholder Uniswap-like).
    """
    if not web3:
        raise ValueError("Web3 not initialized. Check your RPC_URL.")

    account = web3.eth.account.privateKeyToAccount(PRIVATE_KEY)
    router = web3.eth.contract(address=DEX_ROUTER_ADDRESS, abi=DEX_ROUTER_ABI)

    nonce = web3.eth.get_transaction_count(account.address)

    path = [TOKEN_IN, contract_address]
    deadline = web3.eth.get_block('latest')['timestamp'] + 300

    tx = router.functions.swapExactTokensForTokens(
        amount_in_wei,
        0,  # amountOutMin (for demo)
        path,
        account.address,
        deadline
    ).buildTransaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 300000,  # placeholder
        'gasPrice': web3.toWei('10', 'gwei')
    })

    signed_tx = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt


# ----------------------------------------------------------
# 3. Main Demonstration Flow
# ----------------------------------------------------------

def main():
    """
    Demonstrates a sequence:
      1) Search for meme tweets (Twitter)
      2) Fetch new tokens (GMGN + Pumpfun)
      3) Check a memecoin handle on TweetScout
      4) Rugcheck a token & buy if 'safe'
      5) Notify Telegram on buy
    Adjust or break into subcommands as needed.
    """

    print("\n--- 1) Searching for Meme Tweets ---")
    memes = search_memes("funny meme -is:retweet", max_results=5)
    for i, tweet_info in enumerate(memes, start=1):
        print(f"{i}. {tweet_info.get('text', '')[:80]}...")
        print(f"   Popularity Score: {tweet_info['popularity_score']}")
        print(f"   Is News Link?: {tweet_info['is_news']}")
        print()

    print("\n--- 2) Discovering new tokens from GMGN & Pumpfun ---")
    tokens = aggregate_tokens()
    for t in tokens:
        print(json.dumps(t, indent=2))

    print("\n--- 3) Checking a memecoin handle on TweetScout (placeholder) ---")
    memecoin_handle = "PepeMemecoin"  # example
    tscout_results = search_memecoin_account_on_tweetscout(memecoin_handle)
    if tscout_results:
        print("TweetScout results:")
        for r in tscout_results:
            print(r)
    else:
        print("No results or error in TweetScout search.")

    print("\n--- 4) Checking contract via rugcheck & auto-buy if 'safe' (placeholder) ---")
    # Let's pretend we pick the first token from tokens list (if available)
    if tokens:
        test_token = tokens[0].get("contract") or "0xDEADBEEF"
        rug_data = check_contract_rugcheck(test_token)
        if "error" not in rug_data:
            print(f"[RugCheck] Score: {rug_data['score']}, Status: {rug_data['status']}")
            
            # Arbitrary check: if status isn't "N/A," let's attempt to buy
            # This is purely a demonstration. You would parse real logic (score > X, status == "Safe", etc.)
            if rug_data["status"] != "N/A":
                print(f"Trying to buy token {test_token}...")
                try:
                    amount_in_wei = to_wei(0.001, 'ether')  # example buy: 0.001 WETH
                    receipt = buy_token(test_token, amount_in_wei)
                    print("TX Receipt: ", receipt)
                    send_telegram_message(
                        f"Purchased token {test_token}! TX: {receipt.transactionHash.hex()}"
                    )
                except Exception as e:
                    print(f"[Buy Error] {e}")
                    send_telegram_message(f"Buy error for {test_token}: {e}")
            else:
                print("Skipping buy due to status check.")
        else:
            print(f"RugCheck error: {rug_data['error']}")
    else:
        print("No tokens available to test RugCheck & buy flow.")

    print("\n--- Script completed! ---")


if __name__ == "__main__":
    main()
