import datetime
import ngshare as ng
import numpy as np
from ngw_contract_backtest import ngw as api


def initialize(context):
    context.short = 3
    context.long = 21
    context.count = 35
    context.open_times = 0
    context.close_times = 0
    context.universe = 'ag2101.SHFE'


def create_universe(context):
    pass


def handle_data(context):

    now_datetime = context.get_datetime()
    print(now_datetime)

    # 09:00:00 15:30:00 时间段交易
    if str(now_datetime)[11:19] > '09:00:00' and str(now_datetime)[11:19] < '15:30:00':
        history_data = context.get_history(symbol_exchange=context.universe,count=context.count)
        # print(history_data)

        close_price = history_data['close'].tolist()
        MA_short = np.mean(close_price[-context.short:])
        MA_long = np.mean(close_price[-context.long:])
        MA_short_PD2 = np.mean(close_price[-context.short - 1:])
        MA_long_PD2 = np.mean(close_price[-context.long - 1:])

        # 获取最新价格
        price = context.get_price(symbol_exchange=context.universe)
        # print(price)
        # 如果快线上穿慢线时，金叉买入
        if MA_short > MA_long and MA_short_PD2 <= MA_long_PD2:
            if context.open_times < 10:
                order_id = context.open_long(symbol_exchange=context.universe, price=price, volume=3)
                context.open_times +=1
        # 快线下穿慢线时，死叉卖出
        elif MA_short < MA_long and MA_short_PD2 > MA_long_PD2:
            if context.close_times < 10:
                order_id = context.close_long(symbol_exchange=context.universe, price=price, volume=3)
                context.close_times += 1


        positions = context.get_positions()
        print(positions)
        cash = context.get_cash()
        print('cash： ', cash)
        equity = context.get_equity()
        print('总资产： ', equity)
        print()





info={
    'name':'动态网格',
    'tag':'中风险',
    'sort': 1,
    'init_cash':2000000,
    "start":'2020-06-10 09:00:00',
    "end":'2020-08-30 15:00:00',
    'freq':'1m',
    # 'is_dynamic_universe': True,
    'is_dynamic_universe': False,
    'universe':['ag2101.SHFE'],
    'commission_ratio':0.0003,
    "is_toSQL": False
}
my_strategy = api.create_strategy(info,initialize,create_universe,handle_data)
my_strategy.run()


