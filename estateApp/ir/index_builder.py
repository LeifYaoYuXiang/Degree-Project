from whoosh.fields import Schema, ID, TEXT, NUMERIC
from whoosh.index import create_in, open_dir
# from whoosh.query import *
# from whoosh.qparser import *
from jieba.analyse import ChineseAnalyzer
import pymongo
from pymongo.collection import Collection
import estateApp.ir.settings as settings


class IndexBuilder:
    def __init__(self):
        self.mongoClient = pymongo.MongoClient(host=settings.MONGODB_HOST_SECOND, port=settings.MONGODB_PORT_SECOND)
        # self.db = self.mongoClient[settings.MONGODB_DBNAME][settings.MONGODB_SHEETNAME]
        # self.mongoClient.admin.authenticate('root', 'root')
        self.db = pymongo.database.Database(self.mongoClient, settings.MONGODB_DBNAME_SECOND)
        self.pagesCollection = Collection(self.db, settings.MONGODB_SHEETNAME_SECOND)

    def build_index(self):
        analyzer = ChineseAnalyzer()

        # 创建索引模板
        # 房屋新闻模板
        # schema = Schema(
        #     id=ID(stored=True),
        #     title=TEXT(stored=True, analyzer=analyzer),
        #     url=ID(stored=True),
        #     time=TEXT(stored=True),
        #     content=TEXT(stored=True),
        #     #content=TEXT(stored=False, analyzer=analyzer),  # 文章内容太长了，不存
        # )

        #新房模板
        schema = Schema(
            id=ID(stored=True),
            index=TEXT(stored=True, analyzer=analyzer),
            province=TEXT(stored=True, analyzer=analyzer),
            city=TEXT(stored=True, analyzer=analyzer),
            house_name=TEXT(stored=True, analyzer=analyzer),
            total_price=TEXT(stored=True, analyzer=analyzer),
            position=TEXT(stored=True, analyzer=analyzer),
            size=TEXT(stored=True),
            price_each_square_meter=TEXT(stored=True, analyzer=analyzer),
            province_pinyin=TEXT(stored=True, analyzer=analyzer),
            city_pinyin=TEXT(stored=True, analyzer=analyzer),
            house_name_pinyin=TEXT(stored=True, analyzer=analyzer),
            position_pinyin=TEXT(stored=True, analyzer=analyzer),
            # content=TEXT(stored=False, analyzer=analyzer),  # 文章内容太长了，不存
        )


        # 索引文件相关
        import os.path
        if not os.path.exists('index_second'):
            os.mkdir('index_second')
            ix = create_in('index_second', schema)
            print('未发现索引文件,已构建.')
        else:
            ix = open_dir('index_second')
            print('发现索引文件并载入....')

        # 索引构建
        writer = ix.writer()
        indexed_amount = 0
        total_amount = self.pagesCollection.count_documents({})
        false_amount = self.pagesCollection.count_documents({'indexed': 'FALSE'})
        print(false_amount, '/', total_amount)
        while True:
            try:

                row = self.pagesCollection.find_one({'indexed': 'FALSE'})
                print(row)
                if row is None:
                    # all indexed is 'True' 所有条目已经处理
                    writer.commit()
                    print('所有条目索引处理完毕.')
                    break
                else:
                    # get new row 获取了新的条目

                    writer.add_document(
                        id=str(row['_id']),
                        index=str(row['index']),
                        province=row['province'],
                        city=row['city'],
                        house_name=row['house_name'],
                        total_price=str(row['total_price']),
                        size=str(row['size']),
                        position=row['position'],
                        price_each_square_meter=str(row['price_each_square_meter']),
                        province_pinyin=row['province_pinyin'],
                        city_pinyin=row['city_pinyin'],
                        house_name_pinyin=row['house_name_pinyin'],
                        position_pinyin=row['position_pinyin']
                    )
                    print('here')
                    # the end
                    self.pagesCollection.update_one({'_id': row['_id']}, {'$set': {'indexed': 'TRUE'}})
                    writer.commit()  # 每次构建提交一次
                    writer = ix.writer()  # 然后重新打开
                    indexed_amount += 1
                    print(indexed_amount, '/', false_amount, '/', total_amount)
            except:
                print(row['_id'], '异常.')
                print('已处理', indexed_amount, '/', total_amount, '项.')
                break


# --------此段代码用以在数据库中缺少indexed字段时补充插入indexed字段并初始化为false--------
# host = settings.MONGODB_HOST
# port = settings.MONGODB_PORT
# dbname = settings.MONGODB_DBNAME
# sheetname = settings.MONGODB_SHEETNAME
# client = pymongo.MongoClient(host=host, port=port)
# mydb = client[dbname]
# post = mydb[sheetname]
# post.update({}, {'$set':{'indexed':'False'}}, upsert=False, multi=True)   # 增加indexed项并初始化为False
# post.update({'indexed': 'True'}, {'$set':{'indexed':'False'}})
# --------------------------------------------------------------------------------------

if __name__ == '__main__':
    id = IndexBuilder()
    id.build_index()
