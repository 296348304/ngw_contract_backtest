import datetime
import ngshare as ng
import numpy as np
from ngw_contract_backtest import ngw as api


def initialize(context):
    context.flag = 1
    context.times = 0
    context.universe = 'rb2101.SHFE'


def create_universe(context):
    pass


def handle_data(context):

    now_datetime = context.get_datetime()
    print(now_datetime)

    # 09:00:00 15:30:00 时间段交易
    if str(now_datetime)[11:19] > '09:00:00' and str(now_datetime)[11:19] < '15:30:00':
        # 获取最新价格
        current_price = context.get_price(symbol_exchange=context.universe)
        # print(current_price)

        if context.flag == 1:
            if context.times < 20:
                corder_id = context.open_long(symbol_exchange=context.universe, price=current_price, volume=3)
            else:
                context.flag = -context.flag
                context.times = 0
        else:
            if context.times < 20:
                corder_id = context.close_long(symbol_exchange=context.universe, price=current_price, volume=3)
            else:
                context.flag = -context.flag
                context.times = 0

        positions = context.get_positions()
        print(positions)
        cash = context.get_cash()
        print('cash： ', cash)
        equity = context.get_equity()
        print('总资产： ', equity)
        print()

        context.times += 1
    print(context.times)



info={
    'name':'动态网格',
    'tag':'中风险',
    'sort': 1,
    'init_cash':2000000,
    "start":'2020-02-10 09:00:00',
    "end":'2020-10-30 15:00:00',
    'freq':'1m',
    # 'is_dynamic_universe': True,
    'is_dynamic_universe': False,
    'universe':['rb2101.SHFE'],
    'commission_ratio':0.0003,
    "is_toSQL": False
}
my_strategy = api.create_strategy(info,initialize,create_universe,handle_data)
my_strategy.run()


