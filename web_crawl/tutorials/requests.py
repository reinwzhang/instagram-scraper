# -*- coding: utf-8 -*-
"""
Created on Wed May 16 09:19:46 2018

@author: rein9
"""

from collections import OrderedDict
from urllib import parse

_search_gzh = 1
_search_article = 2

class SougouRequest:
    @classmethod
    def generate_search_gzh_url(cls, keyword, page=2):
        assert isinstance(page, int) and page > 0 
        query = OrderedDict()
        query['type'] = _search_gzh
        query['page'] = page
        query['ie'] = 'utf8'
        query['query'] = keyword
        return 'http://weixin.sogou.com/weixin?%s' % parse.urlencode(query)
    
if __name__ == '__main__':
    url = SougouRequest.generate_search_gzh_url('九章算法')
    print(url)