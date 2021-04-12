__author__ = 'wangjian'
import ngwshare as ng

def get_name_mv(date, codes_list):
    body = {
        "table": 'LC_DIndicesForValuation',
        "code_list": codes_list,
        "field_list": ['TradingDay','TotalMV'],
        "alterField": "TradingDay",
        "startDate": date,
        "endDate": date
    }
    # print(body)
    data = ng.get_fromCode(body=body)
    return data


def get_close(date, codes_list):
    body = {
        "table": 'QT_DailyQuote',
        "code_list": codes_list,
        "field_list": ['TradingDay','ClosePrice'],
        "alterField": "TradingDay",
        "startDate": date,
        "endDate": date
    }
    data = ng.get_fromCode(body=body)
    return data

if __name__ == '__main__':
    import datetime
    date_ = str(datetime.datetime.now())[:10]
    date = str(datetime.datetime.now())[:19]

    # print(date_)
    # data = get_name_mv(date_, ['600006.SH','600722.SH','000895.SZ'])
    # print(data)
    # name = data[data.code == '600006.SH'].name.values[0]
    # TotalMVh = data[data.code == '600006.SH'].TotalMV.values[0]
    # print(name,TotalMVh)


    print(date)
    data = get_name_mv('2020-07-28 00:00:00', ['600006.SH','600722.SH','000895.SZ'])
    print(data)
    name = data[data.code == '600006.SH'].name.values[0]
    TotalMVh = data[data.code == '600006.SH'].TotalMV.values[0]
    print(name,TotalMVh)


    data = get_close('2020-07-28', ['600006.SH','600722.SH','000895.SZ'])
    print(data)


