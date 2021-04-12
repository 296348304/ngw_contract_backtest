import datetime as dt
import ngshare as ng
from ngw_contract_backtest import ngw as api



def initialize(context):
    context.yesuanshi=dt.time(1,41,0)
    context.baisuanshi=dt.time(9,38,0)
    context.yekaishi=dt.time(9,1,0)
    context.yepingshi=dt.time(14,55,0)
    context.baikaishi=dt.time(10,46,0)
    context.baipingshi=dt.time(14,43,0)
    context.zuoshoushi=dt.time(14,59,0)
    context.fenjie=dt.time(20,0,0)
    context.yekaiyu=0.0067
    context.yesunyu=-0.015
    context.yekaijia=None
    context.baikaiyu=0.0067
    context.baisunyu=-0.015
    context.baikaijia=None
    context.zuoshoujia=None
    context.cate='ag'
    context.jiaoyisuo='.SHFE'
    context.count = 1
    context.zhibiao=None
    context.pingzhiye=None
    context.pingzhibai=None
    context.universe = None
    context.volume = 1
    context.posidye=0
    context.posisye=0
    context.posidbai=0
    context.posisbai=0
    context.n=0



def create_universe(context):
    context.kaiciduo=0
    context.kaicikong=0
    context.barji=0
    context.youye=None

    # return
    main_info=ng.get_main_contract(variety_code=context.cate)
    context.universe=main_info['contractName']+context.jiaoyisuo
    print(context.universe)
    history_data = context.get_history(symbol_exchange=context.universe,count=context.count)
    if history_data.iloc[-1]['time'].time()==context.zuoshoushi:
        context.zuoshoujia=history_data.iloc[-1]['open']
    else:
        context.zuoshoujia=None
        print('数据缺失',context.universe,context.get_datetime())
        
    # 模拟触发 每天开盘前创建universe
    print('111111')
    print(context.universe)
    return [context.universe]


def handle_data(context):
    context.barji+=1
    print(context.barji)
    # return
    now_time = context.get_datetime() #当前的时间
    print(now_time)
    if context.barji==1:
        if now_time.time()>=context.fenjie:
            context.youye=True
        else:
            context.youye=False
    #取最新的一根bar的数据
    zuixin_data = context.get_history(symbol_exchange=context.universe,end=now_time,count=context.count)
    jiagenow=zuixin_data.iloc[0]['close']
    print(zuixin_data)
    if context.posidye==1:
        context.pingzhiye=jiagenow/context.yekaijia-1
        if context.pingzhiye<=context.yesunyu:
            order_id = context.close_long_market(symbol_exchange=context.universe,volume=context.volume)
            context.posidye=0
            print('夜盘动量止损平多')
        elif now_time.time()==context.yepingshi:
            order_id = context.close_long_market(symbol_exchange=context.universe,volume=context.volume)
            context.posidye=0
            print('夜盘动量时间平多')
            
    if context.posidbai==1:
        context.pingzhibai=jiagenow/context.baikaijia-1
        if context.pingzhibai<=context.baisunyu:
            order_id = context.close_long_market(symbol_exchange=context.universe,volume=context.volume)
            context.posidbai=0
            print('白盘动量止损平多')
        elif now_time.time()==context.baipingshi:
            order_id = context.close_long_market(symbol_exchange=context.universe,volume=context.volume)
            context.posidbai=0
            print('白盘动量时间平多')
        
    if (context.youye==True and now_time.time()==context.yesuanshi) or \
        (context.youye==False and now_time.time()==context.baisuanshi):
        if context.zuoshoujia!=None:
            context.zhibiao=jiagenow/context.zuoshoujia-1
        else:
            context.zhibiao=None
    if now_time.time()==context.yekaishi and context.zhibiao!=None and \
        context.zhibiao>context.yekaiyu and context.youye==True and context.posidye==0:
            order_id = context.open_long_market(symbol_exchange=context.universe,volume=context.volume)
            context.posidye=1
            context.yekaijia=jiagenow
    elif now_time.time()==context.baikaishi and context.zhibiao!=None and \
        context.zhibiao>context.baikaiyu and context.youye==False and context.posidbai==0:
            order_id = context.open_long_market(symbol_exchange=context.universe,volume=context.volume)
            context.posidye=1
            context.baikaijia=jiagenow
    

info={
    'name':'测试策略',
    'tag':6001,
    'sort': 1,
    'init_cash':100000,
    "start":'2021-03-25 19:00:00',
    "end":'2021-03-25 21:10:00',
    'freq':'1m',
    'force_position_ratio':0.05,
    'universe':['agM.SHFE'],
    'commission_ratio': 0.0001, #0.0003,
    "is_DayNight":True,
    "is_toSQL": False,
    "is_simulate": False,
}
my_strategy = api.create_strategy(info,initialize,create_universe,handle_data)
my_strategy.run()


