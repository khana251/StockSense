# StockSense | Market Sentiment Insight                                                                                            

from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

finviz_url = 'https://finviz.com/quote.ashx?t='
finviz_url = 'https://finviz.com/quote.ashx?t='

tickers = ['META', 'TSLA', 'GOOG', 'MSFT']

news_tables = {}

for ticker in tickers:
    url = finviz_url + ticker

    req = Request(url=url, headers={'user-agent': 'my-app'})
    response = urlopen(req)
    
    html = BeautifulSoup(response, 'html')

    price = html.find('strong', class_='quote-price_wrapper_price').get_text()

    news_table = html.find(id='news-table')
    news_tables[ticker] = news_table
    print('The current price of ' + ticker + ' is: ' + '$' + price)
parsed_data = []

def get_formatted_today():
    return datetime.today().strftime('%b-%d-%y')

for ticker, news_table in news_tables.items():
    for row in news_table.findAll('tr'):
        title = row.a.text
        date_data = row.td.text.split(' ')

        if len(date_data) == 21:
            time = date_data[12]
        else:
            date = date_data[12]
            time = date_data[13]

        if date == 'Today':
            date = get_formatted_today()
        parsed_data.append([ticker, date, time, title])

df = pd.DataFrame(parsed_data, columns=['ticker', 'date', 'time', 'title'])

vader = SentimentIntensityAnalyzer()


f = lambda title: vader.polarity_scores(title)['compound']
df['compound'] = df['title'].apply(f)

df['date'] = pd.to_datetime(df['date'], format='%b-%d-%y').dt.date


mean_df = df.drop(columns=['time', 'title']).groupby(['ticker', 'date']).mean()

mean_df = mean_df.unstack()
mean_df = mean_df.xs('compound', axis="columns").transpose()
mean_df.plot(kind='bar')
plt.show()