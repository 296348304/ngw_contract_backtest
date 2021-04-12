import json
import requests
import traceback
from Crypto.Cipher import DES3
from Crypto.Util.Padding import *


def encrypt(plainText):
    __key_bytes = bytes("niugu123niugu456niugu123", encoding="utf-8")
    __iv_bytes = bytes("12312300", encoding='utf-8')
    """根据明文，做DES加密，并返回Hex字符串"""
    data = bytes(plainText,'utf-8')
    text = pad(data,8)
    cipher = DES3.new(__key_bytes, DES3.MODE_CBC,IV=__iv_bytes)
    m = cipher.encrypt(text)
    s = bytes.hex(m)
    return s

def decrypt(encryptText):
    __key_bytes = bytes("niugu123niugu456niugu123", encoding="utf-8")
    __iv_bytes = bytes("12312300", encoding='utf-8')
    data = bytes.fromhex(encryptText)
    cipher = DES3.new(__key_bytes, DES3.MODE_CBC,IV=__iv_bytes)
    s = cipher.decrypt(data)
    s = unpad(s,8)
    s = s.decode('utf-8') # unpad and decode bytes to str
    return s


def push_stock_new(json_str=None):
    param = encrypt(json_str)
    body = {'param':param}
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6",
            "Content-Type": "application/x-www-form-urlencoded"}
        url = "http://iqftaojinquantstrategywebapi.taojin.svc.ingress.inquant/Trade/SendStgySignal"
        # print(url)
        response = requests.post(url,data=body,headers=headers)
        response.close()
    except Exception:
        print(traceback.format_exc())
        return None
    else:
        response = response.content.decode()
        response_str = decrypt(response)
        response_json = json.loads(response_str)
        # print(response_json)
        return response_json


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

# 期货跟单接口
def trace_order(order=None):
    exchange_num = exchange2num(order.get('exchange'))
    side_offset = {'open_long': [66, 1], 'close_long': [83, 2], 'open_short': [83, 1], 'close_short': [66, 2]}
    side_, offset = side_offset[order.get('side')]

    doc = {
        "StgyId": str(1),
        "Symbol": order.get('symbol'),
        "Exchange": str(exchange_num),
        "OrderSide": str(side_),
        "Offset": str(offset),
        "Quantity": str(int(order.get('filled_volume'))),
        "Scale": str(round(float(order.get('order_percent')),4)),
        "Price": str(round(float(order.get('avg_price')),4)),
        "OrderType": str(1),
    }
    json_str = json.dumps(doc)
    print(json_str)
    response_json = push_stock_new(json_str=json_str)
    print(response_json)
    return response_json


if __name__ == '__main__':

    # json_str = {"StgyId":"1","Symbol":"c2105","Exchange":"5","OrderSide":"66","Offset":"1","Quantity":"1","Scale":"0.2","Price":"2777","OrderType":"1"}
    # json_str = {"StgyId": "1", "Symbol": "bu2016", "Exchange": "4", "OrderSide": "66", "Offset": "1", "Quantity": "3","Scale": "0.0158", "Price": "2692.0", "OrderType": "1"}

    order = {'create_time': '2021-01-08 11:03:00', 'order_id': 686364202013586, 'symbol_exchange': 'bu2016.SHFE', 'symbol': 'bu2016', 'varietyId': 29, 'exchange': 'SHFE', 'exchangeId': 4, 'side': 'open_long', 'sideId': 1, 'avg_price': 2692.0, 'initial_volume': 3.0, 'filled_volume': 3.0, 'filled_amount': 80760.0, 'order_percent': 0.0158, 'margin': 8076.0, 'margin_ratio': 0.1, 'lots': 10, 'status': 'Filled', 'commission': 8.076, 'other': 0, 'complete_time': '2021-01-08 11:03:00'}

    trace_order(order=order)

    # a = push_stock_new()
    # print(a)
    # print(type(a))

