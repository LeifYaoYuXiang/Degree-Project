from whoosh.index import open_dir
# from whoosh.query import *
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh import sorting


class QuerySecond:
    def __init__(self, mydir=None):
        if mydir is None:
            self.ix = open_dir('index_second')
        else:
            print(mydir)
            self.ix = open_dir(mydir)
        self.searcher = self.ix.searcher()

    def search(self, parameter):
        # 从parameter中取出要执行搜索的字段（如newsContent, newsUrl）
        parser = None
        list = parameter['keys']
        if len(list) == 1:
            parser = QueryParser(list[0], schema=self.ix.schema)
        if len(list) > 1:
            parser = MultifieldParser(list, schema=self.ix.schema)

        # sorting
        scores = sorting.ScoreFacet()


        # 是否分页返回OR全部返回,默认全部返回
        _limit = None
        if 'page' in parameter and 'pagesize' in parameter:
            page = parameter['page']
            pagesize = parameter['pagesize']
            if page > 0 and pagesize != 0:
                _limit = page * pagesize

        # 执行搜索
        myquery = parser.parse(parameter['keywords'])
        results = self.searcher.search(myquery, limit=_limit, sortedby=[scores])
        print(len(results))

        return results

    def standard_search(self, query):
        parameter = {
            'keys': ['province', 'city', 'house_name', 'total_price', 'size', 'position',
                     'price_each_square_meter', 'province_pinyin', 'city_pinyin', 'house_name_pinyin',
                     'position_pinyin'],
            'keywords': query,
            'page': 15,
            'pagesize': 10,
        }
        return self.search(parameter)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.searcher.close()
        print('Query close.')


## beta code
if __name__ == '__main__':
    q = QuerySecond()
    print('----------')
    q.standard_search('北京')
    print('----------')