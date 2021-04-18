import random
import time
from string import digits
import datetime
from ngw_contract_backtest.ngw.conn_sql.insert_sql import insert_order
from ngw_contract_backtest.ngw.data.data_api import get_hisBar, contract_depth, get_price, get_all_hisBar, celery_post
from ngw_contract_backtest.ngw.app_api.common import turn_main_contract
from ngw_contract_backtest.ngw.utils.date_util import str2datetime
try:
    from ngw_contract_backtest.ngw.constants import LOGFLAG
    if LOGFLAG:
        from ngw_contract_backtest.ngw.utils.log_util import print
except:
    LOGFLAG = False

class Context(object):
    def __init__(self, info=None):
        self.exchange2id_dict = {'CFFEX': 3, 'SHFE': 4, 'DCE': 5, 'CZCE': 6, 'INE': 15}
        self.side2id_dict = {'open_long':1,'open_short':2,'close_long':3,'close_short':4}
        self.info = info
        self.cache = {}

        self.strategyBasic_id = None
        self.universe_lots = None
        self.margin_ratios = None
        self.varieties_id = None
        self.all_varieties = None
        self.all_margin_ratios = None
        self.stgyId = None
        self.last_equity = None

        self.sort = self.info.get('sort')
        self.tag = self.info.get('tag')
        self.commission_ratio = self.info.get('commission_ratio')
        self.freq = self.info.get('freq')
        self.start_ = self.info.get('start_')
        self.end_ = self.info.get('end_')
        self.is_toSQL = self.info.get('is_toSQL')
        self.is_simulate = self.info.get('is_simulate')

        self.now_datetime = None
        self.available_cash = self.info.get('init_cash')
        self.frozen_cash = 0

        self.positions = {}
        self.orders = {}
        self.total_commission = 0

        # 2021-02-24 交易次数  日胜率 扣手续费 前后
        # self.mid_datetime = None
        self.today_commission = 0
        self.today_tradetimes = 0
        self.total_tradetimes = 0


    def get_lots_margin_ratio(self,symbol_exchange=None):
        lots = self.universe_lots.get(symbol_exchange)
        margin_ratio = self.margin_ratios.get(symbol_exchange)
        varietyId = self.varieties_id.get(symbol_exchange)
        if not lots and not margin_ratio:
            symbol = symbol_exchange.split('.')[0]
            if 'M' in symbol and symbol[0] != 'M':
                variety_code = symbol.replace('M', '')
                symbol = turn_main_contract(variety_code=variety_code)
            if symbol == 'MAM':
                symbol = turn_main_contract(variety_code='MA')
            variety = symbol.translate(str.maketrans('', '', digits))
            variety_ = self.all_varieties.loc[self.all_varieties['varietyCode'] == variety]
            varietyId = variety_['id'].tolist()[0]
            lots = variety_['lots'].tolist()[0]
            if self.is_simulate:
                try:
                    margin_ratio = self.all_margin_ratios.loc[self.all_margin_ratios['code']==symbol]['ratio'].tolist()[0]
                except:
                    margin_ratio = self.all_margin_ratios.loc[(self.all_margin_ratios['varietyID']==varietyId)
                                                         & (self.all_margin_ratios['code']=='!')]['ratio'].tolist()[-1]
            else:
                margin_ratio = self.all_margin_ratios.loc[(self.all_margin_ratios['varietyID'] == varietyId)
                                                     & (self.all_margin_ratios['code'] == '!')]['ratio'].tolist()[-1]
            self.universe_lots[symbol_exchange] = lots
            self.margin_ratios[symbol_exchange] = margin_ratio
            self.varieties_id[symbol_exchange] = varietyId

        return lots,margin_ratio,varietyId

    def open_long_market(self, symbol_exchange=None, volume=None, level=None):
        if volume <= 0:
            print('错误! {}  volume<=0'.format(volume))
            return
        price = self.get_price(symbol_exchange=symbol_exchange)
        if self.is_simulate:
            depth = self.get_depth(symbol_exchange=symbol_exchange)
            price = float(depth.get('ask')[0][0])
        return self.open_long(symbol_exchange=symbol_exchange, price=price, volume=volume, level=level)
    def open_short_market(self, symbol_exchange=None, volume=None, level=None):
        if volume <= 0:
            print('错误! {}  volume<=0'.format(volume))
            return
        price = self.get_price(symbol_exchange=symbol_exchange)
        if self.is_simulate:
            depth = self.get_depth(symbol_exchange=symbol_exchange)
            price = float(depth.get('ask')[0][0])
        return self.open_short(symbol_exchange=symbol_exchange, price=price, volume=volume, level=level)
    def close_long_market(self, symbol_exchange=None, volume=None, level=None):
        if volume <= 0:
            print('错误! {}  volume<=0'.format(volume))
            return
        price = self.get_price(symbol_exchange=symbol_exchange)
        if self.is_simulate:
            depth = self.get_depth(symbol_exchange=symbol_exchange)
            price = float(depth.get('bid')[0][0])
        return self.close_long(symbol_exchange=symbol_exchange, price=price, volume=volume, level=level)
    def close_short_market(self, symbol_exchange=None, volume=None, level=None):
        if volume <= 0:
            print('错误! {}  volume<=0'.format(volume))
            return
        price = self.get_price(symbol_exchange=symbol_exchange)
        if self.is_simulate:
            depth = self.get_depth(symbol_exchange=symbol_exchange)
            price = float(depth.get('bid')[0][0])
        return self.close_short(symbol_exchange=symbol_exchange, price=price, volume=volume, level=level)

    def open_long(self, symbol_exchange=None, price=None, volume=None, level=None):
        if price <= 0:
            print('错误! {}  price<=0'.format(price))
            return
        if volume <= 0:
            print('错误! {}  volume<=0'.format(volume))
            return
        # 获取乘数、保证金率、varietyId
        lots,margin_ratio,varietyId = self.get_lots_margin_ratio(symbol_exchange=symbol_exchange)
        amount = round(float(volume*price*lots),4)
        order_percent = round(amount/self.last_equity/(level if level else 5), 4)
        commission = round(float(amount*self.commission_ratio),4)
        margin = round(float(amount*margin_ratio),4)
        exchangeId = self.exchange2id_dict[symbol_exchange.split('.')[1]]

        # 先判断 是否能满足开仓
        need_total_cash = round(margin + commission, 4)
        if self.available_cash >= need_total_cash:
            self.available_cash = round(self.available_cash - need_total_cash, 4)
            self.frozen_cash = round(self.frozen_cash + margin, 4)
        else:
            print('错误! 余额不足,开仓失败.  可用余额：{}  目标金额：{}'.format(self.available_cash, need_total_cash))
            return

        # 有仓位
        position = self.positions.get(symbol_exchange)
        if position:
            position_long = position.get('long')
            if position_long:
                pre_volume = position_long['volume']
                now_volume = pre_volume+volume
                now_amount = position_long['amount']+amount
                now_avg_price = round(float(now_amount/(now_volume*lots)),4)
                now_margin = round(position_long['margin'] + margin, 4)
                self.positions[symbol_exchange]['long']['avg_price'] = now_avg_price

                last_update_price = position_long['last_update_price']
                last_update_avg_price = (last_update_price*pre_volume+volume*price)/now_volume
                self.positions[symbol_exchange]['long']['last_update_price'] = last_update_avg_price

                self.positions[symbol_exchange]['long']['volume'] = now_volume
                self.positions[symbol_exchange]['long']['amount'] = round(float(now_amount),4)
                self.positions[symbol_exchange]['long']['margin'] = now_margin
            else:
                doc = {
                    'symbol_exchange': symbol_exchange,
                    'symbol': symbol_exchange.split('.')[0],
                    'varietyId': varietyId,
                    'exchange': symbol_exchange.split('.')[1],
                    'exchangeId': exchangeId,
                    'side': 'long',
                    'avg_price': price,
                    'volume': volume,
                    'amount': amount,
                    'margin': margin,
                    'margin_ratio': margin_ratio,
                    'lots':lots,
                    'last_update_price': price,
                }
                self.positions[symbol_exchange]['long'] = doc

        # 无仓位，建仓
        else:
            doc = {
                'symbol_exchange': symbol_exchange,
                'symbol': symbol_exchange.split('.')[0],
                'varietyId': varietyId,
                'exchange': symbol_exchange.split('.')[1],
                'exchangeId': exchangeId,
                'side': 'long',
                'avg_price': price,
                'volume': volume,
                'amount': amount,
                'margin': margin,
                'margin_ratio': margin_ratio,
                'lots': lots,
                'last_update_price': price,
            }
            self.positions[symbol_exchange] = {'long':doc}


        order_id = int("".join(random.choice("0123456789") for _ in range(15)))
        if self.is_simulate:
            now_time = str(datetime.datetime.now())[:19]
        else:
            now_time = self.get_datetime()
        order = {
            'create_time':now_time,
            'order_id': order_id,
            'symbol_exchange':symbol_exchange,
            'symbol': symbol_exchange.split('.')[0],
            'varietyId': varietyId,
            'exchange': symbol_exchange.split('.')[1],
            'exchangeId': exchangeId,
            'side':'open_long',
            'sideId':self.side2id_dict['open_long'],
            'avg_price': price,
            'initial_volume': volume,
            'filled_volume': volume,
            'filled_amount': amount,
            'order_percent': order_percent,
            'margin': margin,
            'margin_ratio': margin_ratio,
            'lots': lots,
            'status': 'Filled',
            'commission': commission,
            'other': 0,
            'complete_time': now_time
        }
        # 插入order
        # print('下单', order)
        self.orders[order_id] = order
        self.total_commission = round(self.total_commission + commission, 4)


        # self.total_tradetimes +=1
        # if self.mid_datetime:
        #     if str(self.mid_datetime)[:10] == str(self.now_datetime)[:10]:
        #         self.today_commission = round(self.today_commission + commission, 4)
        #         self.today_tradetimes +=1
        #     else:
        #         self.today_commission = round(commission, 4)
        #         self.today_tradetimes = 1
        #         self.mid_datetime = self.now_datetime
        # else:
        #     self.mid_datetime = self.now_datetime
        #     self.today_commission = round(commission, 4)
        #     self.today_tradetimes = 1

        self.total_tradetimes +=1
        if str(self.now_datetime)[11:19] == '21:00:00':
            self.today_commission = round(commission, 4)
            self.today_tradetimes = 1
        else:
            self.today_commission = round(self.today_commission + commission, 4)
            self.today_tradetimes += 1


        # 入库
        if self.is_simulate:
            info = {
                'strategyBasic_id':self.strategyBasic_id,
                'stgyId': self.stgyId,
                'sort': self.sort,
                'tag': self.tag,
                'margin_ratio': margin_ratio,
                'last_equity':self.last_equity,
                'is_toSQL': self.is_toSQL,
            }
            post_body = {
                'info' : info,
                'order': order,
                'strategy_position': self.positions,
            }
            celery_post(post_body)
            # send_mq.delay(info=info,order_raw=order,strategy_position=self.positions)
        else:
            insert_order(strategyBasic_id=self.strategyBasic_id, sort=self.sort, order=order, is_toSQL=self.is_toSQL)

        # insert_order(strategyBasic_id=self.strategyBasic_id, sort=self.sort, order=order, is_toSQL=self.is_toSQL)

        print(order)
        return order

    def open_short(self, symbol_exchange=None, price=None, volume=None, level=None):
        if price <= 0:
            print('错误! {}  price<=0'.format(price))
            return
        if volume <= 0:
            print('错误! {}  volume<=0'.format(volume))
            return
        # 获取乘数
        # lots = self.universe_lots.get(symbol_exchange)
        # margin_ratio = self.margin_ratios.get(symbol_exchange)
        lots,margin_ratio,varietyId = self.get_lots_margin_ratio(symbol_exchange=symbol_exchange)
        amount = round(float(volume*price*lots),4)
        order_percent = round(amount/self.last_equity/(level if level else 5), 4)
        commission = round(float(amount*self.commission_ratio),4)
        margin = round(float(amount*margin_ratio),4)
        exchangeId = self.exchange2id_dict[symbol_exchange.split('.')[1]]

        # 先判断 是否能满足开仓
        need_total_cash = round(margin + commission, 4)
        if self.available_cash >= need_total_cash:
            self.available_cash = round(self.available_cash - need_total_cash, 4)
            self.frozen_cash = round(self.frozen_cash + margin, 4)
        else:
            print('错误! 余额不足,开仓失败.  {}  {}'.format(self.available_cash, need_total_cash))
            return

        # 有仓位
        position = self.positions.get(symbol_exchange)
        if position:
            position_long = position.get('short')
            if position_long:
                pre_volume = position_long['volume']
                now_volume = pre_volume+volume
                now_amount = position_long['amount']+amount
                now_avg_price = round(float(now_amount/(now_volume*lots)),4)
                now_margin = round(position_long['margin'] + margin, 4)
                self.positions[symbol_exchange]['short']['avg_price'] = now_avg_price

                last_update_price = position_long['last_update_price']
                last_update_avg_price = (last_update_price*pre_volume+volume*price)/now_volume
                self.positions[symbol_exchange]['short']['last_update_price'] = last_update_avg_price

                self.positions[symbol_exchange]['short']['volume'] = now_volume
                self.positions[symbol_exchange]['short']['amount'] = round(float(now_amount),4)
                self.positions[symbol_exchange]['short']['margin'] = now_margin
            else:
                doc = {
                    'symbol_exchange': symbol_exchange,
                    'symbol': symbol_exchange.split('.')[0],
                    'varietyId': varietyId,
                    'exchange': symbol_exchange.split('.')[1],
                    'exchangeId': exchangeId,
                    'side': 'short',
                    'avg_price': price,
                    'volume': volume,
                    'amount': amount,
                    'margin': margin,
                    'margin_ratio': margin_ratio,
                    'lots': lots,
                    'last_update_price':price,
                }
                self.positions[symbol_exchange]['short'] = doc

        # 无仓位，建仓
        else:
            doc = {
                'symbol_exchange': symbol_exchange,
                'symbol': symbol_exchange.split('.')[0],
                'varietyId': varietyId,
                'exchange': symbol_exchange.split('.')[1],
                'exchangeId': exchangeId,
                'side': 'short',
                'avg_price': price,
                'volume': volume,
                'amount': amount,
                'margin': margin,
                'margin_ratio': margin_ratio,
                'lots': lots,
                'last_update_price': price,
            }
            self.positions[symbol_exchange] = {'short':doc}


        order_id = int("".join(random.choice("0123456789") for _ in range(15)))
        if self.is_simulate:
            now_time = str(datetime.datetime.now())[:19]
        else:
            now_time = self.get_datetime()
        order = {
            'create_time': now_time,
            'order_id': order_id,
            'symbol_exchange':symbol_exchange,
            'symbol': symbol_exchange.split('.')[0],
            'varietyId': varietyId,
            'exchange': symbol_exchange.split('.')[1],
            'exchangeId': exchangeId,
            'side':'open_short',
            'sideId': self.side2id_dict['open_short'],
            'avg_price': price,
            'initial_volume': volume,
            'filled_volume': volume,
            'filled_amount': amount,
            'order_percent': order_percent,
            'margin': margin,
            'margin_ratio': margin_ratio,
            'lots': lots,
            'status': 'Filled',
            'commission': commission,
            'other': 0,
            'complete_time': now_time
        }
        # 插入order
        # print('下单', order)
        self.orders[order_id] = order
        self.total_commission = round(self.total_commission + commission, 4)


        self.total_tradetimes +=1
        if str(self.now_datetime)[11:19] == '21:00:00':
            self.today_commission = round(commission, 4)
            self.today_tradetimes = 1
        else:
            self.today_commission = round(self.today_commission + commission, 4)
            self.today_tradetimes += 1


        # 入库
        if self.is_simulate:
            info = {
                'strategyBasic_id':self.strategyBasic_id,
                'stgyId': self.stgyId,
                'sort': self.sort,
                'tag': self.tag,
                'margin_ratio': margin_ratio,
                'last_equity': self.last_equity,
                'is_toSQL': self.is_toSQL,
            }
            post_body = {
                'info' : info,
                'order': order,
                'strategy_position': self.positions,
            }
            celery_post(post_body)
            # send_mq.delay(info=info,order_raw=order,strategy_position=self.positions)
        else:
            insert_order(strategyBasic_id=self.strategyBasic_id, sort=self.sort, order=order, is_toSQL=self.is_toSQL)

        # insert_order(strategyBasic_id=self.strategyBasic_id, sort=self.sort, order=order, is_toSQL=self.is_toSQL)

        print(order)
        return order

    def close_long(self, symbol_exchange=None, price=None, volume=None, is_force=None, level=None):
        if price <= 0:
            print('错误! {}  price<=0'.format(price))
            return
        if volume <= 0:
            print('错误! {}  volume<=0'.format(volume))
            return
        # 获取乘数
        lots,margin_ratio,varietyId = self.get_lots_margin_ratio(symbol_exchange=symbol_exchange)

        amount = round(float(volume*price*lots),4)
        order_percent = round(amount/self.last_equity/(level if level else 5), 4)
        commission = round(float(amount*self.commission_ratio),4)

        # 一定是有仓位，才平仓
        margin = 0
        real_pnl = 0
        real_pnl_ratio = 0
        pnl = 0
        pnl_ratio = 0
        position = self.positions.get(symbol_exchange)
        if position:
            position_long = position.get('long')
            if position_long:
                # 错误
                if volume > position_long['volume']:
                    print('错误! 持仓量 < 平仓量.  {}  {}'.format(position_long['volume'], volume))
                    return
                # 平仓完
                if volume == position_long['volume']:
                    # 盈亏
                    pre_volume = position_long['volume']

                    pre_avg_price = position_long['avg_price']
                    real_pnl = round((price - pre_avg_price) * pre_volume * lots,4)
                    real_pnl_ratio = round((price - pre_avg_price)/pre_avg_price, 4)

                    last_update_price = position_long['last_update_price']
                    pnl = (price - last_update_price) * pre_volume * lots
                    pnl_ratio = round((price - last_update_price)/last_update_price, 4)

                    margin = round(self.positions[symbol_exchange]['long']['margin'],4)
                    self.positions[symbol_exchange]['long'] = {}
                    # 清除字典里的key
                    self.positions[symbol_exchange].pop('long')
                    if not self.positions[symbol_exchange].get('short'):
                        self.positions.pop(symbol_exchange)
                # 平仓一部分
                if volume < position_long['volume']:
                    pre_volume = position_long['volume']

                    pre_avg_price = position_long['avg_price']
                    real_pnl = round((price - pre_avg_price) * volume * lots, 4)
                    real_pnl_ratio = round((price - pre_avg_price)/pre_avg_price, 4)

                    last_update_price = position_long['last_update_price']
                    pnl = (price - last_update_price) * volume * lots
                    pnl_ratio = round((price - last_update_price)/last_update_price, 4)

                    now_volume = pre_volume - volume
                    # now_amount = position_long['amount'] - amount
                    now_amount = position_long['amount'] - volume * pre_avg_price * lots

                    # 计算返还保证金
                    pre_margin = position_long['margin']
                    avg_margin = pre_margin/pre_volume
                    margin = round(avg_margin*volume ,4)
                    now_margin = round(pre_margin - margin, 4)
                    # self.positions[symbol_exchange]['long']['last_update_price'] = now_avg_price
                    self.positions[symbol_exchange]['long']['volume'] = now_volume
                    self.positions[symbol_exchange]['long']['amount'] = round(float(now_amount),4)
                    self.positions[symbol_exchange]['long']['margin'] = now_margin
            else:
                print('错误! 无持仓,无法平仓.')
                return
        else:
            print('错误! 无持仓,无法平仓.')
            return

        # pnl_ = round(pnl, 4)
        self.available_cash = round(self.available_cash + pnl + margin - commission,4)
        self.frozen_cash = round(self.frozen_cash - margin,4)

        order_id = int("".join(random.choice("0123456789") for _ in range(15)))
        if self.is_simulate:
            now_time = str(datetime.datetime.now())[:19]
        else:
            now_time = self.get_datetime()
        order = {
            'create_time': now_time,
            'order_id': order_id,
            'symbol_exchange':symbol_exchange,
            'symbol': symbol_exchange.split('.')[0],
            'varietyId': varietyId,
            'exchange': symbol_exchange.split('.')[1],
            'exchangeId': self.exchange2id_dict[symbol_exchange.split('.')[1]],
            'side': 'close_long',
            'sideId': self.side2id_dict['close_long'],
            'avg_price': price,
            'initial_volume': volume,
            'filled_volume': volume,
            'filled_amount': amount,
            'order_percent': order_percent,
            'return_margin': margin,
            'pnl': real_pnl,
            'pnl_ratio':real_pnl_ratio,
            'lots': lots,
            'status': 'Filled',
            'commission': commission,
            'is_force':is_force,
            'other': 0,
            'complete_time': now_time
        }
        # 插入order
        # print('下单', order)
        self.orders[order_id] = order
        self.total_commission = round(self.total_commission + commission, 4)


        self.total_tradetimes +=1
        if str(self.now_datetime)[11:19] == '21:00:00':
            self.today_commission = round(commission, 4)
            self.today_tradetimes = 1
        else:
            self.today_commission = round(self.today_commission + commission, 4)
            self.today_tradetimes += 1


        # 入库
        if self.is_simulate:
            info = {
                'strategyBasic_id':self.strategyBasic_id,
                'stgyId': self.stgyId,
                'sort': self.sort,
                'tag': self.tag,
                'margin_ratio': margin_ratio,
                'last_equity': self.last_equity,
                'is_toSQL': self.is_toSQL,
            }
            post_body = {
                'info': info,
                'order': order,
                'strategy_position': self.positions,
            }
            celery_post(post_body)
            # send_mq.delay(info=info,order_raw=order,strategy_position=self.positions)
        else:
            insert_order(strategyBasic_id=self.strategyBasic_id, sort=self.sort, order=order, is_toSQL=self.is_toSQL)

        # insert_order(strategyBasic_id=self.strategyBasic_id, sort=self.sort, order=order, is_toSQL=self.is_toSQL)

        print(order)
        return order

    def close_short(self, symbol_exchange=None, price=None, volume=None, is_force=None, level=None):
        if price <= 0:
            print('错误! {}  price<=0'.format(price))
            return
        if volume <= 0:
            print('错误! {}  volume<=0'.format(volume))
            return
        # 获取乘数
        # lots = self.universe_lots.get(symbol_exchange)
        lots,margin_ratio,varietyId = self.get_lots_margin_ratio(symbol_exchange=symbol_exchange)

        amount = round(float(volume * price * lots), 4)
        order_percent = round(amount/self.last_equity/(level if level else 5), 4)
        commission = round(float(amount * self.commission_ratio), 4)

        # 一定是有仓位，才平仓
        margin = 0
        pnl = 0
        pnl_ratio = 0
        real_pnl = 0
        real_pnl_ratio = 0
        position = self.positions.get(symbol_exchange)
        if position:
            position_long = position.get('short')
            if position_long:
                # 错误
                if volume > position_long['volume']:
                    print('错误! 持仓量 < 平仓量.  {}  {}'.format(position_long['volume'], volume))
                    return
                # 平仓完
                if volume == position_long['volume']:
                    # 盈亏
                    pre_volume = position_long['volume']
                    pre_avg_price = position_long['avg_price']
                    real_pnl = round(-(price - pre_avg_price) * pre_volume * lots, 4)
                    real_pnl_ratio = -round((price - pre_avg_price)/pre_avg_price, 4)

                    last_update_price = position_long['last_update_price']
                    pnl = -(price - last_update_price) * pre_volume * lots
                    pnl_ratio = -round((price - last_update_price)/last_update_price, 4)
                    # 退换保证金
                    margin = round(self.positions[symbol_exchange]['short']['margin'],4)
                    self.positions[symbol_exchange]['short'] = {}
                    # 清除字典里的key
                    self.positions[symbol_exchange].pop('short')
                    if not self.positions[symbol_exchange].get('long'):
                        self.positions.pop(symbol_exchange)
                # 平仓一部分
                if volume < position_long['volume']:
                    pre_volume = position_long['volume']

                    pre_avg_price = position_long['avg_price']
                    real_pnl = round(-(price - pre_avg_price) * volume * lots, 4)
                    real_pnl_ratio = -round((price - pre_avg_price)/pre_avg_price, 4)

                    last_update_price = position_long['last_update_price']
                    pnl = -(price - last_update_price) * volume * lots
                    pnl_ratio = -round((price - last_update_price)/last_update_price, 4)

                    now_volume = pre_volume - volume
                    # now_amount = position_long['amount'] - amount
                    now_amount = position_long['amount'] - volume * pre_avg_price * lots

                    pre_margin = position_long['margin']
                    avg_margin = pre_margin/pre_volume
                    margin = round(avg_margin*volume ,4)
                    now_margin = round(pre_margin - margin, 4)
                    self.positions[symbol_exchange]['short']['volume'] = now_volume
                    self.positions[symbol_exchange]['short']['amount'] = round(float(now_amount),4)
                    self.positions[symbol_exchange]['short']['margin'] = now_margin
            else:
                print('错误! 无持仓,无法平仓.')
                return
        else:
            print('错误! 无持仓,无法平仓.')
            return

        # pnl_ = round(pnl, 4)
        self.available_cash = round(self.available_cash + pnl + margin - commission, 4)
        self.frozen_cash = round(self.frozen_cash - margin,4)

        order_id = int("".join(random.choice("0123456789") for _ in range(15)))
        if self.is_simulate:
            now_time = str(datetime.datetime.now())[:19]
        else:
            now_time = self.get_datetime()
        order = {
            'create_time': now_time,
            'order_id': order_id,
            'symbol_exchange': symbol_exchange,
            'symbol': symbol_exchange.split('.')[0],
            'varietyId':varietyId,
            'exchange': symbol_exchange.split('.')[1],
            'exchangeId': self.exchange2id_dict[symbol_exchange.split('.')[1]],
            'side': 'close_short',
            'sideId': self.side2id_dict['close_short'],
            'avg_price': price,
            'initial_volume': volume,
            'filled_volume': volume,
            'filled_amount': amount,
            'order_percent':order_percent,
            'return_margin': margin,
            'pnl': real_pnl,
            'pnl_ratio':real_pnl_ratio,
            'lots': lots,
            'status': 'Filled',
            'commission': commission,
            'is_force': is_force,
            'other':0,
            'complete_time': now_time
        }
        # 插入order
        # print('下单', order)
        self.orders[order_id] = order
        self.total_commission = round(self.total_commission + commission, 4)


        self.total_tradetimes +=1
        if str(self.now_datetime)[11:19] == '21:00:00':
            self.today_commission = round(commission, 4)
            self.today_tradetimes = 1
        else:
            self.today_commission = round(self.today_commission + commission, 4)
            self.today_tradetimes += 1


        # 入库
        if self.is_simulate:
            info = {
                'strategyBasic_id':self.strategyBasic_id,
                'stgyId': self.stgyId,
                'sort': self.sort,
                'tag': self.tag,
                'margin_ratio':margin_ratio,
                'last_equity': self.last_equity,
                'is_toSQL': self.is_toSQL,
            }
            post_body = {
                'info' : info,
                'order': order,
                'strategy_position': self.positions,
            }
            celery_post(post_body)
            # send_mq.delay(info=info,order_raw=order,strategy_position=self.positions)
        else:
            insert_order(strategyBasic_id=self.strategyBasic_id, sort=self.sort, order=order, is_toSQL=self.is_toSQL)

        # insert_order(strategyBasic_id=self.strategyBasic_id, sort=self.sort, order=order, is_toSQL=self.is_toSQL)

        print(order)
        return order

    def get_datetime(self):
        return self.now_datetime


    def get_positions(self):
        return self.positions


    def get_cash(self):
        total_cash = round(self.available_cash + self.frozen_cash, 4)
        cash = {'available_cash':self.available_cash,'frozen_cash':self.frozen_cash,'total_cash':total_cash}
        return cash


    def get_pnl(self):
        total_pnl = 0
        if self.is_simulate:
            now_time = str(datetime.datetime.now())[:19]
        else:
            now_time = self.get_datetime()
        positions = self.get_positions()
        for pos, pos_ins in positions.items():
            if self.is_simulate:
                symbol = pos.split('.')[0]
                exchange = pos.split('.')[1]
                # price = get_price(symbol=symbol, exchange=exchange, end=now_time)
                price = get_price(symbol=symbol, exchange=exchange)
            else:
                price = self.get_close_price(symbol_exchange=pos, now_time=now_time)
            long_pnl = 0
            short_pnl = 0
            # lots = self.universe_lots.get(pos)
            lots, margin_ratio,varietyId= self.get_lots_margin_ratio(symbol_exchange=pos)
            if pos_ins.get('long'):
                avg_price = pos_ins.get('long')['last_update_price']
                volume = pos_ins.get('long')['volume']
                long_pnl = (price - avg_price) * volume * lots
            if pos_ins.get('short'):
                avg_price = pos_ins.get('short')['last_update_price']
                volume = pos_ins.get('short')['volume']
                short_pnl = (avg_price - price) * volume * lots
            pnl = long_pnl + short_pnl
            total_pnl += pnl
        return round(total_pnl,4)


    def update_available_cash(self):
        total_pnl = 0
        total_margin = 0
        if self.is_simulate:
            now_time = str(datetime.datetime.now())[:19]
        else:
            now_time = self.get_datetime()
        positions = self.get_positions()
        for pos, pos_ins in positions.items():
            if self.is_simulate:
                symbol = pos.split('.')[0]
                exchange = pos.split('.')[1]
                # price = get_price(symbol=symbol, exchange=exchange, end=now_time)
                price = get_price(symbol=symbol, exchange=exchange)
            else:
                price = self.get_open_price(symbol_exchange=pos, now_time=now_time)
            long_pnl = 0
            short_pnl = 0
            long_margin = 0
            short_margin = 0
            # lots = self.universe_lots.get(pos)
            # margin_ratio = self.margin_ratios.get(pos)
            lots, margin_ratio,varietyId = self.get_lots_margin_ratio(symbol_exchange=pos)
            if pos_ins.get('long'):
                avg_price = pos_ins.get('long')['avg_price']

                last_update_price = pos_ins.get('long')['last_update_price']
                volume = pos_ins.get('long')['volume']
                long_pnl = (price - last_update_price) * volume * lots
                # 更新保证金
                amount = round(float(volume * price * lots), 4)
                long_margin = round(float(amount * margin_ratio), 4)
                self.get_positions()[pos]['long']['margin'] = long_margin

                # print('long {} 持仓均价：{}  上次价格：{}  现价：{}'.format(pos, avg_price, last_update_price, price))
                self.get_positions()[pos]['long']['last_update_price'] = price
            if pos_ins.get('short'):
                avg_price = pos_ins.get('short')['avg_price']

                last_update_price = pos_ins.get('short')['last_update_price']
                volume = pos_ins.get('short')['volume']
                short_pnl = (last_update_price - price) * volume * lots
                # 更新保证金
                amount = round(float(volume * price * lots), 4)
                short_margin = round(float(amount * margin_ratio), 4)
                self.get_positions()[pos]['short']['margin'] = short_margin

                # print('short {} 持仓均价：{}  上次价格：{}  现价：{}'.format(pos, avg_price, last_update_price, price))
                self.get_positions()[pos]['short']['last_update_price'] = price

            pnl = long_pnl + short_pnl
            margin = long_margin + short_margin
            total_pnl += pnl
            total_margin += margin

        pre_frozen_cash = round(self.frozen_cash, 4)
        now_frozen_cash = total_margin
        diff_frozen_cash = pre_frozen_cash - now_frozen_cash

        pre_available_cash = round(self.available_cash, 4)
        total_pnl = round(total_pnl, 4)
        now_available_cash = round(self.available_cash + total_pnl + diff_frozen_cash, 4)

        self.frozen_cash = now_frozen_cash
        self.available_cash = now_available_cash
        # print('原cash : {}   盈亏 : {}  保证金变化: {}  现cash: {}'.format(
        #     pre_available_cash, total_pnl, diff_frozen_cash, now_available_cash))


    def get_equity(self):
        cash_ins = self.get_cash()
        total_cash = cash_ins['available_cash'] + cash_ins['frozen_cash']
        total_pnl = self.get_pnl()
        total_equity = round(total_pnl + total_cash, 4)

        # # 强平操作(前提有仓位)
        # if total_equity <= 0:
        #     total_equity = self.force_position(total_equity)
        return total_equity


    def check_is_force_position(self):
        # cash < 0

        available_cash = self.get_cash()['available_cash']
        if available_cash < 0:
            # print('强平操作。。。')
            while True:
                if available_cash >= 0:
                    self.available_cash = round(available_cash, 4)
                    break
                # 随机平仓位
                positions = self.get_positions()
                pos_1 = list(positions.keys())[0]  # 'ag2101.SHFE'
                positipos_ins_1 = list(positions.values())[0]

                if self.is_simulate:
                    price = self.get_price(symbol_exchange=pos_1)
                else:
                    price = self.get_open_price(symbol_exchange=pos_1)

                if positipos_ins_1.get('long'):
                    order = self.close_long(symbol_exchange=pos_1, price=price, volume=1, is_force=1)
                    pnl = order['pnl']
                    commission = order['commission']
                    return_margin = order['return_margin']
                else:
                    order = self.close_short(symbol_exchange=pos_1, price=price, volume=1, is_force=1)
                    pnl = order['pnl']
                    commission = order['commission']
                    return_margin = order['return_margin']
                force_money = pnl + return_margin - commission
                # print('强平单  ',order)
                # print('盈亏 {}  返还保证金 {}  手续费 {}   合计：{}'.format(pnl,return_margin,commission,force_money))
                available_cash += force_money
        else:
            return


    def get_history(self,symbol_exchange=None,freq=None,end=None,count=None):
        if self.is_simulate:
            if not end:
                # end = str(datetime.datetime.now())[:19]
                end = str(self.get_datetime())[:19]
            symbol = symbol_exchange.split('.')[0]
            exchange = symbol_exchange.split('.')[1]
            freq_ = freq if freq else self.freq
            data = get_hisBar(symbol=symbol, exchange=exchange, freq=freq_, end=end, count=count)
            return data
        else:
            if not end:
                end = str(self.get_datetime())[:19]
            end_ = int(end.replace('-', '').replace(' ', '').replace(':', ''))
            df_data = self.cache.get(symbol_exchange)
            if df_data is None:
                t11 = time.time()
                symbol = symbol_exchange.split('.')[0]
                exchange = symbol_exchange.split('.')[1]
                freq_ = freq if freq else self.freq
                df_data = get_all_hisBar(symbol=symbol, exchange=exchange, freq=freq_, start=self.start_, end=self.end_)
                self.cache[symbol_exchange] = df_data
                print('{}  加载数据成功!  {} s'.format(symbol_exchange, str(time.time() - t11)[:4]))
            r_data = df_data.loc[df_data["time"] < end_][-count:]
            return r_data.sort_values(by='time').reset_index(drop=True)


    def get_price(self,symbol_exchange=None,now_time=None):
        if self.is_simulate:
            if not now_time:
                now_time = str(datetime.datetime.now())[:19]
            symbol = symbol_exchange.split('.')[0]
            exchange = symbol_exchange.split('.')[1]
            # price = get_price(symbol=symbol, exchange=exchange, end=now_time)
            price = get_price(symbol=symbol, exchange=exchange)
            return price
        else:
            if not now_time:
                now_time = str(self.get_datetime())[:19]
            now_time_ = int(now_time.replace('-', '').replace(' ', '').replace(':', ''))
            df_data = self.cache.get(symbol_exchange)
            if df_data is None:
                t11 = time.time()
                symbol = symbol_exchange.split('.')[0]
                exchange = symbol_exchange.split('.')[1]
                df_data = get_all_hisBar(symbol=symbol, exchange=exchange, freq=self.freq, start=self.start_, end=self.end_)
                self.cache[symbol_exchange] = df_data
                print('{}  加载数据成功!  {} s'.format(symbol_exchange, str(time.time() - t11)[:4]))
            open_price = float(df_data.loc[(df_data['time'] >= now_time_)].iloc[0]['open'])
            return open_price
            # try:
            #     close_price = df_data.loc[(df_data['time'] >= now_time_)]['close'].tolist()[0]
            #     # open_close = float(df_data.loc[(df_data['time'] > now_time_)].iloc[0]['open'])
            # except:
            #     close_price = df_data.loc[df_data["time"] <= now_time_][-1:]['close'].tolist()[0]
            # return close_price

    def get_depth(self,symbol_exchange=None,now_time=None):
        if self.is_simulate:
            if not now_time:
                now_time = str(datetime.datetime.now())[:19]
            symbol = symbol_exchange.split('.')[0]
            exchange = symbol_exchange.split('.')[1]
            data = contract_depth(symbol=symbol, exchange=exchange, end=now_time)
            return data


    def get_close_price(self,symbol_exchange=None,now_time=None):
        if not now_time:
            now_time = str(self.get_datetime())[:19]
        df_data = self.cache.get(symbol_exchange)
        if df_data is None:
            t11 = time.time()
            symbol = symbol_exchange.split('.')[0]
            exchange = symbol_exchange.split('.')[1]
            df_data = get_all_hisBar(symbol=symbol, exchange=exchange, freq=self.freq, start=self.start_, end=self.end_)
            self.cache[symbol_exchange] = df_data
            print('{}  加载数据成功!  {} s'.format(symbol_exchange, str(time.time() - t11)[:4]))
        now_time_ = int(now_time.replace('-', '').replace(' ', '').replace(':', ''))
        # try:
        #     close_price = df_data.loc[(df_data['time'] == now_time_)]['close'].tolist()[0]
        # except:
        #     close_price = df_data.loc[df_data["time"] <= now_time_][-1:]['close'].tolist()[0]
        close_price = df_data.loc[df_data["time"] < now_time_][-1:]['close'].tolist()[0]
        return close_price

    def get_open_price(self,symbol_exchange=None,now_time=None):
        if not now_time:
            now_time = str(self.get_datetime())[:19]
        df_data = self.cache.get(symbol_exchange)
        if df_data is None:
            t11 = time.time()
            symbol = symbol_exchange.split('.')[0]
            exchange = symbol_exchange.split('.')[1]
            df_data = get_all_hisBar(symbol=symbol, exchange=exchange, freq=self.freq, start=self.start_, end=self.end_)
            self.cache[symbol_exchange] = df_data
            print('{}  加载数据成功!  {} s'.format(symbol_exchange, str(time.time() - t11)[:4]))
        now_time_ = int(now_time.replace('-', '').replace(' ', '').replace(':', ''))
        # try:
        #     open_price = df_data.loc[(df_data['time'] == now_time_)]['open'].tolist()[0]
        # except:
        #     open_price = df_data.loc[df_data["time"] <= now_time_][-1:]['open'].tolist()[0]
        open_price = df_data.loc[df_data["time"] < now_time_][-1:]['open'].tolist()[0]
        return open_price



if __name__ == '__main__':
    pass
