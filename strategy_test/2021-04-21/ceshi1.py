import datetime as dt
import ngshare as ng
from ngw_contract_backtest import ngw as api



def initialize(context):
    context.count = 1
    context.cate='ag'
    context.jiaoyisuo='SHFE'
    


def create_universe(context):
    now_time = context.get_datetime() #当前的时间
    print(now_time,type(now_time))
    main_info=ng.get_main_contract(variety_code=context.cate)
    context.mainsym=main_info['symbol']
    context.universe=context.mainsym+'.'+context.jiaoyisuo
    # 模拟触发 每天开盘前创建universe
    return [context.universe]



def handle_data(context):
    now_time = context.get_datetime() #当前的时间
    print(now_time,type(now_time))
    riqi=now_time[:10]
    riqi='2021-04-12'
    main_info=data = ng.get_HisMainContract(variety=context.cate, start=riqi, end=riqi)
    print(main_info,main_info['symbol'])
    #history_data = context.get_history(symbol_exchange=context.universe,count=context.count)
    #print(history_data)
    #data = ng.get_hisTick(symbol=context.mainsym,exchange=context.jiaoyisuo,end=now_time,count=context.count)
    #print(data)
    #price = context.GetPreviousTick(symbol_exchange=context.universe,now_time=now_time)
    #print(price)
    pass

info={
    'name':'测试策略',
    'tag':6001,
    'sort': 1,
    'init_cash':100000,
    "start":'2019-03-25 20:00:00',
    "end":'2019-03-25 21:00:00',
    'freq':'1m',
    'force_position_ratio':0.05,
    'universe':["agM.SHFE"],
    'commission_ratio': 0.0001, #0.0003,
    "is_DayNight":True,
    "is_toSQL": False,
    "is_simulate": False,
}
my_strategy = api.create_strategy(info,initialize,create_universe,handle_data)
my_strategy.run()


