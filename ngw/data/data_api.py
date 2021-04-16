import json
import traceback

import math
import requests
import time
import pandas as pd
import datetime
import numpy as np
from ngwcontractbacktest.ngw.constants import host
from ngwcontractbacktest.ngw.utils.date_util import str2datetime

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


requests.DEFAULT_RETRIES = 50
def freq2dataType(freq=None):
    # print(freq)
    if freq is None:
        return 60
    elif freq == '1m':
        return 60
    elif freq == '5m':
        return 5 * 60
    elif freq == '15m':
        return 15 * 60
    elif freq == '30m':
        return 30 * 60
    elif freq == '60m':
        return 60 * 60
    elif freq == '1d':
        return 60 * 60 * 24
    elif freq == '1w':
        return 60 * 60 * 24 * 7
    else:
        return 60 * 60 * 24


def exchange2num(exchange):
    if exchange is None:
        return 4
    # 中金所
    elif exchange == 'CFFEX':
        return 3
    # 上期所
    elif exchange == 'SHFE':
        return 4
    # 大商所
    elif exchange == 'DCE':
        return 5
    # 郑商所
    elif exchange == 'CZCE':
        return 6
    # 上海国际能源交易中心
    elif exchange == 'INE':
        return 15


def get_hisBar_raw(symbol=None, exchange=None, freq=None, start=None, end=None, count=None):
    # print(symbol, exchange, freq, start, end)
    # print(start,type(start))
    # print(end, type(end))
    # body = {"symbol": "rb2010", "exchange": 4, "dataType": 60, "begin": "20201009", "end": "20201020"}
    exchange_ = exchange2num(exchange)
    dataType = freq2dataType(freq=freq)

    url = ''
    body = {"symbol": symbol, "exchange": exchange_, "dataType": dataType, "dataSource":1 }
    if start and end and not count:
        begin = start.replace('-', '').replace(' ', '').replace(':', '')
        end = end.replace('-', '').replace(' ', '').replace(':', '')
        body['begin'] = begin
        body['end'] = end
        url = "https://apigateway.inquantstudio.com/api/MarketData/GetHisBar"
    if not start and not end and count:
        body['count'] = count
        url = "https://apigateway.inquantstudio.com/api/MarketData/GetLastBar"
    if not start and end and count:
        end = end.replace('-', '').replace(' ', '').replace(':', '')
        body['end'] = end
        body['count'] = count
        url = "https://apigateway.inquantstudio.com/api/MarketData/GetPreviousBar"
    # print(body)
    # print(url)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6",
            "Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(body), headers=headers)
        response.close()
    except Exception:
        print(traceback.format_exc())
        return None
    else:
        response = response.content.decode()
        response_json = json.loads(response)
        data = response_json.get('data')
        try:
            df_data = pd.DataFrame(data)
            df_data.columns = ['symbol', 'exchange', 'bar_type', 'time', 'pre_close', 'open', 'high', 'low', 'close',
                               'volume',
                               'turnover', 'open_interest', 'settlement']

            df_data_ = df_data.sort_values(by='time').reset_index(drop=True)
        except:
            df_data_ = pd.DataFrame()
        return df_data_


def get_hisBar(symbol=None, exchange=None, freq=None, start=None, end=None, count=None):
    delay_times = 5
    i = 0
    while i < delay_times:
        data = get_hisBar_raw(symbol=symbol, exchange=exchange, freq=freq, start=start, end=end, count=count)
        if isinstance(data, pd.DataFrame):
            if not data.empty:
                return data
        i += 1
        time.sleep(0.01)
        continue

def get_all_hisBar(symbol=None, exchange=None, freq=None, start=None, end=None, count=None):
    # print(symbol, exchange, freq, start, end)
    if start and end and not count:
        start_ = str2datetime(start)
        end = str2datetime(end)
        diff = end - start_
        diff_days = diff.days

        all_pd_data = pd.DataFrame()
        if diff_days >= 150:
            run_times = math.ceil(diff_days / 150)
            for i in range(run_times):
                end_temp = start_ + datetime.timedelta(days=150)
                if end_temp >= end:
                    data = get_hisBar(symbol=symbol, exchange=exchange, freq=freq, start=str(start_)[:19],end=str(end)[:19])
                    all_pd_data = all_pd_data.append(data)
                    break
                data = get_hisBar(symbol=symbol, exchange=exchange, freq=freq, start=str(start_)[:19],end=str(end_temp)[:19])
                all_pd_data = all_pd_data.append(data)
                start_ = end_temp
        else:
            return get_hisBar(symbol=symbol, exchange=exchange, freq=freq, start=str(start)[:19], end=str(end)[:19])
        return all_pd_data.reset_index(drop=True)
    else:
        return get_hisBar(symbol=symbol, exchange=exchange, freq=freq, start=start, end=end, count=count)






def get_hisTick_raw(symbol=None, exchange=None, start=None, end=None, count=None):
    exchange_ = exchange2num(exchange)

    url = ''
    body = {"symbol": symbol, "exchange": exchange_, "dataSource":1}
    if start and end and not count:
        begin = start.replace('-', '').replace(' ', '').replace(':', '')
        end = end.replace('-', '').replace(' ', '').replace(':', '')
        body['begin'] = begin
        body['end'] = end
        url = "https://apigateway.inquantstudio.com/api/MarketData/GetHisTick"
    if not start and not end and count:
        body['count'] = count
        url = "https://apigateway.inquantstudio.com/api/MarketData/GetLastTick"
    if not start and end and count:
        end = end.replace('-', '').replace(' ', '').replace(':', '')
        body['end'] = end
        body['count'] = count
        url = "https://apigateway.inquantstudio.com/api/MarketData/GetPreviousTick"

    # print(body)
    # print(url)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6",
            "Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(body), headers=headers)
        response.close()
    except Exception:
        print(traceback.format_exc())
        return None
    else:
        response = response.content.decode()
        response_json = json.loads(response)
        data = response_json.get('data')
        try:
            df_data = pd.DataFrame(data)
            df_data.columns = ['symbol', 'exchange', 'time',
                               'last', 'open', 'high', 'low', 'pre_close',
                               'volume','turnover',
                               'bid','ask','upper_limit','lower_limit',
                               'open_interest', 'settlement']
        except:
            df_data = pd.DataFrame()
        return df_data


def get_hisTick(symbol=None, exchange=None, start=None, end=None, count=None):
    delay_times = 5
    i = 0
    while i < delay_times:
        data = get_hisTick_raw(symbol=symbol, exchange=exchange, start=start, end=end, count=count)
        if isinstance(data, pd.DataFrame):
            if not data.empty:
                return data
        i += 1
        time.sleep(0.01)
        continue



def contract_depth_raw(symbol=None, exchange=None, end=None):
    exchange_ = exchange2num(exchange)
    url = ''
    body = {"symbol": symbol, "exchange": exchange_, "count":1, "dataSource":1}
    if not end:
        url = "https://apigateway.inquantstudio.com/api/MarketData/GetLastTick"
    if end:
        end = end.replace('-', '').replace(' ', '').replace(':', '')
        body['end'] = end
        url = "https://apigateway.inquantstudio.com/api/MarketData/GetPreviousTick"
    # print(body)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6",
            "Content-Type": "application/json"}
        # print(url)
        response = requests.post(url, data=json.dumps(body), headers=headers)
        response.close()
    except Exception:
        print(traceback.format_exc())
        return None
    else:
        response = response.content.decode()
        response_json = json.loads(response)
        print(response_json)
        data = response_json.get('data')[0]
        # return data
        bid = [[i['p'],i['v']] for i in data['bid']]
        ask = [[i['p'],i['v']] for i in data['ask']]
        c_depth = {'bid':bid,'ask':ask,'time':str(datetime.datetime.strptime(str(data['t']),'%Y%m%d%H%M%S'))}
        return c_depth


def contract_depth(symbol=None, exchange=None, end=None):
    delay_times = 5
    i = 0
    while i < delay_times:
        data = contract_depth_raw(symbol=symbol, exchange=exchange, end=end)
        if data:
            return data
        i += 1
        time.sleep(0.05)
        continue






def get_price_raw(symbol=None, exchange=None, end=None):
    exchange_ = exchange2num(exchange)
    url = ''
    body = {"symbol": symbol, "exchange": exchange_, "count":1, "dataSource":1}
    if not end:
        url = "https://apigateway.inquantstudio.com/api/MarketData/GetLastTick"
    if end:
        end = end.replace('-', '').replace(' ', '').replace(':', '')
        body['end'] = end
        url = "https://apigateway.inquantstudio.com/api/MarketData/GetPreviousTick"
    # print(body)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6",
            "Content-Type": "application/json"}
        # print(url)
        response = requests.post(url, data=json.dumps(body), headers=headers)
        response.close()
    except Exception:
        print(traceback.format_exc())
        return None
    else:
        response = response.content.decode()
        response_json = json.loads(response)
        data = response_json.get('data')[0]
        price = round(float(data['px']), 4)
        return price


def get_price(symbol=None, exchange=None, end=None):
    delay_times = 5
    i = 0
    while i < delay_times:
        data = get_price_raw(symbol=symbol, exchange=exchange, end=end)
        if data:
            return data
        i += 1
        time.sleep(0.05)
        continue





def celery_post(body):
    url = "http://{}/contract/celery_task".format(host)
    # print(body)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6",
            "Content-Type": "application/json"}
        # print(url)
        response = requests.post(url, data=json.dumps(body), headers=headers)
        response.close()
    except Exception:
        print(traceback.format_exc())
        return None
    else:
        response = response.content.decode()
        response_json = json.loads(response)
        data = response_json.get('data')
        return data




if __name__ == '__main__':
    # start = str2datetime('2019-01-01')
    # end = str2datetime('2020-11-01')
    # print(start)
    # print(end)
    # diff = end-start
    #
    # all_pd_data = pd.DataFrame()
    # diff_days = diff.days
    # if diff_days>=150:
    #     run_times = math.ceil(diff_days/150)
    #     for i in range(run_times):
    #         # print(i)
    #         end_temp = start + datetime.timedelta(days=150)
    #         if end_temp >= end:
    #             # print(start,end)
    #             data = get_hisBar(symbol='rb2101', exchange='SHFE', freq='1m', start=str(start)[:19], end=str(end)[:19])
    #             # print(data)
    #             all_pd_data = all_pd_data.append(data)
    #             break
    #         # print(start, end_temp)
    #         data = get_hisBar(symbol='rb2101', exchange='SHFE', freq='1m', start=str(start)[:19], end=str(end_temp)[:19])
    #         # print(data)
    #         all_pd_data = all_pd_data.append(data)
    #         start = end_temp
    # else:
    #     pass
    # print(all_pd_data.reset_index(drop=True))
    #
    # # data = get_hisBar(symbol='rb2101', exchange='SHFE', freq='1m', start=start, end=end)
    # # print(data)
    #
    #
    # data = get_all_hisBar(symbol='rb2101', exchange='SHFE', freq='1m', start='2019-01-01', end='2020-11-01')
    # print(data)


    # data = get_hisBar(symbol='rb2101', exchange='SHFE', freq='1m', start='2020-10-20 09:50:00', end='2020-10-21 14:25:00')
    # print(data)
    # data = get_hisBar(symbol='rb2101', exchange='SHFE', freq='1m', end=str(datetime.datetime.now())[:19],count=200)
    # print(data)
    # data = get_hisBar(symbol='rb2101', exchange='SHFE', freq='1m', count=200)
    # print(data)


    # data = get_hisTick(symbol='rb2101', exchange='SHFE', start='2020-11-19 09:50:00', end='2020-11-19 10:25:00')
    # print(data)
    # data = get_hisTick(symbol='rb2101', exchange='SHFE', end=str(datetime.datetime.now())[:19], count=10)
    # print(data)
    # data = get_hisTick(symbol='rb2101', exchange='SHFE', count=10)
    # print(data)


    # "TA105.CZCE"

    a = contract_depth(symbol='TA105', exchange='CZCE', end='2021-03-02 13:00:00')
    print(a)


    # data = get_hisBar(symbol='rb2101', exchange='SHFE', freq='1m', start='2020-10-20 09:50:00', end='2020-10-21 14:25:00')
    # print(data)
    # data = get_hisBar(symbol='rb2101', exchange='SHFE', freq='5m', start='2020-10-20 09:50:00', end='2020-10-21 14:25:00')
    # print(data)
    # data = get_hisBar(symbol='rb2101', exchange='SHFE', freq='15m', start='2020-10-20 09:50:00', end='2020-10-21 14:25:00')
    # print(data)
    # data = get_hisBar(symbol='rb2101', exchange='SHFE', freq='30m', start='2020-10-20 09:50:00', end='2020-10-21 14:25:00')
    # print(data)



    # data = contract_depth(symbol='rb2101', exchange='SHFE', end=str(datetime.datetime.now())[:19])
    # print(data)
    #
    # data = contract_depth(symbol='rb2101', exchange='SHFE')
    # print(data)


    # data = get_price(symbol='rb2101', exchange='SHFE', end=str(datetime.datetime.now())[:19])
    # print(data)
    #
    # data = get_price(symbol='rb2101', exchange='SHFE')
    # print(data)











