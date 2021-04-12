import datetime
import ngshare as ng
import numpy as np
from ngw_contract_backtest import ngw as api


def initialize(context):
    context.N = 20
    context.k = 2
    context.count = 35
    context.universe = 'agM.SHFE'


def create_universe(context):
    pass


def handle_data(context):

    now_datetime = context.get_datetime()
    print(now_datetime)

    # 09:00:00 15:30:00 时间段交易
    if str(now_datetime)[11:19] > '09:00:00' and str(now_datetime)[11:19] <= '15:00:00':

        if now_datetime == '2020-04-13 09:40:00':
            # print('hahahahhahahhahahahhaaaha')
            price = context.get_price(symbol_exchange=context.universe)
            order = context.open_long(symbol_exchange=context.universe, price=price, volume=10)
            print(order)

        positions = context.get_positions()
        print(positions)
        cash = context.get_cash()
        print('cash： ', cash)
        pnl = context.get_pnl()
        print('pnl： ', pnl)
        equity = context.get_equity()
        print('总资产： ', equity)
        print()





info={
    'name':'布林反转',
    'tag':'中风险',
    'sort': 1,
    'init_cash':2000000,
    "start":'2020-06-10 09:00:00',
    "end":'2020-09-30 15:00:00',
    'freq':'1m',
    'commission_ratio': 0.0003,
    "is_toSQL": False,

    'universe':['rbM.SHFE'],
    'is_preload':True,
}
my_strategy = api.create_strategy(info,initialize,create_universe,handle_data)
my_strategy.run()



