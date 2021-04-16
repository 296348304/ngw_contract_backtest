import json
import traceback
import requests
import time
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def exchange2num(exchange):
    if exchange is None:
        return 4
    # 中金所
    elif exchange == 'CFFEX':
        return 3
    # 上期所
    elif exchange == 'SHFE':
        return 4
    # 大商所
    elif exchange == 'DCE':
        return 5
    # 郑商所
    elif exchange == 'CZCE':
        return 6
    # 上海国际能源交易中心
    elif exchange == 'INE':
        return 15

# 策略信号新增
def send_strategy_signal(stgyId=None,symbol=None,exchange=None,side=None,quantity=None,price=None):
    exchange_num = exchange2num(exchange)
    side_offset = {'open_long': [66, 1], 'close_long': [66, 2], 'open_short': [83, 1], 'close_short': [83, 2]}
    side_, offset = side_offset[side]
    body = {
          "stgyId": stgyId,
          "symbol": symbol,
          "exchange": exchange_num,
          "orderSide": side_,
          "offset": offset,
          "quantity": quantity,
          "price": price,
          "orderType": 1,
          "note": ''
    }
    # print(body)
    # url = 'http://iqfairobotwebapi.taojin.svc.ingress.inquant/Trade/SendStgySignal'
    url = "http://dev-taojinairobot.inquant.cn/Trade/SendStgySignal"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6",
            "Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(body), headers=headers)
        response.close()
    except Exception:
        print(traceback.format_exc())
        return None
    else:
        response = response.content.decode()
        response_json = json.loads(response)
        if response_json['error_no'] == 0:
            return int(response_json['data'])
        else:
            return 0

if __name__ == '__main__':
    t11 = time.time()


    stgyId = 1
    symbol = 'rb2101'
    exchange = 'SHFE'
    side = 'open_long'
    quantity = 10
    price = 3884
    a = send_strategy_signal(stgyId=stgyId,symbol=symbol,exchange=exchange,side=side,quantity=quantity,price=price)
    print(a)

    print(time.time()-t11)




















