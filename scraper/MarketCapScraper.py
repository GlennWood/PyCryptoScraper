# coding: utf-8

from __future__ import absolute_import, unicode_literals
from __future__ import print_function

from schema.DataSchema import DataSchema
#from lxml import html
import scraper.Base

import sys
import re
import requests
import ast
import time

class MarketCapScraper(scraper.Base.CryptoScraperBase):

    def __init__(self, base_url = 'https://coinmarketcap.com', currencies_to_scrape=ast.literal_eval("[{'name':'ALL','tags':['usd']}]")):
        """
            Initializes the gecko-scraper
        """
        self.base_url = base_url

        valid_currencies = DataSchema(many=True).load(currencies_to_scrape)
        self.currencies_to_scrape = valid_currencies

        self.mapping = [
            [ 'market_cap_usd',   [0] ],
            [ 'market_cap_currency', [2] ],
            [ 'market_cap', [1] ],
            [ 'market_cap_code', [0] ],
            [ 'val-1',      [0] ],
            [ 'val-2',      [0] ],
            [ 'val-3',      [0] ],
            [ 'volume_usd', [0] ],
            [ 'volume_btc', [0] ],
            [ 'val-4',      [0] ],
            [ 'price_usd',  [2] ],
            [ 'price_btc',  [2] ]
        ]

    def _extract(self, name, tag, *args, **kwargs):
        """
            Extract data from the given url

        :param name: CryptCurrency name
        :type name: str
        :param tag: Tag for the CryptCurrency
        :type tag: str
        :param args:
        :param kwargs:
        :return:
        """
        content = self.get_page_content(name, tag)
        return content

    def _transform(self, page_content, exchange_symbol, *args, **kwargs):
        """
            Transforms the extracted data into an given format

        :param page_content: extracted page content in html
        :type page_content: str
        :param args:
        :param kwargs:
        :return: Transformed CryptCurrency Details
        """
        return self._get_currency_details(page_content, exchange_symbol)

    
    def scrape(self):
        """
            Scrape All Currencies from CoinMarketCap

        :return: Scraped Crypt-Currencies
        """

        response = requests.get(self.base_url+'/all/views/all/')
        response.raise_for_status()
        matches = re.findall(
            r'<td class="no-wrap currency-name" data-sort="([^"]+)[^>]>' # Currency name
            '\s*<div [^>]*></div>\s*<span class="currency-symbol"><a href="([^"]+)"' # Detail URL
            '\s*>([^<]+)</a></span>'   # Symbol
            '.*?data-usd="([^"]+)"'    # MarketCap USD
            '.*?data-btc="([^"]+)"'    # MarketCap BTC
            '.*?data-usd="([^"]+)"'    # Price USD
            '.*?data-btc="([^"]+)"'    # Price BTC
            '.*?data-supply="([^"]+)"' # Volume
            '.*?data-usd="([^"]+)"'    # Volume USD
            '.*?data-btc="([^"]+)"'    # Volume BTC
            ,response.content, re.DOTALL)
        results = []
        for mtch in matches:
            one_result = []
            coinPath = mtch[0].lower().replace(' ','-').replace('.','-').replace('-[futures]','')
            '''
            coinPath = mtch[0].lower().replace(' ','-').replace('.','-').replace('-[futures]','')

            if coinPath in coinPathMap:
                coinPath = coinPathMap[coinPath]
            '''

            currencies_to_scrape = ast.literal_eval("[{'name':'"+coinPath+"','tags':['usd']}]")
            #output = options.output
            valid_currencies = DataSchema(many=True).load(currencies_to_scrape)
            marketcap_scraper = MarketCapScraper(currencies_to_scrape=valid_currencies)
            try:
                url = self.base_url+mtch[1]
                response = requests.get(url)
                response.raise_for_status()
                one_result = marketcap_scraper.scrape_detail(url, response.content)
                results.append(one_result)
            except requests.exceptions.HTTPError as ex:
                #if '-' in coinPath: # Sometimes CoinGecko just deletes a ' ' or a '-'.
                #    coinPath = coinPath.replace('-','')
                #    keep_trying = True
                #else:
                print(str(ex), file=sys.stderr)

        return results

    def scrape_detail(self, url, content):
        """
            Scrape Crypt-Currencies from the given CoinMarketCap detail page

        :return: Scraped Crypt-Currencies
        """
        matches = re.findall(
        r'<h3 class="details-text-medium">Market Cap</h3>\s*</div>\s*'
        '<div class="coin-summary-item-detail details-text-medium">\s*'
        '<span data-currency-market-cap data-usd="[^"]*">\s*'
        '<span data-currency-value>([^<\n]*)</span>\s*'
        '<span data-currency-code>([^<\n]*)</span>\s*'
        '</span><br>\s*<span class="text-gray">\s*'
        '<span data-format-market-cap data-format-value="[^<\n]*">\s*([^<\n]*)\s*'
        '</span>\s*([^<\n]*)\s*<br>\s*</span>\s*</div>\s*'
        '.*?'
        '<td data-sort="[^"]*"><img src="[^"]*" class="logo" alt="[^"]*"><a href="/exchanges/bitfinex/">[^<]*</a></td>\s*'
        '<td data-sort="[^/]*/USD"><a href="[^"]*" target="_blank">[^<]*</a></td>\s*'
        '<td class="text-right" data-sort="[^"]*">\s*'
        '<span class="volume" data-usd="([^"]*)" data-btc="([^"]*)" data-native="([^"]*)">\s*'
        '[^<]*</span>\s*</td>\s*'
        '<td class="text-right" data-sort="[^"]*">\s*'
        '<span class="price" data-usd="([^"]*)" data-btc="([^"]*)" data-native="([^"]*)">\s*'
        '[^<]*</span>\s*</td>\s*'

        ,content, re.DOTALL)
        
        results = {}
        if len(matches) is 0:
            results['ERROR'] = ['Does not parse', url]
        else:
            idx = 0
            for mapping in self.mapping:
                try:
                    value = matches[0][idx]
                    idx += 1
                    proc = mapping[1][0]
                    if proc is 1:
                        value = scraper.Base.clean_numerical_amount(value)
                    elif proc is 2:
                        value = scraper.Base.clean_currency_amount(value)
                    
                    results[mapping[0]] = value
                except IndexError as ex:
                    print(str(ex)+" while mapping field '"+mapping[0]+"'")
        # append current timestamp
        results['timestamp'] = int(time.time())

        print(results)

        return results
