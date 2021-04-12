import datetime
import time
from ngw_contract_backtest.ngw.utils.date_util import str2datetime
from ngw_contract_backtest.ngw.data.data_api import get_hisBar, get_all_hisBar


class DataCache(object):
    def __init__(self,start,end,freq,universe):
        self.start = start
        self.end = end
        self.freq = freq
        self._universe = universe

        self.data = {}


    def init_data(self):
        if not self._universe:
            return self.data
        for i in self._universe:
            t11 = time.time()
            symbol = i.split('.')[0]
            exchange = i.split('.')[1]
            data = get_all_hisBar(symbol=symbol, exchange=exchange, freq=self.freq, start=self.start,end=self.end)
            self.data[i] = data
            print('{}  预加载数据成功!  {} s'.format(i,str(time.time()-t11)[:4]))
        return self.data

    def add_minute(self, str_date, minutes):
        str_datetime = datetime.datetime.strptime(str(str_date), '%Y%m%d%H%M%S') + datetime.timedelta(minutes=minutes)
        return int(str(str_datetime)[:19].replace('-', '').replace(' ', '').replace(':', ''))


if __name__ == '__main__':
    import time

    start = '2020-09-10 09:00:00'
    end = '2020-11-12 15:00:00'
    freq = '1m'
    # universe = ['rb2101.SHFE','i2011.DCE','cu2101.SHFE']
    universe = ['rb2101.SHFE']
    cache = DataCache(start,end,freq,universe)
    cache.init_data()

    print(cache.data)


    t11 = time.time()

    df_data = cache.data.get('rb2101.SHFE')
    start = 20200909210200
    end = 20201112225800
    date_list = df_data.loc[(df_data["time"] >= start) & (df_data["time"] <= end)]["time"].tolist()
    date_list = [str(datetime.datetime.strptime(str(i), '%Y%m%d%H%M%S'))[:19] for i in date_list]
    print(date_list)
    print(len(date_list))

    print(time.time()-t11)

    # df_data = cache.data.get('rb2101.SHFE')
    # r_data = df_data.loc[df_data["time"] <= 20200914230500][-1:]
    # r_data_ = r_data.sort_values(by='time').reset_index(drop=True)
    # print(r_data_)


    # df_data = cache.data.get('i2011.DCE')
    # r_data = df_data.loc[df_data["time"] <= 20200914230500][-1:]
    # r_data_ = r_data.sort_values(by='time').reset_index(drop=True)
    # print(r_data_)



    # df_data = cache.data.get('cu2101.SHFE')
    # r_data = df_data.loc[df_data["time"] <= 20200914230500][-1:]
    # r_data_ = r_data.sort_values(by='time').reset_index(drop=True)
    # print(r_data_)










