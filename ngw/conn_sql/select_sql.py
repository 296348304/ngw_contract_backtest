import datetime
import pandas as pd
import decimal

from ngw_contract_backtest.ngw.utils.date_util import return_last_trading_day
from pymysql import *

from ngw_contract_backtest.ngw.constants import MYSQL_HOST, MYSQL_PORT, \
    MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
try:
    from ngw_contract_backtest.ngw.constants import LOGFLAG
    if LOGFLAG:
        from ngw_contract_backtest.ngw.utils.log_util import print
except:
    LOGFLAG = False

def conn_mysql(sql=None):
    conn = connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DATABASE,
                   charset='utf8')
    cs1 = conn.cursor()
    cs1.execute(sql)

    data = cs1.fetchall()
    # logger.info('读取成功.')
    # print('读取成功.')

    cs1.close()
    conn.close()
    return data


# 获取 strategyId 和 stgyId
def get_strategyId_stgyId_lastEquity_lastAvailableCash_lastFrozenCash(name=None):
    sql = """select strategyBasic_id from strategyBasic where name='{}' order by create_time desc;""".format(name)
    strategyBasic_id = conn_mysql(sql)[0][0]

    sql = """select stgyId from basicTab where basicId={};""".format(strategyBasic_id)
    stgyId = conn_mysql(sql)[0][0]

    sql = """select equity,equityNoComm,available_cash,frozen_cash from strategyValues where strategyBasic_id = {} and 
    trading_day=(select max(trading_day) from strategyValues where strategyBasic_id = {});"""\
        .format(strategyBasic_id,strategyBasic_id)
    data_ = conn_mysql(sql=sql)[0]
    equity = data_[0]
    # equityNoComm = data_[1]
    available_cash = data_[2]
    frozen_cash = data_[3]

    sql = """select total_commission,total_tradetimes from performance where strategyBasic_id = {} and 
    trading_day=(select max(trading_day) from performance where strategyBasic_id = {});"""\
        .format(strategyBasic_id,strategyBasic_id)
    data_ = conn_mysql(sql=sql)[0]
    totalCommission = data_[0]
    totalTradetimes = data_[1]

    return [int(strategyBasic_id),int(stgyId),float(equity),float(available_cash),float(frozen_cash),
            float(totalCommission), int(totalTradetimes)]




# 获取所有的 dates,equities
def get_total_equities(strategyBasic_id=None):
    sql = """select trading_day,equity,equityNoComm from strategyValues where strategyBasic_id = {};""".format(strategyBasic_id)
    # print(sql)
    data = conn_mysql(sql=sql)

    dates = []
    equities = []
    equitiesNoComm = []
    for i in data:
        dates.append(str(i[0]))
        equities.append(round(float(i[1]),4))
        equitiesNoComm.append(round(float(i[2]),4))

    return dates,equities,equitiesNoComm


# 获取所有的 dates,equities
def get_orders(strategyBasic_id=None):
    sql = """select symbol,varietyId,exchange,side,avg_price,filled_volume,pnl,commission from ordersList 
    where strategyBasic_id = {};""".format(strategyBasic_id)
    # print(sql)
    data = conn_mysql(sql=sql)
    data_ = []
    for i in data:
        temp_ = []
        for j in i:
            if isinstance(j, decimal.Decimal):
                temp_.append(float(j))
            elif isinstance(j, datetime.datetime):
                temp_.append(str(j))
            else:
                temp_.append(j)
        data_.append(temp_)
    df_data = pd.DataFrame(data_)
    df_data.columns = ['symbol','varietyId','exchange','side','avg_price','filled_volume','pnl','commission']
    df_data_dict = df_data.to_dict(orient='records')
    return df_data_dict


# # 获取上一日的equity
# def get_last_equity(strategyBasic_id=None):
#     sql = """select equity from strategyValues where strategyBasic_id = {} and
#     trading_day=(select max(trading_day) from strategyValues where strategyBasic_id = {});"""\
#         .format(strategyBasic_id,strategyBasic_id)
#     data = conn_mysql(sql=sql)[0][0]
#     return data


def get_positions(strategyBasic_id=None):
    last_trading_day = str(return_last_trading_day())[:10]
    sql = """select symbol_exchange,symbol,varietyId,exchange,exchangeId,side,avg_price,volume,amount,
    margin,margin_ratio,lots,last_update_price from positionsList where strategyBasic_id = {} and trading_day >='{}';"""\
        .format(strategyBasic_id,last_trading_day)
    # print(sql)
    data = conn_mysql(sql=sql)
    if data:
        data_ = []
        for i in data:
            temp_ = []
            for j in i:
                if isinstance(j, decimal.Decimal):
                    temp_.append(float(j))
                elif isinstance(j, datetime.datetime):
                    temp_.append(str(j))
                else:
                    temp_.append(j)
            data_.append(temp_)
        df_data = pd.DataFrame(data_)
        df_data.columns = ['symbol_exchange','symbol','varietyId','exchange','exchangeId','side','avg_price','volume','amount','margin','margin_ratio','lots','last_update_price']
        # print(df_data)

        positions_dict = {}
        for ii in df_data.index:
            doc = dict(df_data.loc[ii])
            # print(doc)
            temp_pos = {}
            if doc['side'] == 'long':
                temp_pos['long'] = doc
            else:
                temp_pos['short'] = doc
            # print(positions_dict)
            positions_dict[doc['symbol_exchange']] = temp_pos
        return positions_dict
    else:
        return {}


if __name__ == '__main__':
    from pprint import pprint
    import time
    t1 = time.time()

    a = get_positions(strategyBasic_id=757376836023159)
    print(a)

    positions =  {'TA105.CZCE': {'short': {'symbol_exchange': 'TA105.CZCE', 'symbol': 'TA105', 'varietyId': 35, 'exchange': 'CZCE', 'exchangeId': 6, 'side': 'long', 'avg_price': 4575.7922, 'volume': 44.0, 'amount': 1006674.2769999995, 'margin': 60376.8, 'margin_ratio': 0.06, 'lots': 5, 'last_update_price': 4574.0}}}


    # a = get_strategyId_stgyId_lastEquity_lastAvailableCash_lastFrozenCash(name='DynamicRSV网格_buM.SHFE')
    # print(a)



    # def get_win_rate(orders=None):
    #     win_times = 0
    #     for order in orders:
    #         if order['side'] in ['close_long', 'close_short']:
    #             pnl = order['pnl']
    #             commission = order['commission']
    #             if pnl > 2 * commission:
    #                 win_times += 1
    #     try:
    #         win_rate = round(win_times / len(orders), 4)
    #     except:
    #         win_rate = 0
    #     return win_rate
    #
    # a = get_orders(strategyBasic_id=705398160193077)
    # print(a)
    #
    # b = get_win_rate(orders=a)
    # print(b)
    #
    # print(time.time()-t1)