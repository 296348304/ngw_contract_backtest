import datetime
import traceback
from queue import Queue
import ngwshare as ng
import time
import json
import schedule
import threading
from string import digits
import matplotlib.pyplot as plt
from ngw_contract_backtest.ngw.data.data_api import get_TradeDatetime
from ngw_contract_backtest.ngw.utils.data_util import get_variety_code, isin_TradeDatetimeList
from ngw_contract_backtest.ngw.conn_sql.select_sql import get_total_equities, \
    get_strategyId_stgyId_lastEquity_lastAvailableCash_lastFrozenCash, get_orders, get_positions
from ngw_contract_backtest.ngw.app_api.common import turn_main_contract
from ngw_contract_backtest.ngw.report.risk_metrics import calculate, get_win_rate
from ngw_contract_backtest.ngw.data.cache import DataCache
from ngw_contract_backtest.ngw.utils.freq_util import freq_1m, freq_1m_sim
from ngw_contract_backtest.ngw.utils.freq_util import freq_10s_sim
from ngw_contract_backtest.ngw.utils.date_util import is_trading_day_on_data, str2datetime, return_last_next_tradingDay, \
    get_trading_days, return_last_trading_day, return_next_trading_day
from ngw_contract_backtest.ngw.conn_sql.insert_sql import strategy_basic, insert_performance, insert_values, \
    insert_position
# from ngw_contract_backtest.ngw.websocket.websocketClient import WebSocketClient
from ngw_contract_backtest.ngw.context.context import Context
import ctypes
from pylab import *  # 支持中文
mpl.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False



class StrategyRunner():
    def __init__(self,info=None,initialize=None,create_universe=None,handle_data=None,run_daily=None):
        self.info = info
        self.initialize = initialize
        self.create_universe = create_universe
        self.handle_data = handle_data
        self.run_daily = run_daily
        self.trading_days = get_trading_days()

        self.name = self.info.get('name')
        self.tag = self.info.get('tag')
        self.sort = self.info.get('sort')
        self.init_cash = self.info.get('init_cash')
        self.start = self.info.get('start')
        self.end = self.info.get('end')
        self.is_DayNight = self.info.get('is_DayNight')  # True 夜盘   False 无夜盘
        self.d_start = datetime.datetime.strptime(self.start,'%Y-%m-%d %H:%M:%S')
        self.d_end = datetime.datetime.strptime(self.end,'%Y-%m-%d %H:%M:%S')
        self.start_,self.end_ = return_last_next_tradingDay(start=self.start, end=self.end)
        self.info['start_'] = self.start_
        self.info['end_'] = self.end_
        self.freq = self.info.get('freq')
        self.freq_sim = self.info.get('freq_sim')
        self.run_daily_time = self.info.get('run_daily_time') if self.info.get('run_daily_time') else "07:00:00"
        self.commission_ratio = self.info.get('commission_ratio')
        self.is_toSQL = self.info.get('is_toSQL')
        self.is_simulate = True if self.info.get('is_simulate') else False
        self._universe = self.info.get('universe')
        self._variety = get_variety_code(self._universe[0])
        self.is_fixed = self.info.get('is_fixed')

        self.stgyId = None
        self.universe_lots = None
        self.margin_ratios = None
        self.varieties_id = None
        self.all_varieties = None
        self.all_margin_ratios = None

        self.context = Context(self.info)
        self.cache = DataCache(self.start_,self.end_,self.freq,self._universe)

        self.dates = []
        self.equities = []
        self.equitiesNoComm = []

    def get_marginRatios_Lots(self,_universe):
        universe_lots = {}
        margin_ratios = {}
        varieties_id = {}
        all_varieties_lots = ng.get_all_varieties()
        all_margin_ratios = ng.get_all_margin_ratios()
        if not _universe:
            return universe_lots,margin_ratios,varieties_id,all_varieties_lots,all_margin_ratios
        for i in _universe:
            symbol = i.split('.')[0]
            if 'M' in symbol and symbol[0] != 'M':
                variety_code = symbol.replace('M','')
                symbol = turn_main_contract(variety_code=variety_code)
            if symbol == 'MAM':
                symbol = turn_main_contract(variety_code='MA')
            variety = symbol.translate(str.maketrans('', '', digits))
            variety_ = all_varieties_lots.loc[all_varieties_lots['varietyCode'] == variety]
            varietyId = variety_['id'].tolist()[0]
            lots = variety_['lots'].tolist()[0]
            if self.is_simulate:
                try:
                    margin_ratio = all_margin_ratios.loc[all_margin_ratios['code']==symbol]['ratio'].tolist()[0]
                except:
                    margin_ratio = all_margin_ratios.loc[(all_margin_ratios['varietyID']==varietyId)
                                                         & (all_margin_ratios['code']=='!')]['ratio'].tolist()[-1]
            else:
                margin_ratio = all_margin_ratios.loc[(all_margin_ratios['varietyID'] == varietyId)
                                                     & (all_margin_ratios['code'] == '!')]['ratio'].tolist()[-1]
            universe_lots[i] = int(lots)
            margin_ratios[i] = float(margin_ratio)
            varieties_id[i] = int(varietyId)
        return [universe_lots,margin_ratios,varieties_id,all_varieties_lots,all_margin_ratios]

    # ===============================================================================================
    def initialize_(self):
        try:
            self.strategyBasic_id = strategy_basic(name=self.name, tag=self.tag, sort=self.sort,
                                                   init_cash=self.init_cash,start=self.start,
                                                   end=self.end, freq=self.freq, is_toSQL=self.is_toSQL,
                                                   commission_ratio=self.commission_ratio)
            self.context.strategyBasic_id = self.strategyBasic_id
            details_data = self.get_marginRatios_Lots(self._universe)
            self.context.universe_lots = self.universe_lots = details_data[0]
            self.context.margin_ratios = self.margin_ratios = details_data[1]
            self.context.varieties_id = self.varieties_id = details_data[2]
            self.context.all_varieties = self.all_varieties = details_data[3]
            self.context.all_margin_ratios = self.all_margin_ratios = details_data[4]

            self.context.last_equity = self.info.get('init_cash')
            self.context.cache = self.cache.init_data()
            self.initialize(self.context)
        except:
            print(traceback.format_exc())


    def create_universe_(self):
        try:
            self._universe = self.create_universe(self.context)
            return self._universe
        except:
            print(traceback.format_exc())

    def run_daily_(self):
        try:
            if self.run_daily:
                self.run_daily(self.context)
        except:
            print(traceback.format_exc())

    def handle_data_(self):
        try:
            # 每根bar前:1.更新available_cash 2.检查 是否要强平
            self.context.update_available_cash()
            self.context.check_is_force_position()
            self.handle_data(self.context)
        except:
            print(traceback.format_exc())


    def snapshot(self,t_date):
        equity = self.context.get_equity()
        t_day = str(t_date)[:10]
        todayCommission = self.context.today_commission
        totalCommission = self.context.total_commission
        todayTradetimes = self.context.today_tradetimes
        totalTradetimes = self.context.total_tradetimes
        equityNoComm = equity + totalCommission

        self.dates.append(t_day)
        self.equities.append(equity)
        self.equitiesNoComm.append(equityNoComm)

        self.context.last_equity = equity

        if self.is_toSQL:
            # 插入 positions
            updates_positions = []
            positions = self.context.get_positions()
            for pos, pos_ins in positions.items():
                if pos_ins.get('long') or pos_ins.get('short'):
                    position_ = pos_ins.get('long') if pos_ins.get('long') else pos_ins.get('short')
                    doc = {
                        'id':0,
                        'strategyBasic_id': self.strategyBasic_id,
                        'sort': self.sort,
                        'trading_day': self.dates[-1],

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
                        'update_time':t_day+' 00:00:00'
                    }
                    updates_positions.append(doc)
            insert_position(updates_positions)

            # 插入 金额
            cash = self.context.get_cash()
            cash['equity'] = equity
            cash['equityNoComm'] = equityNoComm
            insert_values(strategyBasic_id=self.strategyBasic_id,sort=self.sort, t_day=t_day,cash=cash)

            # 插入 指标
            risk_ = calculate(self.dates, self.equities, self.equitiesNoComm)
            win_rate = get_win_rate(list(self.context.orders.values()))
            risk_['win_rate'] = win_rate
            risk_['today_commission'] = todayCommission
            risk_['total_commission'] = totalCommission
            risk_['today_tradetimes'] = todayTradetimes
            risk_['total_tradetimes'] = totalTradetimes

            insert_performance(strategyBasic_id=self.strategyBasic_id,sort=self.sort, t_day=t_day,risk=risk_)



    # ===============================================================================================
    def sim_initialize_(self):
        try:
            t_datetime = str(datetime.datetime.now())[:19]
            self.context.now_datetime = t_datetime
            print('{} sim_initialize_'.format(str(datetime.datetime.now())))
            data_ = get_strategyId_stgyId_lastEquity_lastAvailableCash_lastFrozenCash(name=self.name)
            print(data_)
            self.context.strategyBasic_id = self.strategyBasic_id = data_[0]
            self.context.stgyId = self.stgyId = data_[1]
            self.context.last_equity = self.last_equity = data_[2]
            # self.context.init_cash = self.init_cash = data_[3]  # 修改bug available_cash不是init_cash
            self.context.available_cash = self.init_cash = data_[3]
            self.context.frozen_cash = data_[4]
            self.context.total_commission = data_[5]
            self.context.total_tradetimes = data_[6]

            details_data = self.get_marginRatios_Lots(self._universe)
            self.context.universe_lots = self.universe_lots = details_data[0]
            self.context.margin_ratios = self.margin_ratios = details_data[1]
            self.context.varieties_id = self.varieties_id = details_data[2]
            self.context.all_varieties = self.all_varieties = details_data[3]
            self.context.all_margin_ratios = self.all_margin_ratios = details_data[4]

            self.initialize(self.context)

            # 2021-03-02新加，update positions
            self.context.positions = get_positions(strategyBasic_id=self.strategyBasic_id)
            # 修复
            if self.is_fixed:
                self.sim_create_universe_()
        except:
            print(traceback.format_exc())

    def sim_create_universe_(self):
        if is_trading_day_on_data(datetime.datetime.now(), self.trading_days):
            try:
                t_datetime = str(datetime.datetime.now())[:19]
                self.context.now_datetime = t_datetime
                print('{} sim_create_universe_'.format(str(datetime.datetime.now())))
                _universe = self.create_universe(self.context)
                if _universe:
                    self._universe = _universe
                details_data = self.get_marginRatios_Lots(self._universe)
                self.context.universe_lots = self.universe_lots = details_data[0]
                self.context.margin_ratios = self.margin_ratios = details_data[1]
                self.context.varieties_id = self.varieties_id = details_data[2]
                self.context.all_varieties = self.all_varieties = details_data[3]
                self.context.all_margin_ratios = self.all_margin_ratios = details_data[4]

                # 2021-03-02 新加，update positions
                self.context.positions = get_positions(strategyBasic_id=self.strategyBasic_id)

                if self.is_DayNight:
                    # 2021-04-19 新加：添加品种交易日历
                    ld = return_last_trading_day(data=self.trading_days)
                    l2d = str(str2datetime(ld) - datetime.timedelta(days=2))[:10]
                    nd = return_next_trading_day(data=self.trading_days)
                    n2d = str(str2datetime(ld) + datetime.timedelta(days=2))[:10]
                    self.context.TradeDatetimeList = get_TradeDatetime(variety=self._variety, start=l2d, end=n2d)
            except:
                print(traceback.format_exc())
        else:
            print('{} today is not trading day. sim_create_universe_'.format(str(datetime.datetime.now())[:19]))


    def sim_run_daily_(self):
        if is_trading_day_on_data(datetime.datetime.now(), self.trading_days):
            try:
                if self.run_daily:
                    t_datetime = str(datetime.datetime.now())[:19]
                    self.context.now_datetime = t_datetime
                    print('{} run_daily_'.format(str(datetime.datetime.now())))
                    self.run_daily(self.context)
            except:
                print(traceback.format_exc())
        else:
            print('{} today is not trading day. run_daily_'.format(str(datetime.datetime.now())[:19]))


    def sim_handle_data_(self,t_time):
        if is_trading_day_on_data(datetime.datetime.now(), self.trading_days):
            try:
                print('{} sim_handle_data_'.format(str(datetime.datetime.now())))
                t_datetime = str(datetime.datetime.now())[:10] + ' ' + t_time
                self.context.now_datetime = t_datetime
                # 每根bar前:1.更新available_cash 2.检查 是否要强平
                self.context.update_available_cash()
                self.context.check_is_force_position()
                self.handle_data(self.context)
            except:
                print(traceback.format_exc())
        else:
            print('{} today is not trading day. sim_handle_data_'.format(str(datetime.datetime.now())[:19]))



    def sim_night_handle_data_(self, t_time):
        t_datetime = str(datetime.datetime.now())[:10] + ' ' + t_time
        if isin_TradeDatetimeList(datetimeStr=t_datetime, TradeDatetimeList=self.context.TradeDatetimeList):
            try:
                print('{} sim_handle_data_'.format(str(datetime.datetime.now())))
                # t_datetime = str(datetime.datetime.now())[:10] + ' ' + t_time
                self.context.now_datetime = t_datetime
                # 每根bar前:1.更新available_cash 2.检查 是否要强平
                self.context.update_available_cash()
                self.context.check_is_force_position()
                self.handle_data(self.context)
            except:
                print(traceback.format_exc())
        else:
            print('{} today is not trading day. sim_night_handle_data_'.format(str(datetime.datetime.now())[:19]))



    def sim_snapshot(self):
        if is_trading_day_on_data(datetime.datetime.now(), self.trading_days):
            t_day = str(datetime.datetime.now())[:10]

            # 插入 positions
            updates_positions = []
            positions = self.context.get_positions()
            for pos, pos_ins in positions.items():
                if pos_ins.get('long') or pos_ins.get('short'):
                    position_ = pos_ins.get('long') if pos_ins.get('long') else pos_ins.get('short')
                    doc = {
                        'id':0,
                        'strategyBasic_id': self.strategyBasic_id,
                        'sort': self.sort,
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
                        'update_time':str(datetime.datetime.now())[:19]
                    }
                    updates_positions.append(doc)
            insert_position(updates_positions)

            # 插入 金额
            cash = self.context.get_cash()
            equity = self.context.get_equity()

            todayCommission = self.context.today_commission
            totalCommission = self.context.total_commission
            todayTradetimes = self.context.today_tradetimes
            totalTradetimes = self.context.total_tradetimes
            equityNoComm = equity + totalCommission

            cash['equity'] = equity
            cash['equityNoComm'] = equityNoComm
            # print(cash)
            insert_values(strategyBasic_id=self.strategyBasic_id, sort=self.sort, t_day=t_day, cash=cash)

            # 查询dates values
            dates,equities,equitiesNoComm = get_total_equities(strategyBasic_id=self.strategyBasic_id)

            # 插入 指标
            risk_ = calculate(dates, equities, equitiesNoComm)
            win_rate = get_win_rate(get_orders(strategyBasic_id=self.strategyBasic_id))
            risk_['win_rate'] = win_rate
            risk_['today_commission'] = todayCommission
            risk_['total_commission'] = totalCommission
            risk_['today_tradetimes'] = todayTradetimes
            risk_['total_tradetimes'] = totalTradetimes
            print(risk_)
            insert_performance(strategyBasic_id=self.strategyBasic_id,sort=self.sort, t_day=t_day,risk=risk_)

            self.context.last_equity = self.last_equity = equity
            print('{} sim_snapshot'.format(str(datetime.datetime.now())))
        else:
            print('{} today is not trading day. sim_snapshot'.format(str(datetime.datetime.now())[:19]))
    # ===============================================================================================

    def run(self):
        # 模拟
        if self.is_simulate:
            self.sim_initialize_()
            # 每天开盘跑
            schedule.every().day.at(self.run_daily_time).do(self.sim_run_daily_)

            # create_universe 根据是否有夜盘选择晚上或早上8点跑
            if self.is_DayNight:
                schedule.every().day.at('20:00:00').do(self.sim_create_universe_)
            else:
                schedule.every().day.at('08:00:00').do(self.sim_create_universe_)

            # sim_handle_data_
            if self.is_DayNight:
                if self.freq_sim == '10s':
                    for t in freq_10s_sim:
                        schedule.every().day.at(t).do(self.sim_night_handle_data_, t)
                else:
                    for t in freq_1m_sim:
                        schedule.every().day.at(t).do(self.sim_handle_data_, t)
            else:
                if self.freq_sim == '10s':
                    for t in freq_10s_sim:
                        schedule.every().day.at(t).do(self.sim_handle_data_, t)
                else:
                    for t in freq_1m_sim:
                        schedule.every().day.at(t).do(self.sim_handle_data_, t)

            # 打快照
            schedule.every().day.at('15:05:00').do(self.sim_snapshot)

            while True:
                schedule.run_pending()
                time.sleep(1)
        # 回测
        else:
            if self._universe:
                self.run_kline_time()   # K线时间 驱动
                # self.run_util_time()  # 固定时间 驱动
            else:
                self.run_util_time()
            # 画图
            self.run_plot()


    def run_util_time(self):
        self.initialize_()
        t1 = time.time()

        d_start = self.d_start
        d_next = self.d_start
        d_end = self.d_end

        while True:
            # 日循环，大于d_end break
            if d_next > d_end:
                break

            if is_trading_day_on_data(d_next, self.trading_days):
                d_next_min = d_next
                while True:
                    # 分钟循环，大于d_end break
                    if d_next_min > d_end:
                        break
                    # 不是当日date break
                    if str(d_next_min)[:10] > str(d_next)[:10]:
                        break

                    # 每天 09:01:00前 create_universe
                    if str(d_next_min)[11:19] == '09:01:00':
                        # self.universe = self.create_universe_(str(d_next_min)[:10])
                        self.context.now_datetime = str(d_next_min)[:19]
                        self._universe = self.create_universe_()
                        self.run_daily_()
                        self.handle_data_()

                    if str(d_next_min)[11:19] in freq_1m:
                        self.context.now_datetime = str(d_next_min)[:19]
                        self.handle_data_()

                    # 每天 15:00:00后 snapshot
                    if str(d_next_min)[11:19] == '15:00:00':
                        self.context.now_datetime = str(d_next_min)[:19]
                        self.handle_data_()
                        self.snapshot(d_next_min)

                    d_next_min = d_next_min + datetime.timedelta(minutes=1)
            d_next = datetime.datetime.strptime(str(d_next)[:10] + ' 00:00:00',
                                                '%Y-%m-%d %H:%M:%S') + datetime.timedelta(days=1)
        print()
        print('总耗时： ',time.time()-t1)


    def run_kline_time(self):
        self.initialize_()
        t1 = time.time()

        d_start = self.d_start
        d_next = self.d_start
        d_end = self.d_end

        start = int(self.start.replace('-', '').replace(' ', '').replace(':', ''))
        end = int(self.end.replace('-', '').replace(' ', '').replace(':', ''))
        df_data = self.cache.data.get(self._universe[0])
        date_list = df_data.loc[(df_data["time"] >= start) & (df_data["time"] <= end)]["time"].tolist()
        freq_minute_dict = {'1m':1,'5m':5,'15m':15}
        min_ = freq_minute_dict[self.freq]
        date_list = [str(datetime.datetime.strptime(str(i), '%Y%m%d%H%M%S')
                         + datetime.timedelta(minutes=min_))[:19] for i in date_list]

        day_flag = True
        for date in date_list:
            self.context.now_datetime = str(date)[:19]

            if self.is_DayNight and day_flag:
                self._universe = self.create_universe_()
                day_flag = False

            # 每天 09:01:00前 create_universe
            if not self.is_DayNight:
                if str(date)[11:19] == '09:01:00':
                    self._universe = self.create_universe_()

            self.handle_data_()

            # 每天 15:00:00后 snapshot
            if str(date)[11:19] == '15:00:00':
                self.snapshot(date)
                if self.is_DayNight:
                    self._universe = self.create_universe_()


        print()
        print('总耗时： ',time.time()-t1)


    def run_plot(self):
        print('==========================================================')
        print('下单详情')
        for i in self.context.orders.values():
            print(i)
        print('下单次数： ', str(len(self.context.orders.values())))
        print('==========================================================')
        print(len(self.dates),self.dates)
        print(len(self.equities),self.equities)
        risk_ = calculate(self.dates, self.equities, self.equitiesNoComm)
        win_rate = get_win_rate(list(self.context.orders.values()))
        st_year_return = round((risk_['st_acc_return_']/len(self.equities))*250, 4)
        print('年收益率：     ', str(risk_['st_annualized']))
        print('年化收益率：     ', str(risk_['st_annualized']))
        print('策略收益率：     ', str(risk_['st_acc_return_']))
        print('volatility：  ', str(risk_['volatility']))
        print('sharpe：      ', str(risk_['sharpe']))
        print('max_drawdown：', str(risk_['max_drawdown']))
        print('日胜率：        ', str(risk_['daily_win_rate']))
        print('日胜率(不扣手续费)：', str(risk_['daily_win_rate_before']))
        print('总交易次数：        ', str(self.context.total_tradetimes))
        print('总手续费：     ', str(self.context.total_commission))
        print('胜率：         ', str(win_rate))
        print('最后持仓：     ', str(self.context.positions))


        # # 1
        # x = range(len(self.dates))
        # y = [(i/self.init_cash)-1 for i in self.equities]
        # plt.figure(dpi=80, figsize=(12, 6))
        # plt.xticks(x[::6], self.dates[::6], rotation=45)  # 设置稀疏程度
        # plt.grid(alpha=0.5, linestyle="-.")
        # plt.plot(x, y, label=u'portfolio')
        # plt.legend()
        # plt.show()

        # 2
        x = range(len(self.dates))
        y = [(i/self.init_cash)-1 for i in self.equities]
        plt.figure(dpi=80, figsize=(12, 6))
        plt.xticks(x[::15], self.dates[::15], rotation=45)  # 设置稀疏程度
        plt.grid(alpha=0.5, linestyle="-.")
        plt.plot(x, y, label=u'portfolio')

        y2 = [(i/self.init_cash)-1 for i in self.equitiesNoComm]
        plt.plot(x, y2, label=u'portfolio no commission')
        plt.legend()
        plt.show()


        # x = range(len(self.dates))
        # y1 = [(i/self.init_cash)-1 for i in self.equities]
        # y2 = [(i/self.init_cash)-1 for i in self.equitiesNoComm]
        # fig, ax1 = plt.subplots()
        # ax2 = ax1.twinx()  # 做镜像处理
        # ax1.plot(x, y1, 'g-')
        # ax2.plot(x, y2, 'b--')
        # # ax1.set_xlabel('date')
        # # ax1.set_ylabel('portfolio')
        # # ax2.set_ylabel('close')
        # # ax1.figure(dpi=80, figsize=(12, 6))
        # plt.xticks(x[::6], self.dates[::6], rotation=90)  # 设置稀疏程度
        # ax1.grid(alpha=0.2, linestyle="-.")
        # ax2.grid(alpha=0.2, linestyle="-.")
        # plt.legend()
        # plt.show()

        # # 画两个折线用这个
        # x = range(len(self.dates))
        # y1 = [(i/self.init_cash)-1 for i in self.equities]
        # y2 = [(i/self.init_cash)-1 for i in self.equitiesNoComm]
        # fig, ax1 = plt.subplots()
        # plt.figure(dpi=80, figsize=(12, 6))
        # # plt.xticks(x[::6], self.dates[::6], rotation=45)
        # ax2 = ax1.twinx()  # 做镜像处理
        # ax1.plot(x, y1, 'g-')
        # ax2.plot(x, y2, 'b--')
        # ax1.set_xlabel('X data')  # 设置x轴标题
        # ax1.set_ylabel('total_count', color='g')  # 设置Y1轴标题
        # ax2.set_ylabel('bad_rate', color='b')  # 设置Y2轴标题
        # plt.show()

        print()


if __name__ == '__main__':
    pass