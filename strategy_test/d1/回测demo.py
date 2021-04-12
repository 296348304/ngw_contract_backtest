import datetime
import ngshare as ng
import numpy as np
from ngw_contract_backtest import ngw as api
import pandas as pd
from string import digits




def initialize(context):
    pass


def create_universe(context):
    pass


def handle_data(context):

    now_datetime = context.get_datetime()
    print(now_datetime)

    date = now_datetime[:10]
    hm = now_datetime[11:16]

    # 夜盘 >=21:00 or <=04:00
    if hm>='21:00' or hm<="04:00":
        # 21:00 开盘，开仓
        if hm=='21:01':
            cash = context.get_cash()
            print('cash： ', cash)
            context.open_long_market(symbol_exchange='jM.DCE', volume=3)
            cash = context.get_cash()
            print('cash： ', cash)
            context.open_long_market(symbol_exchange='jdM.DCE', volume=14)
            cash = context.get_cash()
            print('cash： ', cash)
            context.open_long_market(symbol_exchange='agM.SHFE', volume=8)
            cash = context.get_cash()
            print('cash： ', cash)
            context.open_long_market(symbol_exchange='hcM.SHFE', volume=16)
            cash = context.get_cash()
            print('cash： ', cash)




    # 14:59 收盘，平掉所有仓位
    if hm=='14:59':
        # 当前仓位
        positions = context.get_positions()
        print(positions)
        # 多空仓都平掉
        for symbol_exchange in positions.keys():
            cash = context.get_cash()
            print('cash： ', cash)
            # 平多仓
            if len(positions[symbol_exchange]['long'].keys())!=0:
                volume = positions[symbol_exchange]['long']['volume']
                print("平多头 %s，%s 张"%(symbol_exchange,volume))
                context.close_long_market(symbol_exchange=symbol_exchange,volume=volume)
            # 平空仓
            if len(positions[symbol_exchange]['short'].keys())!=0:
                volume = positions[symbol_exchange]['short']['volume']
                print("平空头 %s，%s 张"%(symbol_exchange,volume))
                context.close_short_market(symbol_exchange=symbol_exchange,volume=volume)




info={
    'name':'布林反转',
    'tag':'中风险',
    'sort': 1,
    'init_cash':1000000,
    "start":'2020-07-21 09:00:00',
    "end":'2020-07-22 15:00:00',
    # "end":'2020-11-18 15:00:00',
    'freq':'1m',
    'commission_ratio': 0.0003,
    "is_toSQL": False,

    'universe':['agM.SHFE'],
    'is_preload':True,
}
my_strategy = api.create_strategy(info,initialize,create_universe,handle_data)
my_strategy.run()


