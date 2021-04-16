# import json
#
# from ngwcontractbacktest.ngw.constants import REDIS_HOST, REDIS_PORT, REDIS_DB1
# from redis import StrictRedis
#
# def conn_redis():
#     try:
#         redis_client=StrictRedis(host=REDIS_HOST,port=REDIS_PORT,db=REDIS_DB1)
#
#         result = redis_client.keys()  #获取所有key的值
#         print(result)
#
#         # exchange = 'poloniex'
#         # symbol = 'BTC/USDT'
#         # key = '{}::market::price::{}'.format(exchange,symbol)
#         # result = redis_client.get(key)
#         # result_json = json.loads(result.decode())
#         # print(type(result_json))
#         # print(result_json)
#
#     except Exception as e:  #输出键的值，如果键不存在则返回None
#         print(e)