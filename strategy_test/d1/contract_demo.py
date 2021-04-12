import datetime
import ngshare as ng
from ngw_contract_backtest import ngw as api



def initialize(context):
    context.count = 30
    context.universe = 'agM.SHFE'
    context.volume = 2



def create_universe(context):
    # 模拟触发 每天开盘前创建universe
    # return ['bu2015.SHFE']
    pass


def run_daily(context):
    pass


def handle_data(context):
    now_datetime = context.get_datetime()
    print(now_datetime)

    history_data = context.get_history(symbol_exchange=context.universe,count=context.count)
    # print(history_data)
    history_data = context.get_history(symbol_exchange=context.universe,end=now_datetime,count=context.count)
    # print(history_data)


    price = context.get_price(symbol_exchange=context.universe,now_time=now_datetime)
    # print(price)




    order_id = context.open_long(symbol_exchange=context.universe,price=price,volume=context.volume)
    # order_id = context.open_short(symbol_exchange=context.universe,price=price,volume=context.volume)
    # order_id = context.close_long(symbol_exchange=context.universe,price=price,volume=context.volume)
    # order_id = context.close_short(symbol_exchange=context.universe,price=price,volume=context.volume)
    #
    # order_id = context.open_long_market(symbol_exchange=context.universe,volume=context.volume)
    # order_id = context.open_short_market(symbol_exchange=context.universe,volume=context.volume)
    # order_id = context.close_long_market(symbol_exchange=context.universe,volume=context.volume)
    # order_id = context.close_short_market(symbol_exchange=context.universe,volume=context.volume)


    positions = context.get_positions()
    print("position : ",positions)
    cash = context.get_cash()
    print('cash： ', cash)
    pnl = context.get_pnl()
    print('pnl： ', pnl)
    equity = context.get_equity()
    print('总资产： ', equity)


info={
    'name':'测试策略',
    'tag':6001,
    'sort': 1,
    'init_cash':1000000,
    "start":'2021-03-26 09:00:00',
    "end":'2021-03-30 15:00:00',
    'freq':'1m',
    'force_position_ratio':0.05,
    'universe':['agM.SHFE'],
    'commission_ratio': 0.0001, #0.0003,
    "run_daily_time":"07:00:00",
    "is_toSQL": False,
    "is_simulate": False,
}
my_strategy = api.create_strategy(info,initialize,create_universe,handle_data)
my_strategy.run()


