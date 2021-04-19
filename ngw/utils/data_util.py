

def get_variety_code(symbol_exchange):
    symbol = symbol_exchange.split('.')[0]
    if 'M' in symbol and symbol[0] != 'M':
        variety_code = symbol.replace('M', '')
        return variety_code
    if symbol == 'MAM':
        # print('MA')
        return 'MA'


def isin_TradeDatetimeList(datetimeStr=None, TradeDatetimeList=None):
    for b_e in TradeDatetimeList:
        begin = b_e.get('begin')
        end = b_e.get('end')
        datetimeStr = str(str(datetimeStr)[:19]).replace('-', '').replace(' ', '').replace(':', '')
        if datetimeStr >= begin and datetimeStr < end:
            return True
    return False
