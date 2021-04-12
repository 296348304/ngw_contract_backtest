import datetime
import ngshare as ng
import numpy as np
import pandas as pd
from ngw_contract_backtest import ngw as api

def initialize(context):
    context.N = 20
    context.k = 2
    context.count = 35
    context.universe = info['universe'][0]  #'rb2101.SHFE'

    contract_detail = ng.get_contract_detail(symbol=context.universe.split(".")[0],
                                             exchange=context.universe.split(".")[1])
    PARAMS = {
        "sigmamulti": 1,
        "stoploss": 0.005,
        "sgltradecap": 1.0 / 3,
        "gvpctlimit": 0.002,
        "gvpctlimit_cap": 0.004,
        "HLmin": 31,
        "trademinlist":get_trademinlist(),
        "priceStep":contract_detail["priceStep"],
        "multiplier" : contract_detail["lots"],
    }
    context.PARAMS = PARAMS

def create_universe(context):
    pass

def get_trademinlist():
    def datetime_range(startstr, endstr, mindelta):
        # include start and end
        start = pd.to_datetime(startstr)
        end = pd.to_datetime(endstr)
        delta = datetime.timedelta(minutes=mindelta)
        current = start
        while current <= end:
            yield current
            current += delta
    list1 = [dt.strftime('%H:%M:%S') for dt in datetime_range("20201111090000","20201111101500",1)]
    list2 = [dt.strftime('%H:%M:%S') for dt in datetime_range("20201111103100","20201111113000",1)]
    list3 = [dt.strftime('%H:%M:%S') for dt in datetime_range("20201111133100","20201111145500",1)]
    trademinlist = list1+list2+list3
    return trademinlist


def get_nearestprice(price, direction, priceStep):
    if price*1.0/priceStep -int(price*1.0/priceStep) == 0:
        return price
    else:
        downprice = int(price*1.0/priceStep)*priceStep
        upprice = downprice + priceStep
        if direction == "buy":
            return downprice
        if direction == "sell":
            return upprice

def get_nexttradeprice(timenum, context, start = 0):
    navs = context.Perf["Navs"]
    gridbs = context.gridbs
    gvpctlimit = context.gvpctlimit

    RSV = (navs[timenum] - navs[start:timenum + 1].min()) / (navs[start:timenum + 1].max() - navs[start:timenum + 1].min())
    nextsell_p = max(navs[timenum] + RSV * gridbs, navs[timenum] * (1 + gvpctlimit / 2.0))
    nextbuy_p = min(navs[timenum] - (1 - RSV) * gridbs, navs[timenum] * (1 - gvpctlimit / 2.0))
    return nextsell_p, nextbuy_p

def adjust_buysell(context):
    nextsell = context.nextsell
    nextbuy = context.nextbuy
    histmean = context.histmean
    gvpctlimit = context.gvpctlimit
    gvpctlimit_cap = context.gvpctlimit_cap
    nav_0 = context.nav_0
    if nextsell * 1.0 / nextbuy - 1 < gvpctlimit:
        nextsell_new = histmean + (nextsell - histmean) / (nextsell - nextbuy) * nextbuy * gvpctlimit
        nextbuy_new = histmean - (histmean - nextbuy) / (nextsell - nextbuy) * nextbuy * gvpctlimit
        nextsell = nextsell_new
        nextbuy = nextbuy_new
    if nextsell * 1.0 / nextbuy - 1 > gvpctlimit_cap:
        if nav_0 > 1.0 / gvpctlimit_cap:
            nextsell_new = histmean + (nextsell - histmean) / (nextsell - nextbuy) * nextbuy * gvpctlimit_cap
            nextbuy_new = histmean - (histmean - nextbuy) / (nextsell - nextbuy) * nextbuy * gvpctlimit_cap
            nextsell = nextsell_new
            nextbuy = nextbuy_new
    return nextsell,nextbuy

def handle_data(context):
    now_datetime = context.get_datetime()
    print(now_datetime)
    positions = context.get_positions()
    print(positions)
    cash = context.get_cash()
    print('cash： ', cash)
    pnl = context.get_pnl()
    print('pnl： ', pnl)
    equity = context.get_equity()
    print('总资产： ', equity)

    trcols = ["tradepos", "tradeprice", "nextbuy", "nextsell"]
    nexttimestr = (pd.to_datetime(now_datetime)+datetime.timedelta(minutes=1)).strftime('%H:%M:%S')
    nexttimestr = str(now_datetime)[11:19]
    if nexttimestr == "09:01:00":
        context.Perf = pd.DataFrame(index=context.PARAMS["trademinlist"],
                            columns=["Navs", "Pre_Navs", "Stra", "Trade", "Pos", "LastPos",
                                     "sellfee", "buyfee", "PNLpunit", "PNL", "stopflag",
                                     "TotalPNL", "tradepos", "tradeprice", "nextbuy", "nextsell",
                                     "histmean", "upbound", "downbound"])
        history_data = context.get_history(symbol_exchange=context.universe, count=2)
        # print(history_data)
        context.posrecord = pd.DataFrame(columns=trcols)
        context.traderecord = pd.DataFrame(columns=trcols)

        context.Perf["Navs"][0] = history_data["settlement"][0]
        context.Perf["Navs"][1] = history_data["close"][1]
        context.Perf["Pre_Navs"][0] = context.Perf["Navs"][0]
        context.Perf["Pre_Navs"][1] = context.Perf["Navs"][0]
        context.Perf["Pos"][0] = 0
        context.Perf["Pos"][1] = 0
        context.Perf["PNL"][0] = 0
        context.Perf["PNL"][1] = 0
        context.Perf["PNLpunit"][0] = 0
        context.Perf["PNLpunit"][1] = context.Perf["Navs"][1] - context.Perf["Navs"][0]
        maxaum = context.get_equity()/context.margin_ratios.get(context.universe)
        aum = min(info["init_cash"] / 0.2, maxaum)  # wait for fix
        context.posmax = int(aum * 1.0 / history_data["close"][1] / context.PARAMS["multiplier"])
        context.stoploss = -1 * context.PARAMS["stoploss"] * aum
        context.sglpos = int(context.PARAMS["sgltradecap"] * context.posmax)
        context.stopsignal = 0
        context.gvpctlimit = context.PARAMS["gvpctlimit"]
        context.gvpctlimit_cap = context.PARAMS["gvpctlimit_cap"]
        context.sigmamulti = context.PARAMS["sigmamulti"]
        context.HLmin = context.PARAMS["HLmin"]
        context.priceStep = context.PARAMS["priceStep"]
        context.minb4start = context.PARAMS["trademinlist"][context.HLmin-1]  # "09:30:00"
        context.nav_0 = context.Perf["Navs"][1]

    elif nexttimestr in context.PARAMS["trademinlist"]:
        timestr_i = nexttimestr
        timenum = context.PARAMS["trademinlist"].index(timestr_i)

        history_data = context.get_history(symbol_exchange=context.universe, count=1)
        context.Perf["Navs"][timenum] = history_data["close"][0]
        context.Perf["Pre_Navs"][timenum] = context.Perf["Navs"][timenum-1]
        context.Perf["LastPos"][timenum] = context.Perf["Pos"][timenum-1]
        context.Perf["PNLpunit"][timenum] = context.Perf["Navs"][timenum] - context.Perf["Pre_Navs"][timenum]
        context.Perf["PNL"][timenum] = context.Perf["PNLpunit"][timenum] * context.Perf["LastPos"][timenum] * context.PARAMS["multiplier"]
        pnl_up2now = context.Perf["PNL"][:timenum + 1].sum()

        if nexttimestr < context.minb4start:  # "09:30:00"
            context.Perf["Pos"][timenum] = 0
            context.Perf["PNL"][timenum] = 0
            context.Perf["stopflag"][timenum] = 0
        elif nexttimestr == context.minb4start:  # "09:30:00"
            context.nextsell = context.Perf["Navs"][1:context.HLmin].max()
            context.nextbuy = context.Perf["Navs"][1:context.HLmin].min()
            context.histmean = context.Perf["Navs"][1:context.HLmin].mean()
            if context.nextsell - context.nextbuy == 0:
                context.stopsignal = 1
                print("Data Abnormal for {}".format(now_datetime))
            else:
                context.nextsell, context.nextbuy = adjust_buysell(context)
                context.gridbs = (context.nextsell - context.nextbuy) * 2
                rets4std = pd.Series(context.Perf["Navs"][:context.HLmin])
                rets4std = rets4std * 1.0 / rets4std.shift(1) - 1
                timelenth = len(context.PARAMS["trademinlist"])
                context.dailysigma = rets4std.std() * np.sqrt(timelenth - 1)
                context.upbound = max(context.nav_0 * np.exp(context.sigmamulti * context.dailysigma), context.nextsell)
                context.downbound = min(context.nav_0 * np.exp(-context.sigmamulti * context.dailysigma), context.nextbuy)

                context.Perf["upbound"][context.HLmin-1] = context.upbound
                context.Perf["downbound"][context.HLmin-1] = context.downbound
                context.Perf["histmean"][context.HLmin-1] = context.histmean

                context.nextsell_0 = get_nearestprice(context.nextsell, "sell", context.priceStep)
                context.nextbuy_0 = get_nearestprice(context.nextbuy, "buy", context.priceStep)

                context.Perf["nextsell"][context.HLmin-1] = context.nextsell_0
                context.Perf["nextbuy"][context.HLmin - 1] = context.nextbuy_0
                context.Perf["Pos"][context.HLmin - 1] = 0
                context.Perf["stopflag"][context.HLmin - 1] = context.stopsignal
        elif nexttimestr == "14:55:00":
            context.Perf.loc["14:55:00","Pos"] = 0
            if context.Perf["Pos"][timenum] != context.Perf["Pos"][timenum - 1]:
                traderecord_i = pd.DataFrame(index=[timestr_i], columns=trcols)
                traderecord_i.loc[timestr_i, "tradepos"] = context.Perf["Pos"][timenum] - context.Perf["LastPos"][timenum]
                traderecord_i.loc[timestr_i, "tradeprice"] = context.Perf["Navs"][timenum]
                traderecord_i.loc[timestr_i, "nextsell"] = "dailyclose"
                traderecord_i.loc[timestr_i, "nextbuy"] = "dailyclose"
                context.posrecord = context.posrecord.append(traderecord_i)
            if len(context.posrecord) != 0:
                tradeidx = context.posrecord.index
                context.Perf.loc[tradeidx, trcols] = context.posrecord
            # context.Perf.to_csv("D://draft//"+context.universe.split(".")[0]+"_"+str(now_datetime)[:10]+".csv")
            # print(context.get_equity())
            # print(context.posrecord)
        elif pnl_up2now <= context.stoploss:
            if context.stopsignal != 1:
                context.stopsignal = 1
                context.Perf["stopflag"][timenum] = context.stopsignal
                stoptime = timestr_i
                context.Perf["Pos"][timenum] = 0
                traderecord_i = pd.DataFrame(index=[timestr_i], columns=trcols)
                traderecord_i.loc[timestr_i, "tradepos"] = context.Perf["Pos"][timenum] - context.Perf["LastPos"][timenum]
                traderecord_i.loc[timestr_i, "tradeprice"] = context.Perf["Navs"][timenum]
                traderecord_i.loc[timestr_i, "nextsell"] = "stoploss"
                traderecord_i.loc[timestr_i, "nextbuy"] = "stoploss"
                context.posrecord = context.posrecord.append(traderecord_i)
                context.traderecord = pd.DataFrame(columns=trcols)
            else:
                pass
        elif context.stopsignal != 1:
            if len(context.traderecord) == 0:
                if context.Perf["Navs"][timenum] >= context.nextsell_0:
                    traderecord_i = pd.DataFrame(index=[timestr_i], columns=trcols)
                    traderecord_i.loc[timestr_i, "tradeprice"] = context.Perf["Navs"][timenum]
                    tradepos = -1.0 * int((context.nextsell_0 - context.histmean) / (context.upbound - context.histmean) * 1.0 * context.posmax)
                    traderecord_i.loc[timestr_i, "tradepos"] = max(-1.0 * context.sglpos, tradepos)
                    nextsell_p, nextbuy_p = get_nexttradeprice(timenum, context)
                    traderecord_i.loc[timestr_i, "nextsell"] = get_nearestprice(nextsell_p, "sell", context.priceStep)
                    traderecord_i.loc[timestr_i, "nextbuy"] = get_nearestprice(nextbuy_p, "buy", context.priceStep)
                    context.posrecord = context.posrecord.append(traderecord_i)
                    context.traderecord = context.traderecord.append(traderecord_i)
                    context.Perf["Trade"][timenum] = max(-1.0 * context.sglpos, tradepos)
                if context.Perf["Navs"][timenum] <= context.nextbuy_0:
                    traderecord_i = pd.DataFrame(index=[timestr_i], columns=trcols)
                    traderecord_i.loc[timestr_i, "tradeprice"] = context.Perf["Navs"][timenum]
                    tradepos = 1.0 * int((context.histmean - context.nextbuy_0) / (context.histmean - context.downbound) * 1.0 * context.posmax)
                    traderecord_i.loc[timestr_i, "tradepos"] = min(1.0 * context.sglpos, tradepos)
                    nextsell_p, nextbuy_p = get_nexttradeprice(timenum, context)
                    traderecord_i.loc[timestr_i, "nextsell"] = get_nearestprice(nextsell_p, "sell", context.priceStep)
                    traderecord_i.loc[timestr_i, "nextbuy"] = get_nearestprice(nextbuy_p, "buy", context.priceStep)
                    context.posrecord = context.posrecord.append(traderecord_i)
                    context.traderecord = context.traderecord.append(traderecord_i)
                    context.Perf["Trade"][timenum] = min(1.0 * context.sglpos, tradepos)
            else:
                lasttrade_i = context.traderecord.iloc[len(context.traderecord) - 1, :]
                lastpos_i = lasttrade_i["tradepos"]
                nextbuy_i = lasttrade_i["nextbuy"]
                nextsell_i = lasttrade_i["nextsell"]
                if lastpos_i > 0:
                    if context.Perf["Navs"][timenum] >= nextsell_i:
                        context.Perf["Trade"][timenum] = -1 * lastpos_i
                        context.traderecord = context.traderecord.iloc[:len(context.traderecord) - 1, :]
                        traderecord_i = pd.DataFrame(index=[timestr_i], columns=trcols)
                        traderecord_i.loc[timestr_i, "tradepos"] = -1 * lastpos_i
                        traderecord_i.loc[timestr_i, "tradeprice"] = context.Perf["Navs"][timenum]
                        nextsell_p, nextbuy_p = get_nexttradeprice(timenum, context)
                        context.nextsell_0 = get_nearestprice(nextsell_p, "sell", context.priceStep)
                        context.nextbuy_0 = get_nearestprice(nextbuy_p, "buy", context.priceStep)
                        context.histmean = context.Perf["Navs"][1:timenum].mean()
                        context.upbound = max(context.nav_0 * np.exp(context.sigmamulti * context.dailysigma), nextsell_p)
                        context.downbound = min(context.nav_0 * np.exp(-context.sigmamulti * context.dailysigma), nextbuy_p)
                        context.Perf["upbound"][timenum] = context.upbound
                        context.Perf["downbound"][timenum] = context.downbound
                        context.Perf["histmean"][timenum] = context.histmean
                        traderecord_i.loc[timestr_i, "nextsell"] = context.nextsell_0
                        traderecord_i.loc[timestr_i, "nextbuy"] = context.nextbuy_0
                        context.posrecord = context.posrecord.append(traderecord_i)
                    if context.Perf["Navs"][timenum] <= nextbuy_i:
                        traderecord_i = pd.DataFrame(index=[timestr_i], columns=trcols)
                        traderecord_i.loc[timestr_i, "tradeprice"] = context.Perf["Navs"][timenum]
                        tradepos = 1.0 * int((context.histmean - nextbuy_i) / (context.histmean - context.downbound) * 1.0 * context.posmax)
                        traderecord_i.loc[timestr_i, "tradepos"] = min(min(1.0 * context.posmax, tradepos) - lastpos_i, context.sglpos)
                        nextsell_p, nextbuy_p = get_nexttradeprice(timenum, context)
                        traderecord_i.loc[timestr_i, "nextsell"] = get_nearestprice(nextsell_p, "sell", context.priceStep)
                        traderecord_i.loc[timestr_i, "nextbuy"] = get_nearestprice(nextbuy_p, "buy", context.priceStep)
                        context.posrecord = context.posrecord.append(traderecord_i)
                        context.traderecord = context.traderecord.append(traderecord_i)
                        context.Perf["Trade"][timenum] = min(min(1.0 * context.posmax, tradepos) - lastpos_i, context.sglpos)
                if lastpos_i < 0:
                    if context.Perf["Navs"][timenum] >= nextsell_i:
                        traderecord_i = pd.DataFrame(index=[timestr_i], columns=trcols)
                        traderecord_i.loc[timestr_i, "tradeprice"] = context.Perf["Navs"][timenum]
                        tradepos = -1.0 * int((nextsell_i - context.histmean) / (context.upbound - context.histmean) * 1.0 * context.posmax)
                        traderecord_i.loc[timestr_i, "tradepos"] = max(max(-1.0 * context.posmax, tradepos) - lastpos_i,-1.0 * context.sglpos)
                        nextsell_p, nextbuy_p = get_nexttradeprice(timenum, context)
                        traderecord_i.loc[timestr_i, "nextsell"] = get_nearestprice(nextsell_p, "sell", context.priceStep)
                        traderecord_i.loc[timestr_i, "nextbuy"] = get_nearestprice(nextbuy_p, "buy", context.priceStep)
                        context.posrecord = context.posrecord.append(traderecord_i)
                        context.traderecord = context.traderecord.append(traderecord_i)
                        context.Perf["Trade"][timenum] = max(max(-1.0 * context.posmax, tradepos) - lastpos_i, -1.0 * context.sglpos)
                    if context.Perf["Navs"][timenum] <= nextbuy_i:
                        context.Perf["Trade"][timenum] = -1.0 * lastpos_i
                        context.traderecord = context.traderecord.iloc[:len(context.traderecord) - 1, :]
                        traderecord_i = pd.DataFrame(index=[timestr_i], columns=trcols)
                        traderecord_i.loc[timestr_i, "tradepos"] = -1.0 * lastpos_i
                        traderecord_i.loc[timestr_i, "tradeprice"] = context.Perf["Navs"][timenum]
                        nextsell_p, nextbuy_p = get_nexttradeprice(timenum, context)
                        context.nextsell_0 = get_nearestprice(nextsell_p, "sell", context.priceStep)
                        context.nextbuy_0 = get_nearestprice(nextbuy_p, "buy", context.priceStep)
                        context.histmean = context.Perf["Navs"][1:timenum].mean()
                        context.upbound = max(context.nav_0 * np.exp(context.sigmamulti * context.dailysigma),nextsell_p)
                        context.downbound = min(context.nav_0 * np.exp(-context.sigmamulti * context.dailysigma), nextbuy_p)
                        context.Perf["upbound"][timenum] = context.upbound
                        context.Perf["downbound"][timenum] = context.downbound
                        context.Perf["histmean"][timenum] = context.histmean
                        traderecord_i.loc[timestr_i, "nextsell"] = context.nextsell_0
                        traderecord_i.loc[timestr_i, "nextbuy"] = context.nextbuy_0
                        context.posrecord = context.posrecord.append(traderecord_i)
            context.Perf["Pos"][timenum] = context.posrecord["tradepos"][:timenum + 1].sum()
            context.Perf["stopflag"][timenum] = context.stopsignal
        else:
            pass
        if context.Perf["Pos"][timenum] != context.Perf["Pos"][timenum-1]:
            tradepos = context.Perf["Pos"][timenum] - context.Perf["Pos"][timenum-1]
            # tradeprice = price = context.get_price(symbol_exchange=context.universe)
            if context.Perf["Pos"][timenum-1] == 0:
               if context.Perf["Pos"][timenum]>0:
                   context.open_long_market(symbol_exchange=context.universe, volume=abs(tradepos))
               if context.Perf["Pos"][timenum]<0:
                   context.open_short_market(symbol_exchange=context.universe, volume=abs(tradepos))
            if context.Perf["Pos"][timenum-1] > 0:
               if tradepos>0:
                   context.open_long_market(symbol_exchange=context.universe, volume=abs(tradepos))
               if tradepos<0:
                   context.close_long_market(symbol_exchange=context.universe, volume=abs(tradepos))
            if context.Perf["Pos"][timenum-1] < 0:
               if tradepos>0:
                   context.close_short_market(symbol_exchange=context.universe, volume=abs(tradepos))
               if tradepos<0:
                   context.open_short_market(symbol_exchange=context.universe, volume=abs(tradepos))
        # if nexttimestr == "14:43:00":
        #     print(context.get_positions())
        #     print('cash： ', context.get_cash())
        #     print('pnl： ', context.get_pnl())
        #     print('总资产： ', context.get_equity())

    else:
        pass

    # price = context.get_price(symbol_exchange=context.universe)
    # print(price)

    positions = context.get_positions()
    print(positions)
    cash = context.get_cash()
    print('cash： ', cash)
    pnl = context.get_pnl()
    print('pnl： ', pnl)
    equity = context.get_equity()
    print('总资产： ', equity)
    print()

info={
    'name':'RSV网格',
    'tag':'中风险',
    'sort': 1,
    'init_cash':1000000,
    # "start": '2020-10-01 09:00:00',
    # "end": '2020-10-09 15:00:00',
    "start": '2020-09-01 09:00:00',
    "end": '2020-10-09 15:00:00',
    'freq':'1m',
    'force_position_ratio':0.05,
    # 'universe':['MAM.CZCE'],
    'universe': ['rbM.SHFE'],
    'commission_ratio':0.0003/2.0,
    "is_toSQL": True,

    "is_simulate":True
}
my_strategy = api.create_strategy(info,initialize,create_universe,handle_data)
my_strategy.run()


