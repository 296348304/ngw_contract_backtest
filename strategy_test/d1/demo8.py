import datetime
import ngshare as ng
import numpy as np
from ngw_contract_backtest import ngw as api


def initialize(context):
    context.grid = []
    context.grid_direction = -1    # -1向下开网格 1向上开网格
    context.grid_num = 2          # 网格数量
    context.price_separation = 15  # 网格间距
    context.cover_diff = 20        # 网格平仓价差
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

        # 开网格
        if len(context.grid) == 0 \
                or (context.grid_direction == -1 and current_price - context.grid[-1][
            'open_price'] > context.price_separation) \
                or (context.grid_direction == 1 and current_price - context.grid[-1][
            'open_price'] < context.price_separation):
            if context.grid_direction == -1:
                corder_id = context.open_long(symbol_exchange=context.universe, price=current_price, volume=30)
                context.grid.append({'open_price': current_price, 'cover_price': current_price + context.cover_diff})
            else:
                corder_id = context.close_long(symbol_exchange=context.universe, price=current_price, volume=30)
                context.grid.append({'open_price': current_price, 'cover_price': current_price - context.cover_diff})

        # 第一个网格止盈
        if len(context.grid) > 0 and (
                context.grid_direction == -1 and current_price > context.grid[-1]['cover_price']) or \
                (context.grid_direction == 1 and current_price < context.grid[-1]['cover_price']):
            if context.grid_direction == -1:
                corder_id = context.close_long(symbol_exchange=context.universe, price=current_price, volume=30)
            else:
                corder_id = context.open_long(symbol_exchange=context.universe, price=current_price, volume=30)
            context.grid.pop()

        # 创建网格数量超过指定数量，最后一个网格止损
        elif len(context.grid) > context.grid_num:
            if context.grid_direction == -1:
                corder_id = context.close_long(symbol_exchange=context.universe, price=current_price, volume=30)
            else:
                corder_id = context.open_long(symbol_exchange=context.universe, price=current_price, volume=30)
            del context.grid[0]


        positions = context.get_positions()
        # print(positions)
        cash = context.get_cash()
        # print('cash： ', cash)
        equity = context.get_equity()
        # print('总资产： ', equity)
        # print()





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


