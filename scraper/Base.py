# coding: utf-8

from __future__ import absolute_import, unicode_literals
from abc import ABCMeta, abstractmethod
import re


class CryptoScraperBase(object):
    """
        Base class for the crypto-scraper
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def _extract(self, *args, **kwargs):
        """ extracting data"""

    @abstractmethod
    def _transform(self, *args, **kwargs):
        """ transform data"""

def clean_currency_amount(data):
    m = re.search(r'^\S([,\d.]+)', data)
    if m:
        return m.group(1).replace(',','')
    else:
        return data

def clean_numerical_amount(data):
    return data.replace(',','')
