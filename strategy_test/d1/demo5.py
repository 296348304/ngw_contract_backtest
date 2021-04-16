import datetime
import ngshare as ng
from ngw_contract_backtest import ngw as api


def initialize(context):
    context.short = 12
    context.long = 26
    context.smooth = 9
    context.count = 35
    context.open_times = 0
    context.close_times = 0
    context.universe = 'rb2101.SHFE'


def create_universe(context):
    pass


def handle_data(context):

    now_datetime = context.get_datetime()
    print(now_datetime)

    # 09:00:00 15:30:00 时间段交易
    if str(now_datetime)[11:19] > '09:00:00' and str(now_datetime)[11:19] < '15:30:00':
        history_data = context.get_history(symbol_exchange=context.universe,count=context.count)
        # print(history_data)

        df_close = history_data['close']
        # 计算MACD，diff, dea和macd_hist
        diff = df_close.ewm(span=context.short).mean()-df_close.ewm(span=context.long).mean()
        dea = diff.ewm(span=context.smooth).mean()
        macd_hist = diff - dea

        # 获取最新价格close
        price = context.get_price(symbol_exchange=context.universe)
        # print(price)
        # 柱线由负变正时，作为开仓信号
        if macd_hist.iloc[-1] > 0 and macd_hist.iloc[-2] <= 0:
            if context.open_times < 10:
                order_id = context.open_long(symbol_exchange=context.universe, price=price, volume=3)
                context.open_times +=1

        # 柱线由正变负时，作为平仓信号
        elif macd_hist.iloc[-1] < 0 and macd_hist.iloc[-2] > 0:
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
    "start":'2020-04-10 09:00:00',
    "end":'2020-06-10 15:00:00',
    'freq':'1m',
    # 'is_dynamic_universe': True,
    'is_dynamic_universe': False,
    'universe':['rb2101.SHFE'],
    'commission_ratio':0.0003,
    "is_toSQL": False
}
my_strategy = api.create_strategy(info,initialize,create_universe,handle_data)
my_strategy.run()


