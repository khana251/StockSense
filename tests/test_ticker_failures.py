import contextlib
import io
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch
from urllib.error import URLError

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt


MAIN = Path(__file__).resolve().parents[1] / 'main.py'
GOOD_PAGE = b'''<strong class="quote-price_price">100</strong>
<table id="news-table"><tr><td>Sep-07-26 09:00AM</td>
<td><a class="tab-link-news">Strong earnings growth</a></td></tr></table>'''


class TickerFailureTests(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def run_script(self, responses, ticker_input=''):
        output = io.StringIO()
        errors = io.StringIO()
        with patch('urllib.request.urlopen', side_effect=responses), \
                patch('builtins.input', return_value=ticker_input), \
                patch('nltk.sentiment.vader.SentimentIntensityAnalyzer') as vader, \
                patch('matplotlib.pyplot.show'), \
                contextlib.redirect_stdout(output), \
                contextlib.redirect_stderr(errors):
            vader.return_value.polarity_scores.return_value = {'compound': 0.5}
            module = runpy.run_path(str(MAIN))
            df, ax = module['main']()
            result = {'df': df, 'ax': ax}
        return result, errors.getvalue()

    def test_import_does_not_start_interactive_workflow(self):
        with patch('builtins.input') as prompt, patch('urllib.request.urlopen') as fetch:
            runpy.run_path(str(MAIN))
        prompt.assert_not_called()
        fetch.assert_not_called()
        self.assertEqual(plt.get_fignums(), [])

    def test_terminal_tickers_are_normalized_and_deduplicated(self):
        result, errors = self.run_script(
            [io.BytesIO(GOOD_PAGE), io.BytesIO(GOOD_PAGE)],
            ' aapl, msft AAPL ',
        )
        self.assertEqual(result['df']['ticker'].drop_duplicates().tolist(), ['AAPL', 'MSFT'])
        self.assertEqual(set(result['df']['ticker']), {'AAPL', 'MSFT'})
        self.assertEqual(errors, '')

    def test_single_ticker(self):
        result, errors = self.run_script([io.BytesIO(GOOD_PAGE)], 'tsla')
        self.assertEqual(result['df']['ticker'].drop_duplicates().tolist(), ['TSLA'])
        self.assertEqual(set(result['df']['ticker']), {'TSLA'})
        self.assertEqual(errors, '')

    def test_failed_ticker_does_not_stop_remaining_stocks(self):
        failures = [
            URLError('connection failed'),
            TimeoutError('timed out'),
            b'<html>No price</html>',
            b'<strong class="quote-price_price">100</strong>',
            GOOD_PAGE.replace(b'Sep-07-26', b'invalid-date'),
            b'<strong class="quote-price_price">100</strong><table id="news-table"></table>',
        ]
        for failure in failures:
            with self.subTest(failure=failure):
                first = io.BytesIO(failure) if isinstance(failure, bytes) else failure
                result, errors = self.run_script([
                    first, io.BytesIO(GOOD_PAGE), io.BytesIO(GOOD_PAGE),
                ])
                self.assertEqual(set(result['df']['ticker']), {'GOOG', 'MSFT'})
                self.assertIn('Warning: skipping TSLA:', errors)
                self.assertEqual(
                    [text.get_text() for text in result['ax'].get_legend().get_texts()],
                    ['GOOG', 'MSFT'],
                )
                plt.close('all')

    def test_all_failures_exit_without_a_chart(self):
        with self.assertRaisesRegex(SystemExit, 'No usable news data'):
            self.run_script([URLError('unavailable') for _ in range(3)])
        self.assertEqual(plt.get_fignums(), [])


if __name__ == '__main__':
    unittest.main()
