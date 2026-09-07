# StockSense

StockSense fetches stock quotes and recent news headlines from Finviz, scores the headlines using NLTK's VADER sentiment analyzer, and displays a chart of average daily sentiment for each stock.

## Requirements

- Python 3.14 (tested with Python 3.14.7).
- Internet access to install dependencies and fetch Finviz data.
- A desktop environment to display the Matplotlib chart.

## Setup

Clone the repository and enter its directory:

```bash
git clone https://github.com/khana251/StockSense.git
cd StockSense
```

Create and activate a virtual environment on macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, use Command Prompt:

```bat
py -3.14 -m venv .venv
.venv\Scripts\activate.bat
```

With the environment activated, install the dependencies and download the VADER sentiment dictionary:

```bash
python -m pip install -r requirements.txt
python -m nltk.downloader -d .venv/nltk_data vader_lexicon
```

The dictionary is a separate data download; installing NLTK alone does not include it.

## Run

From the project directory, with the virtual environment activated:

```bash
python main.py
```

The script prints the quote price returned by Finviz for each ticker and opens a sentiment chart. The displayed quote may be the last closing price. Close the chart window to finish the script.

For later sessions, activate the environment again before running. In VS Code, select `.venv/bin/python` (macOS/Linux) or `.venv\Scripts\python.exe` (Windows) using **Python: Select Interpreter**.

## Choose stocks

When you run the script, enter one or more ticker symbols at the terminal prompt:

```text
Examples: AAPL (Apple), MSFT (Microsoft), TSLA (Tesla), GOOG (Alphabet)
Enter ticker symbols separated by spaces or commas [TSLA GOOG MSFT]: AAPL, MSFT
```

Use spaces or commas to separate symbols. Lowercase input is accepted and duplicate symbols are removed. Press Enter without entering symbols to use TSLA, GOOG, and MSFT. Use symbols supported by Finviz; failed tickers are skipped with a warning.

## Read the chart

- **X-axis:** News publication date. Finviz's “Today” is interpreted in the America/New_York time zone.
- **Y-axis:** Average VADER compound score across the retrieved headlines for that stock and date, ranging from −1 (negative) to +1 (positive). Zero is neutral.
- **Colors:** Stock tickers, identified in the legend.

Scores describe headline language, not stock returns or price forecasts. The chart uses the headlines available on the fetched pages, so dates and headline counts can vary between stocks. A missing bar can indicate missing data, rather than neutral sentiment.

## Troubleshooting

- **`ModuleNotFoundError`:** Activate `.venv` and run `python -m pip install -r requirements.txt`. Check that your editor uses the same environment.
- **`Resource vader_lexicon not found`:** Run the VADER download command from Setup using the active environment.
- **`ZoneInfoNotFoundError`:** Install time zone data with `python -m pip install tzdata` in the active environment.
- **`Price element not found` or `News table not found`:** Verify that the ticker has a Finviz page. The site may have changed its HTML or returned an unexpected page; the selectors in `main.py` may need updating. The script warns and skips tickers with failed requests, missing required elements, or unusable news dates, then plots the remaining stocks. If none have usable news, it exits with an explanatory message and no chart.
- **Network errors:** Check connectivity and retry later if Finviz is unavailable or limits requests.
- **No chart window:** Run from a desktop session with an interactive Matplotlib backend. A noninteractive backend such as `Agg` does not open windows.

To leave the virtual environment:

```bash
deactivate
```
