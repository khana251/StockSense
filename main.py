# StockSense | Market Sentiment Insight

from urllib.request import urlopen, Request
from urllib.parse import quote
from urllib.error import URLError
from http.client import HTTPException
import sys
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from zoneinfo import ZoneInfo

FINVIZ_URL = 'https://finviz.com/quote.ashx?t='


def prompt_tickers():
    """Read ticker symbols, removing duplicates and applying defaults."""
    print('Examples: AAPL (Apple), MSFT (Microsoft), TSLA (Tesla), GOOG (Alphabet)')
    try:
        ticker_input = input('Enter ticker symbols separated by spaces or commas [TSLA GOOG MSFT]: ')
    except (EOFError, KeyboardInterrupt):
        sys.exit('\nNo ticker selection received; exiting.')

    tickers = list(dict.fromkeys(ticker_input.upper().replace(',', ' ').split()))
    if not tickers:
        tickers = ['TSLA', 'GOOG', 'MSFT']
    print('Analyzing: ' + ', '.join(tickers))

    return tickers


def fetch_stock_data(ticker):
    """Fetch the quote price and news table for one ticker."""
    url = FINVIZ_URL + quote(ticker, safe='')
    req = Request(url=url, headers={'user-agent': 'my-app'})
    with urlopen(req, timeout=30) as response:
        html = BeautifulSoup(response, 'html.parser')

    price_element = html.find('strong', class_='quote-price_price')
    if price_element is None:
        raise ValueError(f"Price element not found for {ticker}")

    price = price_element.get_text(strip=True)

    news_table = html.find(id='news-table')
    if news_table is None:
        raise ValueError(f"News table not found for {ticker}")
    return price, news_table


def get_formatted_today():
    """Return today in the time zone used by Finviz."""
    return datetime.now(ZoneInfo('America/New_York')).strftime('%b-%d-%y')


def parse_news(ticker, news_table):
    """Parse and validate one ticker’s news before returning any rows."""
    date = None
    ticker_data = []
    for row in news_table.find_all('tr'):
        headline = row.select_one('a.tab-link-news')
        date_cell = row.find('td')
        if headline is None or date_cell is None:
            continue
        title = headline.get_text(strip=True)
        date_data = date_cell.get_text(strip=True).split()

        if len(date_data) == 2:
            date, time = date_data
        elif len(date_data) == 1 and date is not None:
            time = date_data[0]
        else:
            continue

        if date == 'Today':
            date = get_formatted_today()
        datetime.strptime(date, '%b-%d-%y')
        ticker_data.append([ticker, date, time, title])
    if not ticker_data:
        raise ValueError('No usable news headlines found')
    return ticker_data


def collect_news(tickers):
    """Collect headlines, warning and continuing when a ticker fails."""
    parsed_data = []
    for ticker in tickers:
        try:
            price, news_table = fetch_stock_data(ticker)
            print(f'The current price of {ticker} is: ${price}')
            parsed_data.extend(parse_news(ticker, news_table))
        except (URLError, OSError, HTTPException, ValueError) as exc:
            print(f"Warning: skipping {ticker}: {exc}", file=sys.stderr)
    return parsed_data


def analyze_sentiment(parsed_data):
    """Build a DataFrame with headline sentiment scores and parsed dates."""
    df = pd.DataFrame(parsed_data, columns=['ticker', 'date', 'time', 'title'])

    vader = SentimentIntensityAnalyzer()
    df['compound'] = df['title'].apply(
        lambda title: vader.polarity_scores(title)['compound']
    )

    df['date'] = pd.to_datetime(df['date'], format='%b-%d-%y').dt.date
    return df


def plot_sentiment(df):
    """Plot average daily sentiment and return the chart axes."""
    mean_df = df.drop(columns=['time', 'title']).groupby(['ticker', 'date']).mean()

    mean_df = mean_df.unstack()
    mean_df = mean_df.xs('compound', axis="columns").transpose()
    ax = mean_df.plot(kind='bar', figsize=(12, 6))
    ax.set_title('Average Daily News Headline Sentiment by Stock')
    ax.set_xlabel('News publication date')
    ax.set_ylabel('Average sentiment score\n(-1 = negative, 0 = neutral, +1 = positive)')
    ax.set_ylim(-1, 1)
    ax.axhline(0, color='gray', linewidth=0.8)
    ax.legend(title='Stock ticker')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    return ax


def main():
    """Run the interactive stock sentiment workflow."""
    tickers = prompt_tickers()
    parsed_data = collect_news(tickers)
    if not parsed_data:
        sys.exit('No usable news data for any requested ticker; no chart generated.')
    df = analyze_sentiment(parsed_data)
    ax = plot_sentiment(df)
    plt.show()
    return df, ax


if __name__ == '__main__':
    main()
