import datetime
import math
import ngwshare as ng
import pandas as pd
from ngw_contract_backtest.ngw.utils.freq_util import freq_1m

def str2datetime(str_date):
    str_date = str(str_date)
    if len(str_date) == 8:
        return datetime.datetime.strptime(str_date, '%Y%m%d')
    if len(str_date) == 10:
        return datetime.datetime.strptime(str_date, '%Y-%m-%d')
    elif len(str_date) == 19:
        return datetime.datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S')
    elif len(str_date) == 26:
        return datetime.datetime.strptime(str_date, '%Y-%m-%dT%H:%M:%S.%f')
    elif len(str_date) == 28:
        str_date = str_date.split('+')[0]
        return datetime.datetime.strptime(str_date, '%Y-%m-%dT%H:%M:%S.%f')
    elif len(str_date) == 14:
        return datetime.datetime.strptime(str_date, '%Y%m%d%H%M%S')
    elif len(str_date) == 8:
        return datetime.datetime.strptime(str_date, '%Y%m%d')



def get_trading_days():
    body = {
        "table": 'QT_TradingDayNew',
        "field_list": ['TradingDate', 'IfTradingDay', 'SecuMarket'],
        "alterField": 'TradingDate',
        "startDate": '2017-01-01',
        "endDate": '2024-01-01'
    }
    data = ng.get_fromDate(body)
    return data


def is_trading_day_on_data(date,data):
    date = str(date)[:10]+' 00:00:00'
    data = data.loc[data.SecuMarket==83].drop('SecuMarket',axis=1)
    # print(data)
    flag = data.loc[data.TradingDate==date].IfTradingDay.values[0]
    if flag == 1:
        return True
    else:
        return False

def is_trading_day(date=None, data=pd.DataFrame()):
    if data.empty:
        date = str(date)[:10]+' 00:00:00'
        body = {
                "table": 'QT_TradingDayNew',
                "field_list": ['TradingDate', 'IfTradingDay', 'SecuMarket'],
                "alterField": 'TradingDate',
                "startDate": '2017-01-01',
                "endDate": '2024-01-01'
        }
        data = ng.get_fromDate(body)
    data = data.loc[data.SecuMarket==83].drop('SecuMarket',axis=1)
    # print(data)
    flag = data.loc[data.TradingDate==date].IfTradingDay.values[0]
    if flag == 1:
        return True
    else:
        return False


def return_last_trading_day(date=None, data=pd.DataFrame()):
    if date:
        if isinstance(date,str):
            if len(date) == 10:
                now_date = datetime.datetime.strptime(date, '%Y-%m-%d')
            elif len(date) == 19:
                now_date =  datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            else:
                now_date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f')
        elif isinstance(date, datetime.date):
            now_date = date
        else:
            now_date = datetime.datetime.now()
    else:
        now_date = datetime.datetime.now()

    if data.empty:
        body = {
                "table": 'QT_TradingDayNew',
                "field_list": ['TradingDate', 'IfTradingDay', 'SecuMarket'],
                "alterField": 'TradingDate',
                "startDate": '2018-01-01',
                "endDate": '2024-01-01'
        }
        data = ng.get_fromDate(body)
    data = data.loc[data.SecuMarket==83].drop('SecuMarket',axis=1)
    # print(data)

    while True:
            l_date = now_date - datetime.timedelta(days=1)
            l_date = str(l_date)[:10] + ' 00:00:00'
            l_flag = data.loc[data.TradingDate == l_date].IfTradingDay.values[0]
            if l_flag == 1:
                return str(l_date)[:10]
            else:
                now_date = datetime.datetime.strptime(l_date, '%Y-%m-%d %H:%M:%S')
                continue


def return_next_trading_day(date=None, data=pd.DataFrame()):
    if date:
        if isinstance(date,str):
            if len(date) == 10:
                now_date = datetime.datetime.strptime(date, '%Y-%m-%d')
            elif len(date) == 19:
                now_date =  datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            else:
                now_date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f')
        elif isinstance(date, datetime.date):
            now_date = date
        else:
            now_date = datetime.datetime.now()
    else:
        now_date = datetime.datetime.now()

    if data.empty:
        body = {
                "table": 'QT_TradingDayNew',
                "field_list": ['TradingDate', 'IfTradingDay', 'SecuMarket'],
                "alterField": 'TradingDate',
                "startDate": '2018-01-01',
                "endDate": '2024-01-01'
        }
        data = ng.get_fromDate(body)
    data = data.loc[data.SecuMarket==83].drop('SecuMarket',axis=1)

    while True:
            l_date = now_date + datetime.timedelta(days=1)
            l_date = str(l_date)[:10] + ' 00:00:00'
            l_flag = data.loc[data.TradingDate == l_date].IfTradingDay.values[0]
            if l_flag == 1:
                return str(l_date)[:10]
            else:
                now_date = datetime.datetime.strptime(l_date, '%Y-%m-%d %H:%M:%S')
                continue



def return_last_next_tradingDay(start=None,end=None):
    start_time = start[11:19]
    end_time = end[11:19]
    start_datetime = str2datetime(start)
    end_datetime = str2datetime(end)

    body = {
            "table": 'QT_TradingDayNew',
            "field_list": ['TradingDate', 'IfTradingDay', 'SecuMarket'],
            "alterField": 'TradingDate',
            "startDate": '2018-01-01',
            "endDate": '2024-01-01'
    }
    data = ng.get_fromDate(body)
    data = data.loc[data.SecuMarket==83].drop('SecuMarket',axis=1)

    start_1_str = return_last_next('last', start_datetime, data, start_time)
    end_1_str = return_last_next('next', end_datetime, data, end_time)

    return start_1_str,end_1_str


def return_last_next(type,date,data,time):
    now_date = date
    if type == 'last':
        while True:
                l_date = now_date - datetime.timedelta(days=1)
                # print(l_date)
                l_date = str(l_date)[:10] + ' 00:00:00'
                l_flag = data.loc[data.TradingDate == l_date].IfTradingDay.values[0]
                if l_flag == 1:
                    return str(l_date)[:10] + ' ' + time
                else:
                    now_date = datetime.datetime.strptime(l_date, '%Y-%m-%d %H:%M:%S')
                    continue
    else:
        while True:
                l_date = now_date + datetime.timedelta(days=1)
                # print(l_date)
                l_date = str(l_date)[:10] + ' 00:00:00'
                l_flag = data.loc[data.TradingDate == l_date].IfTradingDay.values[0]
                if l_flag == 1:
                    return  str(l_date)[:10] + ' ' + time
                else:
                    now_date = datetime.datetime.strptime(l_date, '%Y-%m-%d %H:%M:%S')
                    continue



if __name__ == '__main__':
    import time
    data = get_trading_days()

    t11 = time.time()

    ld = return_last_trading_day(data=data)
    nd = return_next_trading_day(data=data)

    print(ld)
    print(nd)


    # data = get_TradeDatetime(variety='ag', start='2021-04-08', end='2021-05-13')
    # print(data)


    print(time.time()-t11)




    # start = str2datetime('2019-01-01')
    # end = str2datetime('2020-11-01')
    # print(start)
    # print(end)
    # diff = end-start
    #
    # a = return_last_trading_day(date=None)
    # print(a)




    # diff_days = diff.days
    # if diff_days>=150:
    #     run_times = math.ceil(diff_days/150)
    #     for i in range(run_times):
    #         print(i)
    #         end_temp = start + datetime.timedelta(days=150)
    #         if end_temp >= end:
    #             print(start,end)
    #             break
    #         print(start, end_temp)
    #         start = end_temp
    # else:
    #     pass




    # body = {
    #         "table": 'QT_TradingDayNew',
    #         "field_list": ['TradingDate', 'IfTradingDay', 'SecuMarket'],
    #         "alterField": 'TradingDate',
    #         "startDate": '2017-01-01',
    #         "endDate": '2024-01-01'
    # }
    # data1 = ng.get_fromDate(body)

    # date1 = str2datetime('2020-05-20')
    # print(date1)
    # print(type(date1))

    # for i in range(1000):
    #     date_ = datetime.datetime.now() + datetime.timedelta(days=i)
    #     is_trading = is_trading_day(date_)
    #     print(date_, is_trading)


    # i = 0
    # end = str(datetime.datetime.now())[:10]
    # start = end
    # while i<20:
    #     last_date = return_last_trading_day(start)
    #     i+=1
    #     start = str(last_date)[:10]
    #     print(i,last_date)
    #     print()
    #
    # print(start,end)

    # a = return_next_trading_day('2020-09-11')
    # print(a)

    # d_start = datetime.datetime.strptime('2020-09-14 09:00:00', '%Y-%m-%d %H:%M:%S')
    # d_next = datetime.datetime.strptime('2020-09-14 09:00:00', '%Y-%m-%d %H:%M:%S')
    # d_end = datetime.datetime.strptime('2020-11-12 15:00:00', '%Y-%m-%d %H:%M:%S')

    # first_datetime = d_start
    # start_datetime = d_start
    # next_datetime = d_start
    # first_date = d_start.date()
    # end_datetime = d_end
    # while True:
    #     if next_datetime == first_datetime:
    #         print(first_date,'    create_universe')
    #     next_datetime = start_datetime + datetime.timedelta(minutes=1)
    #     start_datetime = next_datetime
    #     if end_datetime < next_datetime:
    #         break
    #     if first_date != next_datetime.date():
    #         first_date = next_datetime.date()
    #         print(first_date,'    create_universe')
    #     print(next_datetime,'    handle_data_')
    #     print()


    # s,e = return_last_next_tradingDay(start='2020-09-14 09:00:00', end='2020-09-14 09:00:00')
    # print(s,len(s))
    # print(e,len(e))



    # while True:
    #     if d_next > d_end:
    #         break
    #
    #     if is_trading_day_on_data(d_next,data1):
    #         print(d_next)
    #         d_next_min = d_next
    #         while True:
    #             if str(d_next_min)[:10] > str(d_next)[:10]:
    #                 break
    #
    #             if str(d_next_min)[11:19] == '09:01:00':
    #                 pass
    #             if str(d_next_min)[11:19] in freq_1m:
    #                 print(d_next_min)
    #
    #             d_next_min = d_next_min + datetime.timedelta(minutes=1)
    #
    #
    #
    #     d_next = datetime.datetime.strptime(str(d_next)[:10]+' 00:00:00', '%Y-%m-%d %H:%M:%S') + datetime.timedelta(days=1)



