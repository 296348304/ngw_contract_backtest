import datetime
import ngshare as ng
import numpy as np
import talib
from ngw_contract_backtest import ngw as api
import pandas as pd


def get_exchange_location(symbol):
    if symbol in ["cuM", "alM", "znM", "pbM", "auM", "agM", "rbM", "wrM",
                  "fuM", "ruM", "buM", "hcM", "niM", "snM", "spM", "ssM", ]:
        return "SHFE"
    elif symbol in ["aM", "bM", "cM", "mM", "yM", "pM", "lM", "vM", "jM", "iM",
                    "jmM", "fbM", "jdM", "ppM", "csM", "egM", "rrM", "ebM", "pgM"]:
        return "DCE"
    elif symbol in ["WHM", "PMM", "CFM", "SRM", "TAM", "OIM", "RIM", "MAM", "FGM",
                    "RSM", "RMM", "JRM", "LRM", "SFM", "SMM", "ZCM", "CYM", "APM",
                    "CJM", "URM", "SAM", "PFM"]:
        return "CZCE"
    elif symbol in ['ICM', 'IFM', 'IHM']:
        return "CFFEX"


def get_all_trade_dates(startday, endday):
    body = {
        "table": 'QT_TradingDayNew',
        "field_list": ['TradingDate', 'IfTradingDay', 'SecuMarket'],
        "alterField": 'TradingDate',
        "startDate": startday,
        "endDate": endday
    }
    data = ng.get_fromDate(body)
    data = data[data.SecuMarket == 83]
    data = data[data.IfTradingDay == 1].reset_index()
    trade_dates = [i[:10] for i in data.TradingDate]
    trade_dates.sort()
    return trade_dates


def get_trade_symbols_info(context):
    symbols = context.symbols
    varietie_infs = ng.get_all_varieties()
    symbol_lots_list = []
    for i in range(0, len(symbols)):
        symbol = symbols[i]
        symbol_lots = varietie_infs[varietie_infs['varietyCode'] == symbol[:-1]]['lots'].iloc[0]
        symbol_lots_list.append(symbol_lots)
    ma5_high = [0] * len(symbols)
    close_high = [0] * len(symbols)
    ma5_low = [0] * len(symbols)
    close_low = [0] * len(symbols)
    signals = [0] * len(symbols)

    main_symbols = [''] * len(symbols)
    df = pd.DataFrame(list(zip(symbols, symbol_lots_list, signals, ma5_high, close_high, ma5_low, close_low, main_symbols)),
                      columns=['symbol', 'lots', 'signals', 'ma5_high', 'close_high', 'ma5_low', 'close_low', 'main_symbols'])
    return df



def initialize(context):
    context.count = 100
    context.symbols = ['cuM', 'agM', 'hcM', 'iM', 'TAM', 'jM', 'ruM']
    context.exchange = ['SHFE', 'SHFE', 'SHFE', 'DCE', 'CZCE', 'DCE', 'SHFE']
    context.freq = '15m'
    context.lever = 2.5
    context.ma5_drow_dn = 1.5 / 100
    context.close_drow_dn = 2 / 100
    context.universe = ['cuM.SHFE', 'agM.SHFE', 'hcM.SHFE', 'iM.DCE', 'TAM.CECE', 'jM.DCE', 'ruM.SHFE']
    context.all_trade_days = get_all_trade_dates('2018-12-01', '2021-12-31')
    context.start_date = '2020-01-01'

    context.symbols_df = get_trade_symbols_info(context)
    # print('context.symbols_df', context.symbols_df)



def create_universe(context):
    # context.universe = ['agM.SHFE']
    pass


def handle_data(context):

    now_datetime = context.get_datetime()
    # 2020-09-30 14:45:00
    print(now_datetime)

    all_trade_days = context.all_trade_days
    all_trade_days_df = pd.DataFrame(all_trade_days, columns=['date'])
    last_trade_days_df = all_trade_days_df[all_trade_days_df['date'] < now_datetime[:10]]  # 上一交易日
    last_trade_day = last_trade_days_df['date'].iloc[-1]  # 上一交易日

    symbols_df = context.symbols_df
    for kk in range(0, symbols_df.shape[0]):
        trade_symbol = symbols_df['symbol'].iloc[kk][:-1]

        main_symbol = symbols_df['main_symbols'].iloc[kk]  # 该品种 记录的主力合约(第一次读取为空)
        if context.start_date != last_trade_day:
            all_live_data = ng.all_contract_price(freq='1d', time=last_trade_day)
            index_list = []
            symbol_str_length = len(trade_symbol)
            for j in range(0, all_live_data.shape[0]):
                # 限定数字月份 ASCII码
                if (all_live_data['symbol'].iloc[j][:symbol_str_length] == trade_symbol) \
                        and (ord(all_live_data['symbol'].iloc[j][symbol_str_length:symbol_str_length+1]) >= 48) \
                        and (ord(all_live_data['symbol'].iloc[j][symbol_str_length:symbol_str_length+1]) <= 57):
                    index_list.append(j)
            all_symbol_data = all_live_data.iloc[index_list]

            index = []
            for i in range(0, all_symbol_data.shape[0]):
                if (all_symbol_data['symbol'].iloc[i][-1] != 'M') and (all_symbol_data['symbol'].iloc[i][-3:] != 'IDX'):
                    index.append(i)
            all_symbol_data_ = all_symbol_data.iloc[index]
            all_symbol_data_1 = all_symbol_data_.sort_values(by='volume', ascending=False)
            main_symbol = all_symbol_data_1['symbol'].iloc[0]
            # symbols_df['main_symbols'].iloc[kk] = main_symbol  # 更新品种主力合约 有可能变化

        # main_symbol_ = main_symbol + '.' + context.exchange
        main_symbol_ = main_symbol + '.' + context.exchange[kk]
        print('main_symbol_', main_symbol_)
        history_data = context.get_history(symbol_exchange=main_symbol_, count=context.count)
        # print('history_data', history_data)
        history_data['ma5'] = talib.SMA(history_data['close'], timeperiod=5)
        close_ma5 = history_data['ma5'].iloc[-1]
        close_ma5_last = history_data['ma5'].iloc[-2]
        history_data['ma20'] = talib.SMA(history_data['close'], timeperiod=20)
        close_ma20 = history_data['ma20'].iloc[-1]
        history_data['ma60'] = talib.SMA(history_data['close'], timeperiod=60)
        close_ma60 = history_data['ma60'].iloc[-1]
        close = history_data['close'].iloc[-1]
        close_last = history_data['close'].iloc[-2]
        # print('history_data1', history_data)

        positions = context.get_positions()
        # print('positions', positions)
        # positions = {'ag2002.SHFE': {'short': {'symbol_exchange': 'ag2002.SHFE', 'symbol': 'ag2002', 'exchange': 'SHFE', 'side': 'short', 'avg_price': 4319.0, 'volume': 92, 'amount': 5960220.0, 'margin': 1013237.4, 'margin_ratio': 0.17, 'lots': 15, 'last_update_price': 4319.0}}}

        symbol_signal = symbols_df['signals'].iloc[kk]
        symbol_lots = symbols_df['lots'].iloc[kk]
        symbol_ma5_high = symbols_df['ma5_high'].iloc[kk]
        symbol_close_high = symbols_df['close_high'].iloc[kk]
        symbol_ma5_low = symbols_df['ma5_low'].iloc[kk]
        symbol_close_low = symbols_df['close_low'].iloc[kk]

        cash = context.get_cash()
        available_cash = cash.get('total_cash') / symbols_df.shape[0] * context.lever  # 当前保证金 可开仓金额(3倍杠杆下)
        # print('trade_symbol', trade_symbol, 'available_cash', available_cash)
        symbol_margin_ratios = context.get_lots_margin_ratio(symbol_exchange=context.universe[kk])[1]
        # print('symbol_margin_ratios', symbol_margin_ratios)
        available_cash_ = min(available_cash, cash.get('available_cash') / symbol_margin_ratios)
        # print('trade_symbol', trade_symbol, 'available_cash_', available_cash_)
        # print('trade_symbol', trade_symbol, 'close', close, 'symbol_lots', symbol_lots)

        if symbol_signal == 0:
            # cash = context.get_cash()
            # signal_amounts = symbols_df[symbols_df['signals'] == 0].shape[0]  # 当前为开仓份数
            # # if signal_amounts == 0:
            # #     available_cash_ = 0  # 份数开满 不能继续开仓
            # # else:
            # #     available_cash = cash.get('available_cash') / signal_amounts * context.lever  # 当前保证金 可开仓金额(3倍杠杆下)
            # #     print('trade_symbol', trade_symbol, 'available_cash', available_cash)
            # #     symbol_margin_ratios = context.get_lots_margin_ratio(symbol_exchange=context.universe[kk])[1]
            # #     print('symbol_margin_ratios', symbol_margin_ratios)
            # #     available_cash_ = min(available_cash, cash.get('available_cash') / symbol_margin_ratios)
            # #     print('trade_symbol', trade_symbol, 'available_cash_', available_cash_)
            condition_1 = close_ma5 > close_ma20
            condition_2 = close_ma20 > close_ma60
            condition_3 = close_ma5 > close_ma5_last
            condition_4 = close > close_last
            if condition_1 and condition_2 and condition_3 and condition_4:
                trade_volumes = int(available_cash_ / (close * symbol_lots))
                context.open_long_market(symbol_exchange=main_symbol_, volume=trade_volumes)
                print('open_long', main_symbol_, trade_volumes)
                symbol_signal = 1  # 更新当前持仓方向 1 多头
                symbol_ma5_high = close_ma5
                symbol_close_high = close
            elif ~condition_1 and ~condition_2 and ~condition_3 and ~condition_4:
                trade_volumes = int(available_cash_ / (close * symbol_lots))
                context.open_short_market(symbol_exchange=main_symbol_, volume=trade_volumes)
                print('open_short', main_symbol_, trade_volumes)
                symbol_signal = -1  # 更新当前持仓方向 -1 空头
                symbol_ma5_low = close_ma5
                symbol_close_low = close
        elif symbol_signal == 1:
            symbol_ma5_high = max(symbol_ma5_high, close_ma5)
            symbol_close_high = max(symbol_close_high, close)
            condition_1 = close_ma20 < close_ma60  # 长期均线拐头 平仓
            condition_2 = (close_ma5 / symbol_ma5_high - 1) <= -context.ma5_drow_dn  # ma5均线下落5%以上
            condition_3 = (close / symbol_close_high - 1) <= -context.close_drow_dn  # close下落5%以上
            if condition_1 or condition_2 or condition_3:
                positions_symbol = list(positions.keys())
                for k in range(0, len(positions_symbol)):
                    symbol_str = positions_symbol[k]
                    if trade_symbol in symbol_str:
                        hold_symbol_str = symbol_str
                        break
                trade_volumes = positions.get(hold_symbol_str).get('long').get('volume')  # 当前合约持仓手数
                context.close_long_market(symbol_exchange=hold_symbol_str, volume=trade_volumes)
                symbol_signal = 0  # 更新当前持仓方向 0 空仓
                print('close_long', hold_symbol_str, trade_volumes)
            else:
                symbol_signal = 1  # 更新当前持仓方向 1 多头
        elif symbol_signal == -1:
            symbol_ma5_low = min(symbol_ma5_low, close_ma5)
            symbol_close_low = min(symbol_close_low, close)
            condition_1 = close_ma20 > close_ma60  # 长期均线拐头 平仓
            condition_2 = (close_ma5 / symbol_ma5_low - 1) >= context.ma5_drow_dn  # ma5均线上涨5%以上
            condition_3 = (close / symbol_close_low - 1) >= context.close_drow_dn  # close上涨5%以上
            if condition_1 or condition_2 or condition_3:
                positions_symbol = list(positions.keys())
                for k in range(0, len(positions_symbol)):
                    symbol_str = positions_symbol[k]
                    if trade_symbol in symbol_str:
                        hold_symbol_str = symbol_str
                        break
                trade_volumes = positions.get(hold_symbol_str).get('short').get('volume')  # 当前合约持仓手数
                context.close_short_market(symbol_exchange=hold_symbol_str, volume=trade_volumes)
                symbol_signal = 0  # 更新当前持仓方向 0 空仓
                print('close_short', hold_symbol_str, trade_volumes)
            else:
                symbol_signal = -1  # 更新当前持仓方向 -1 空头

    # print('耗时3', datetime.datetime.now() - t3)

        symbols_df['signals'].iloc[kk] = symbol_signal
        symbols_df['ma5_high'].iloc[kk] = symbol_ma5_high
        symbols_df['close_high'].iloc[kk] = symbol_close_high
        symbols_df['ma5_low'].iloc[kk] = symbol_ma5_low
        symbols_df['close_low'].iloc[kk] = symbol_close_low
        symbols_df['main_symbols'].iloc[kk] = main_symbol  # 更新品种主力合约 有可能变化

    context.symbols_df = symbols_df
    context.start_date = last_trade_day
    positions = context.get_positions()
    # print('positions1:', positions)
    cash = context.get_cash()
    # print('cash： ', cash)
    equity = context.get_equity()
    # print('总资产： ', equity)

# context.universe = context.symbol + '.' + context.exchange

info={
    'name': '12123',
    'tag': '中风险',
    'sort': 1,
    'init_cash': 2000000,
    "start": '2020-01-01 09:00:00',
    "end": '2020-11-26 15:00:00',
    'freq': '15m',
    'commission_ratio': 0.0003,
    "is_toSQL": False,
    # 'universe': ['cuM.SHFE', 'agM.SHFE', 'hcM.SHFE', 'iM.DCE', 'TAM.CECE', 'jM.DCE', 'ruM.SHFE'],
    'universe': ['agM.SHFE'],
    'is_preload': False,
}
my_strategy = api.create_strategy(info, initialize, create_universe, handle_data)
my_strategy.run()




