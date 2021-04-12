import datetime
import ngshare as ng
from ngw_contract_backtest import ngw as api



def initialize(context):
    context.count = 30
    context.universe = 'rb2101.SHFE'



def create_universe(context,now_date):
    return


def handle_data(context,bars):
    # print(bars)

    # 时间
    now_datetime = context.get_datetime()
    print(now_datetime)

    # 获取历史数据
    history_data = context.get_history(symbol_exchange=context.universe,end=now_datetime,count=context.count)
    print(history_data)
    # history_data = context.get_history(symbol_exchange=context.universe,start='2020-09-10 10:40:00',end='2020-09-10 10:50:00')
    # print(history_data)

    # 获取当前点 价格
    price = context.get_price(symbol_exchange=context.universe,now_time=now_datetime)
    print(price)


    context.open_long(symbol_exchange=context.universe, price=price, volume=3)
    context.open_short(symbol_exchange=context.universe, price=price, volume=1)
    context.close_long(symbol_exchange=context.universe, price=price, volume=2)
    context.close_short(symbol_exchange=context.universe, price=price, volume=4)


    positions = context.get_positions()
    print(positions)
    cash = context.get_cash()
    print('cash： ', cash)
    equity = context.get_equity()
    print('总资产： ', equity)




info={
    'name':'动态网格',
    'tag':'中风险',
    'sort': 1,
    'init_cash':2000000,
    "start":'2020-09-10 09:00:00',
    "end":'2020-09-30 15:00:00',
    'freq':'1m',
    # 'is_dynamic_universe': True,
    'is_dynamic_universe': False,
    'universe':['rb2101.SHFE'],
    'commission_ratio':0.0003,
    "is_toSQL": False
}
my_strategy = api.create_strategy(info,initialize,create_universe,handle_data)
my_strategy.run()


