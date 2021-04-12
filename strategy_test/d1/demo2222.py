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
    context.universe = 'buM.SHFE'



def create_universe(context):
    # 模拟触发 每天开盘前创建universe
    # return ['bu2015.SHFE']
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
        price = context.get_price(symbol_exchange=context.universe,now_time=now_datetime)
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

    # order_id = context.open_long(symbol_exchange=context.universe,price=price,volume=context.volume)
    # order_id = context.open_short(symbol_exchange=context.universe,price=price,volume=context.volume)
    # order_id = context.close_long(symbol_exchange=context.universe,price=price,volume=context.volume)
    # order_id = context.close_short(symbol_exchange=context.universe,price=price,volume=context.volume)
    #
    # order_id = context.open_long_market(symbol_exchange=context.universe,volume=context.volume)
    # order_id = context.open_short_market(symbol_exchange=context.universe,volume=context.volume)
    # order_id = context.close_long_market(symbol_exchange=context.universe,volume=context.volume)
    # order_id = context.close_short_market(symbol_exchange=context.universe,volume=context.volume)




info={
    'name':'测试策略',
    'tag':6001,
    'sort': 1,
    'init_cash':1000000,
    "start":'2021-02-02 09:00:00',
    "end":'2021-02-05 15:00:00',
    'freq':'1m',
    'force_position_ratio':0.05,
    'universe':['buM.SHFE'],
    'commission_ratio': 0.0001, #0.0003,
    "run_daily_time":"07:00:00",
    "is_toSQL": False,
    "is_simulate": False,
}
my_strategy = api.create_strategy(info,initialize,create_universe,handle_data)
my_strategy.run()


