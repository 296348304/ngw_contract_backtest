import ngshare as ng
__author__ = 'wangjian'


def turn_main_contract(variety_code=None):
    symbol = ng.get_main_contract(variety_code=variety_code)['symbol']
    return symbol