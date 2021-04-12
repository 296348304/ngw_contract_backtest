import datetime, os
import ngshare as ng
import numpy as np
import pandas as pd
from ngw_contract_backtest import ngw as api

def initialize(context):
    context.universe = info['universe'][0]  #'rb2101.SHFE'


def create_universe(context):
    print(context.universe)
    variety = context.universe.split(".")[0][:-1]
    market = context.universe.split(".")[1]
    print(variety)
    print(market)
    main_symbol = ng.get_main_contract(variety_code=variety)["symbol"]+"."+market
    context.universe = main_symbol
    return [main_symbol]


def handle_data(context):
    now_datetime = context.get_datetime()
    print(now_datetime)


    positions = context.get_positions()
    print("position : ",positions)
    cash = context.get_cash()
    print('cash： ', cash)
    pnl = context.get_pnl()
    print('pnl： ', pnl)
    equity = context.get_equity()
    print('总资产： ', equity)
    print()

info={
    'name':'DynamicRSV网格_buM.SHFE',
    'tag': 6001,
    'sort': 1,
    'init_cash':1000000,
    "start": '2021-02-20 09:00:00',
    "end": '2021-02-24 15:00:00',
    'freq':'1m',
    'force_position_ratio':0.05,
    'universe':['buM.SHFE'],
    'commission_ratio':0.0003/2.0,
    "is_toSQL": False,
    "is_simulate":False,
}

my_strategy = api.create_strategy(info,initialize,create_universe,handle_data)
my_strategy.run()

# uni_symbol = info["universe"][0].split(".")[0]
# aum_dict = {"init" : [info['init_cash']]}
# for i in range(len(my_strategy.dates)):
#     aum_dict[my_strategy.dates[i]] = [my_strategy.equities[i]]
# aum_df = pd.DataFrame.from_dict(aum_dict).T
# aum_df.columns = ["AUM"]
# aum_df.to_csv(os.path.join("D://draft//",uni_symbol,uni_symbol+"_aum.csv"))
# pnl = aum_df["AUM"] - aum_df["AUM"].shift(1)
# pnl = pnl[pd.notnull(pnl)]
# print("日胜率 ：", round(len(pnl[pnl>0])*1.0/(len(pnl[pnl!=0])),4))



