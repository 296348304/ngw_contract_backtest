import random
import datetime
import traceback
from pymysql import *
from ngw_contract_backtest.ngw.constants import MYSQL_HOST, MYSQL_PORT, \
    MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
try:
    from ngw_contract_backtest.ngw.constants import LOGFLAG
    if LOGFLAG:
        from ngw_contract_backtest.ngw.utils.log_util import print
except:
    LOGFLAG = False

def insert_mysql(sql):
    conn = connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD,database=MYSQL_DATABASE, charset='utf8')
    cs1 = conn.cursor()

    cs1.execute(sql)
    conn.commit()
    # logger.info('插入成功.')
    # print('插入成功.')
    cs1.close()
    conn.close()




# --------------------------------------------------------------------------------------------------------
# 初始strategyBasic_id 入库
def strategy_basic(name=None,tag=None,sort=None,init_cash=None,start=None,end=None,freq=None,
                   commission_ratio=None,is_toSQL=None):
    strategyBasic_id = int("".join(random.choice("0123456789") for _ in range(15)))

    name = name
    tag = tag
    sort = sort
    init_cash = init_cash
    freq = freq
    commission_ratio = commission_ratio

    start_date = start
    end_date = end
    create_time = str(datetime.datetime.now())[:19]

    sql = """insert into strategyBasic values(0,{},'{}',{},{},{},'{}',{},'{}','{}','{}')""".format(
        strategyBasic_id, name, tag, sort, init_cash, freq, commission_ratio,
        start_date, end_date, create_time)

    if is_toSQL:
        insert_mysql(sql)
        print('{} {} {} {} {} strategy_basic 插入成功！'.format(name, strategyBasic_id, init_cash, start_date, end_date))
    else:
        pass
        # print('(测试) {} {} {} {} {} strategy_basic 插入成功！'.format(name, strategyBasic_id, init_cash, start_date, end_date))
    return strategyBasic_id



# 插入order
def insert_order(strategyBasic_id=None,sort=None,order=None,is_toSQL=None):
    # print(order)
    strategyBasic_id = strategyBasic_id
    sort = sort

    create_time = order.get('create_time')
    order_id = order.get('order_id')
    symbol_exchange = order.get('symbol_exchange')
    symbol = order.get('symbol')
    varietyId = order.get('varietyId')
    exchange = order.get('exchange')
    exchangeId = order.get('exchangeId')
    side = order.get('side')
    sideId = order.get('sideId')

    avg_price = order.get('avg_price')
    initial_volume = order.get('initial_volume')
    filled_volume = order.get('filled_volume')
    filled_amount = order.get('filled_amount')
    order_percent = order.get('order_percent')
    lots = order.get('lots')
    status = order.get('status')
    commission = order.get('commission')

    margin = order.get('margin') if order.get('margin') else 0
    margin_ratio = order.get('margin_ratio') if order.get('margin_ratio') else 0
    return_margin = order.get('return_margin') if order.get('return_margin') else 0
    pnl = order.get('pnl') if order.get('pnl') else 0
    pnl_ratio =order.get('pnl_ratio') if order.get('pnl_ratio') else 0
    is_force = order.get('is_force') if order.get('is_force') else 0

    other = order.get('other')
    complete_time = order.get('complete_time')


    sql = """insert into ordersList values(0,{},{},'{}',{},'{}','{}',{},'{}',{},'{}',{}, {},{},{},{},{},{},'{}',{}, {},{},{},{},{},{},{},'{}')""".format(
        strategyBasic_id,sort,create_time,order_id,symbol_exchange,symbol,varietyId,exchange,exchangeId,side,
        sideId,avg_price,initial_volume,filled_volume,filled_amount,order_percent,lots,status,commission,
        margin,margin_ratio,return_margin,pnl,pnl_ratio,is_force,other,complete_time)
    # print(sql)
    if is_toSQL:
        insert_mysql(sql)
        print('{} {} {} {} {} order 插入成功！'.format(symbol_exchange,side,avg_price,filled_volume,commission))
    else:
        pass
        # print('(测试){} {} {} {} {} order 插入成功！'.format(symbol_exchange,side,avg_price,filled_volume,commission))



def insert_position(updates_positions=None):
    if len(updates_positions) > 0:
        val_ = ','.join([str(tuple(i.values())) for i in updates_positions])
        sql = """insert into positionsList values {};""".format(val_)
        try:
            insert_mysql(sql=sql)
            print('批量插入 positions 成功')
        except:
            print(sql)
            print(traceback.format_exc())
            print('批量插入 positions 失败')



# ---------------------------------------------------------------------------------------------
def is_None(i):
    if i is None:
        return 'NULL'
    else:
        return i

def insert_performance(strategyBasic_id=None,sort=None, t_day=None, risk=None):
    strategyBasic_id = strategyBasic_id
    sort = sort
    trading_day = t_day

    st_d_return = is_None(risk.get('st_d_return'))
    st_d_return_value = is_None(risk.get('st_d_return_value'))
    annualized_return = is_None(risk.get('st_annualized'))
    st_c_return = is_None(risk.get('st_acc_return_'))
    volatility = is_None(risk.get('volatility'))
    sharpe_ratio = is_None(risk.get('sharpe'))
    max_drawdown = is_None(risk.get('max_drawdown')[0])
    max_drawdown_start = is_None(risk.get('max_drawdown')[1])
    max_drawdown_end = is_None(risk.get('max_drawdown')[2])
    daily_win_rate = is_None(risk.get('daily_win_rate'))
    daily_win_rate_before = is_None(risk.get('daily_win_rate_before'))
    today_commission = is_None(risk.get('today_commission'))
    total_commission = is_None(risk.get('total_commission'))
    today_tradetimes = is_None(risk.get('today_tradetimes'))
    total_tradetimes = is_None(risk.get('total_tradetimes'))
    win_rate = is_None(risk.get('win_rate'))
    other = 0
    update_time = trading_day+' 00:00:00'

    if max_drawdown_start=='NULL' and max_drawdown_end=='NULL':
        sql = """insert into performance values(0, {},{},'{}',{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},'{}')""".format(
            strategyBasic_id,sort, trading_day, st_d_return, st_d_return_value, annualized_return,st_c_return,volatility,
            sharpe_ratio,max_drawdown, max_drawdown_start, max_drawdown_end, daily_win_rate, win_rate,
            daily_win_rate_before, today_commission, total_commission, today_tradetimes, total_tradetimes, other, update_time)
    else:
        sql = """insert into performance values(0, {},{},'{}',{},{},{},{},{},{},{},'{}','{}',{},{},{},{},{},{},{},{},'{}')""".format(
            strategyBasic_id, sort, trading_day, st_d_return, st_d_return_value, annualized_return, st_c_return,volatility,
            sharpe_ratio, max_drawdown, max_drawdown_start, max_drawdown_end, daily_win_rate, win_rate,
            daily_win_rate_before, today_commission, total_commission, today_tradetimes, total_tradetimes, other, update_time)
    # print(sql)
    insert_mysql(sql)
    print('{}  performance 插入成功'.format(trading_day))



def insert_values(strategyBasic_id=None,sort=None,t_day=None,cash=None):
    strategyBasic_id = strategyBasic_id
    sort = sort
    trading_day = t_day

    available_cash = cash.get('available_cash')
    frozen_cash = cash.get('frozen_cash')
    total_cash = cash.get('total_cash')
    equity = cash.get('equity')
    equityNoComm = cash.get('equityNoComm')

    update_time = t_day+' 00:00:00'

    sql = """insert into strategyValues values(0, {},{},'{}',{},{},{},{},{},'{}')""".format(
        strategyBasic_id, sort, trading_day, available_cash, frozen_cash, total_cash, equity, equityNoComm, update_time)

    insert_mysql(sql)
    print('{} 每天插入 values 成功！available_cash:{} frozen_cash:{} equity:{}'.format(t_day, available_cash, frozen_cash, equity))










if __name__ == '__main__':
    from pprint import pprint
    import datetime

    positions =  {'TA105.CZCE': {'short': {'symbol_exchange': 'TA105.CZCE', 'symbol': 'TA105', 'varietyId': 35, 'exchange': 'CZCE', 'exchangeId': 6, 'side': 'short', 'avg_price': 4575.7922, 'volume': 44.0, 'amount': 1006674.2769999995, 'margin': 60376.8, 'margin_ratio': 0.06, 'lots': 5, 'last_update_price': 4574.0}}}

    updates_positions = []
    for pos, pos_ins in positions.items():
        if pos_ins.get('long') or pos_ins.get('short'):
            position_ = pos_ins.get('long') if pos_ins.get('long') else pos_ins.get('short')
            doc = {
                'id': 0,
                'strategyBasic_id': 757376836023159,
                'sort': 1,
                'trading_day': str(datetime.datetime.now())[:10],

                'symbol_exchange': position_['symbol_exchange'],
                'symbol': position_['symbol'],
                'varietyId': position_['varietyId'],
                'exchange': position_['exchange'],
                'exchangeId': position_['exchangeId'],
                'side': position_['side'],
                'avg_price': position_['avg_price'],
                'volume': position_['volume'],
                'amount': position_['amount'],
                'margin': position_['margin'],
                'margin_ratio': position_['margin_ratio'],
                'lots': position_['lots'],
                'last_update_price': position_['last_update_price'],
                'update_time': str(datetime.datetime.now())[:19]
            }
            updates_positions.append(doc)
    insert_position(updates_positions)


