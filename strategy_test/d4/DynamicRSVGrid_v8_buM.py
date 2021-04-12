import datetime, os
import ngshare as ng
import numpy as np
import pandas as pd
from ngw_contract_backtest import ngw as api

def initialize(context):
    context.N = 20
    context.k = 2
    context.count = 35
    context.universe = info['universe'][0]  #'rb2101.SHFE'

    contract_detail = ng.get_contract_detail(symbol=context.universe.split(".")[0],
                                             exchange=context.universe.split(".")[1])
    PARAMS = {
        "sigmamulti": 1,
        "stoploss": 0.005,
        "sgltradecap": 1.0 / 3,
        "gvpctlimit": 0.002,
        "gvpctlimit_cap": 0.004,
        "HLmin": 31,
        "trademinlist":get_trademinlist(),
        "priceStep":contract_detail["priceStep"],
        "multiplier" : contract_detail["lots"],
        "trademethod" : "inclose", # "inclose", "inmarket", "inlimit"
        "init_lv" : 1.0/0.2,
    }
    context.PARAMS = PARAMS

def create_universe(context):
    return ['cu2101.SHFE']

def get_trademinlist():
    def datetime_range(startstr, endstr, mindelta):
        # include start and end
        start = pd.to_datetime(startstr)
        end = pd.to_datetime(endstr)
        delta = datetime.timedelta(minutes=mindelta)
        current = start
        while current <= end:
            yield current
            current += delta
    list1 = [dt.strftime('%H:%M:%S') for dt in datetime_range("20201111090000","20201111101500",1)]
    list2 = [dt.strftime('%H:%M:%S') for dt in datetime_range("20201111103100","20201111113000",1)]
    list3 = [dt.strftime('%H:%M:%S') for dt in datetime_range("20201111133100","20201111145500",1)]
    trademinlist = list1+list2+list3
    return trademinlist


def get_nearestprice(price, direction, priceStep):
    if price*1.0/priceStep -int(price*1.0/priceStep) == 0:
        return price
    else:
        downprice = int(price*1.0/priceStep)*priceStep
        upprice = downprice + priceStep
        if direction == "buy":
            return downprice
        if direction == "sell":
            return upprice

def get_nexttradeprice(timenum, context, start = 0):
    navs = context.Perf["Navs"]
    gridbs = context.gridbs
    gvpctlimit = context.gvpctlimit

    RSV = (navs[timenum] - navs[start:timenum + 1].min()) / (navs[start:timenum + 1].max() - navs[start:timenum + 1].min())
    nextsell_p = max(navs[timenum] + RSV * gridbs, navs[timenum] * (1 + gvpctlimit / 2.0))
    nextbuy_p = min(navs[timenum] - (1 - RSV) * gridbs, navs[timenum] * (1 - gvpctlimit / 2.0))
    return nextsell_p, nextbuy_p

def adjust_buysell(context):
    nextsell = context.nextsell
    nextbuy = context.nextbuy
    histmean = context.histmean
    gvpctlimit = context.gvpctlimit
    gvpctlimit_cap = context.gvpctlimit_cap
    nav_0 = context.nav_0
    if nextsell * 1.0 / nextbuy - 1 < gvpctlimit:
        nextsell_new = histmean + (nextsell - histmean) / (nextsell - nextbuy) * nextbuy * gvpctlimit
        nextbuy_new = histmean - (histmean - nextbuy) / (nextsell - nextbuy) * nextbuy * gvpctlimit
        nextsell = nextsell_new
        nextbuy = nextbuy_new
    if nextsell * 1.0 / nextbuy - 1 > gvpctlimit_cap:
        if nav_0 > 1.0 / gvpctlimit_cap:
            nextsell_new = histmean + (nextsell - histmean) / (nextsell - nextbuy) * nextbuy * gvpctlimit_cap
            nextbuy_new = histmean - (histmean - nextbuy) / (nextsell - nextbuy) * nextbuy * gvpctlimit_cap
            nextsell = nextsell_new
            nextbuy = nextbuy_new
    return nextsell,nextbuy

def handle_data(context):
    now_datetime = context.get_datetime()
    print(now_datetime)

    positions = context.get_positions()
    print("position : ",positions)
    cash = context.get_cash()
    print('cash： ', cash)
    pnl = context.get_pnl()
    print('pnl： ', pnl)
    equity = context.get_equity()
    print('总资产： ', equity)
    print()

    # context.open_long_market(symbol_exchange=context.universe, volume=abs(5))

    nexttimestr = str(now_datetime)[11:19]
    # if nexttimestr in context.PARAMS["trademinlist"]:
    #     if context.PARAMS["trademinlist"].index(nexttimestr)%4 == 0:
    #         context.open_long_market(symbol_exchange=context.universe, volume=abs(5))
    #     elif context.PARAMS["trademinlist"].index(nexttimestr)%4 ==1:
    #         context.close_long_market(symbol_exchange=context.universe, volume=abs(5))
    #     elif context.PARAMS["trademinlist"].index(nexttimestr)%4 ==2:
    #         context.open_short_market(symbol_exchange=context.universe, volume=abs(5))
    #     else:
    #         context.close_short_market(symbol_exchange=context.universe, volume=abs(5))

    if nexttimestr == '14:46:00':
        context.open_long_market(symbol_exchange=context.universe, volume=abs(5))

    if nexttimestr == '14:47:00':
        context.close_long_market(symbol_exchange=context.universe, volume=abs(5))


    # elif context.PARAMS["trademinlist"].index(nexttimestr)%4 ==1:
    #     context.close_long_market(symbol_exchange=context.universe, volume=abs(5))
    # elif context.PARAMS["trademinlist"].index(nexttimestr)%4 ==2:
    #     context.open_short_market(symbol_exchange=context.universe, volume=abs(5))
    # else:
    #     context.close_short_market(symbol_exchange=context.universe, volume=abs(5))


    positions = context.get_positions()
    print("position : ",positions)
    cash = context.get_cash()
    print('cash： ', cash)
    pnl = context.get_pnl()
    print('pnl： ', pnl)
    equity = context.get_equity()
    print('总资产： ', equity)
    print()

info={
    'name':'RSV网格测试',
    'tag':'中风险',
    'sort': 6001,
    'init_cash':1000000,
    # "start":'2020-01-02 09:00:00',
    # "end":'2020-10-30 15:00:00',
    "start": '2020-09-01 09:00:00',
    "end": '2020-11-30 15:00:00',
    'freq':'1m',
    'force_position_ratio':0.05,
    # 'is_dynamic_universe': True,
    'is_dynamic_universe': False,
    'universe':['cu2101.SHFE'],
    'commission_ratio':0.0003/2.0,
    "is_toSQL": True,
    "is_simulate":True
}

my_strategy = api.create_strategy(info,initialize,create_universe,handle_data)
my_strategy.run()



