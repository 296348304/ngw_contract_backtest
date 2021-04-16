import pika
import time
import datetime
import json
import ngwshare as ng

username = 'lhpt'
pwd = 'lhpt*1ngwermvo'
ip_addr = '192.168.3.213'
port_num = 5672

credentials = pika.PlainCredentials(username, pwd)
connection = pika.BlockingConnection(pika.ConnectionParameters(ip_addr, port_num, '/sty/contract', credentials))
channel = connection.channel()

def get_priceStep(VarietyId):
    symbolsinfo = ng.get_all_varieties()
    priceStep = symbolsinfo.loc[symbolsinfo[id] == VarietyId,"priceStep"]

    return priceStep

def get_stgypos(pos_dict,symbol_exchange):
    if pos_dict != {}:
        if "long" in pos_dict[symbol_exchange].keys():
            long_pos = pos_dict[symbol_exchange]["long"]["volume"]
        else:
            long_pos = 0
        if "short" in pos_dict[symbol_exchange].keys():
            short_pos = pos_dict[symbol_exchange]["short"]["volume"]
        else:
            short_pos = 0
    else:
        long_pos = 0
        short_pos = 0
    return long_pos - short_pos

def get_robotpos(stgyAccount, symbol_exchange):
    long_pos = ng.get_robot_position(stgyAccount=stgyAccount,symbol_exchange=symbol_exchange,posSide=1)
    if long_pos["data"] != None:
        long_pos = long_pos["data"]["quantity"]
    else:
        long_pos = 0
    short_pos = ng.get_robot_position(stgyAccount=stgyAccount,symbol_exchange=symbol_exchange,posSide=2)
    if short_pos["data"] != None:
        short_pos = short_pos["data"]["quantity"]
    else:
        short_pos = 0
    return long_pos - short_pos

def get_tradepos(quantity,side):
    if side == "open_long" or "close_short":
        quantity = 1.0 * quantity
    elif side == "open_short" or "close_long":
        quantity = -1.0 * quantity
    else:
        print("side error : {}".format(side))
        raise
    return quantity

def get_tradeside(last_pos,tgt_pos):
    if last_pos > 0:
        if tgt_pos - last_pos >=0:
            tradeside = "open_long"
        else:
            tradeside = "close_long"
    elif last_pos < 0:
        if tgt_pos - last_pos <=0:
            tradeside = "open_short"
        else:
            tradeside = "close_short"
    else:
        if tgt_pos>=0:
            tradeside = "open_long"
        else:
            tradeside = "open_short"

def execute_trade(stgyAccountId,stgySignalId,symbol_exchange,tradeside,tradequantity):
    symbol = symbol_exchange.split("_")[0]
    exchange = symbol_exchange.split("_")[1]
    nowprice = ng.get_hisTick(symbol=symbol, exchange=exchange, count=1)["last"]
    tradestatus = "success"
    if tradeside == "open_long" or "close_short": #buy
        while tradequantity>0:
            # if nowprice-tgtprice <= 2.0*priceStep:
            #     robot_orderdata = ng.OmsContract_CreateOrder(stgyAccountId=stgyAccountId, stgySignalId=stgySignalId,
            #                                                  symbol_exchange=symbol_exchange, side=tradeside,
            #                                                  quantity=tradequantity)
            # else:

            robot_orderdata = ng.OmsContract_CreateOrder(stgyAccountId=stgyAccountId, stgySignalId=stgySignalId,
                                                         symbol_exchange=symbol_exchange, side=tradeside,
                                                         quantity=tradequantity)

            if robot_orderdata["error_no"] == 0:
                robotOrderID = robot_orderdata["data"]
                checknum=1
                while checknum<=3:
                    OrderStatus = ng.OmsContract_GetOrderStatus(stgyOrderId=robotOrderID)
                    if OrderStatus["status"] == 5:
                        break
                    else:
                        checknum += 1
                tradequantity = OrderStatus["quantity"] - OrderStatus["filled"]
                if tradequantity>0:
                    CancelOrder = ng.OmsContract_CancelOrder(stgyAccountId=stgyAccountId, stgyOrderId=robotOrderID)
                    OrderStatus = ng.OmsContract_GetOrderStatus(stgyOrderId=robotOrderID)
                    tradequantity = OrderStatus["quantity"] - OrderStatus["filled"]
                if tradequantity>0:
                    nowprice = ng.get_hisTick(symbol=symbol, exchange=exchange, count=1)["last"]
            else:
                tradestatus = "failed"
                tradequantity = 0

    elif tradeside == "open_short" or "close_long": #sell
        while tradequantity > 0:
            # if nowprice - tgtprice >= -2.0 * priceStep:
            #     robot_orderdata = ng.OmsContract_CreateOrder(stgyAccountId=stgyAccountId, stgySignalId=stgySignalId,
            #                                                  symbol_exchange=symbol_exchange, side=tradeside,
            #                                                  quantity=tradequantity)
            # else:

            robot_orderdata = ng.OmsContract_CreateOrder(stgyAccountId=stgyAccountId, stgySignalId=stgySignalId,
                                                         symbol_exchange=symbol_exchange, side=tradeside,
                                                         quantity=tradequantity)

            if robot_orderdata["error_no"] == 0:
                robotOrderID = robot_orderdata["data"]
                checknum=1
                while checknum<=3:
                    OrderStatus = ng.OmsContract_GetOrderStatus(stgyOrderId=robotOrderID)
                    if OrderStatus["status"] == 5:
                        break
                    else:
                        checknum += 1
                tradequantity = OrderStatus["quantity"] - OrderStatus["filled"]
                if tradequantity>0:
                    CancelOrder = ng.OmsContract_CancelOrder(stgyAccountId=stgyAccountId, stgyOrderId=robotOrderID)
                    OrderStatus = ng.OmsContract_GetOrderStatus(stgyOrderId=robotOrderID)
                    tradequantity = OrderStatus["quantity"] - OrderStatus["filled"]
                if tradequantity>0:
                    nowprice = ng.get_hisTick(symbol=symbol, exchange=exchange, count=1)["last"]
            else:
                tradestatus = "failed"
                tradequantity = 0

    print("    {}".format(tradestatus))

# 消费成功的回调函数
def callback(ch, method, properties, body):
    orderdata = json.loads(body.decode())
    print(datetime.datetime.now())
    print(orderdata)

    stgySignalId = orderdata["stgySignalId"]
    VarietyId = orderdata["varietyID"]
    symbol_exchange = orderdata["symbol_exchange"]
    tgtprice = orderdata["price"]

    tgt_stgypos = get_stgypos(orderdata["strategy_position"],symbol_exchange)
    # trade_stgypos = get_tradepos(orderdata["quantity"],orderdata["side"])

    maxaum = orderdata["last_equity"] / orderdata["margin_ratio"] * 0.95
    equity_stgypos = min(1000000 * 3, maxaum)

    priceStep = get_priceStep(VarietyId)

    robotsinfo = ng.get_all_robots_info()
    robotsinfo = robotsinfo[(robotsinfo["stgyID"]==33)&(robotsinfo["tarVarietyID"]==VarietyId)&(robotsinfo["status"]==1)]
    robotsinfo.set_index("stgyAccountID", drop=True, inplace=True)

    for stgyAccountId in robotsinfo.index():
        print("--- Trade for stgyAccountId : {}".format(stgyAccountId))
        robotId = robotsinfo.loc[stgyAccountId,"robotId"]
        last_robotpos = get_robotpos(stgyAccountId, symbol_exchange)
        equity_stgypos = robotsinfo.loc[stgyAccountId,"initAsset"]
        # equity_stgypos = get_robotequity()
        tgt_robotpos = int(1.0*equity_stgypos/equity_stgypos*tgt_stgypos)

        tradeside = get_tradeside(last_robotpos,tgt_robotpos)
        tradequantity = abs(tgt_robotpos - last_robotpos)
        print("    tradeside : {}".format(tradeside))
        print("    tradquan  : {}".format(tradequantity))
        print("    execute trade")
        execute_trade(stgyAccountId,stgySignalId,symbol_exchange,tradeside,tradequantity,tgtprice,priceStep)

    # 1.获取订阅该策略的用户 及 对应合约
    # 2.下单

    time.sleep(10)

channel.basic_consume(queue='HDStrategyOrder6002', on_message_callback=callback, auto_ack=True)
print('监听消息中...')
channel.start_consuming()













