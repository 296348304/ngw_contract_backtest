import datetime
import ngshare as ng
import numpy as np
from ngw_contract_backtest import ngw as api


def initialize(context):
    context.N = 20
    context.k = 2
    context.count = 35
    context.universe = 'ag2101.SHFE'


def create_universe(context):
    pass


def handle_data(context):

    now_datetime = context.get_datetime()
    print(now_datetime)

    history_data = context.get_history(symbol_exchange=context.universe,count=context.count)
    # print(history_data)

    df_close = history_data['close'].tolist()
    # MB中轨：N日的简单移动平均
    # UP上轨：中轨 + k倍N日标准差
    # DN下轨：中轨 - k倍N日标准差
    MA = np.mean(df_close[-context.N + 1:])
    MD = np.sqrt(sum([(i - MA) ** 2 for i in df_close]) / len(df_close))
    MB = np.mean(df_close[-context.N + 1:])
    UP = MB + context.k * MD
    DN = MB - context.k * MD

    # 获取最新价格
    price = context.get_price(symbol_exchange=context.universe)
    # print(price)
    # 如果收盘价下穿布林中轨时，平仓
    if df_close[-2] < UP and df_close[-1] > UP:
         context.close_long(symbol_exchange=context.universe, price=price, volume=5)

    # 如果收盘价上穿布林上轨时，开仓
    elif df_close[-2] > DN and df_close[-1] < DN:
        context.open_long(symbol_exchange=context.universe, price=price, volume=5)


    # context.open_long(symbol_exchange=context.universe, price=price, volume=3)
    # context.open_short(symbol_exchange=context.universe, price=price, volume=1)
    # context.close_long(symbol_exchange=context.universe, price=price, volume=2)
    # context.close_short(symbol_exchange=context.universe, price=price, volume=4)

    positions = context.get_positions()
    # print(positions)
    cash = context.get_cash()
    # print('cash： ', cash)
    pnl = context.get_pnl()
    # print('pnl： ', pnl)
    equity = context.get_equity()
    # print('总资产： ', equity)
    # print()





info={
    'name':'布林反转',
    'tag':'中风险',
    'sort': 1,
    'init_cash':2000000,
    "start":'2020-04-10 09:00:00',
    "end":'2020-10-30 15:00:00',
    'freq':'1m',
    'force_position_ratio':0.05,
    # 'is_dynamic_universe': True,
    'is_dynamic_universe': False,
    'universe':['ag2101.SHFE'],
    'commission_ratio':0.0003,
    "is_toSQL": False
}
my_strategy = api.create_strategy(info,initialize,create_universe,handle_data)
my_strategy.run()


