__author__ = 'wangjian'
import math
import numpy as np

def get_daily_earning(st_values):
    """
    :param st_values:
    :return: 每日收益
    """
    if not st_values or len(st_values) == 1:
        return None
    daily_earning = st_values[-1] - st_values[-2]
    return round(daily_earning, 4)

def get_daily_return(st_values):
    """
    :param st_values:
    :return: 每日收益率
    """
    if not st_values or len(st_values) == 1:
        return None
    daily_return = (st_values[-1] / st_values[-2]) - 1
    return round(daily_return, 4)

def get_daily_returns(values):
    """
    :param st_values:
    :return: 每日收益率
    """
    if not values or len(values) == 1:
        return None
    daily_returns = [0] * (len(values) - 1)
    for key, value in enumerate(values[1:]):
        if not values[key] or not value or np.isnan(value / values[key]):
            continue
        daily_returns[key] = value / values[key] - 1.
    return daily_returns

# 三个折线图
def get_accumulative_earning(st_values):
    """
    :param st_values:
    :return: 累计收益
    """
    if not st_values or len(st_values) == 1:
        return None
    accumulative_earning = st_values[-1] - st_values[0]
    return round(accumulative_earning, 4)

def get_accumulative_return(values):
    """
    :param values:
    :return: 累计收益率
    """
    if not values or len(values) == 1:
        return None
    accumulative_return = (values[-1] / values[0]) - 1
    return round(accumulative_return, 4)

def get_relative_return(st_values, bm_values):
    """

    :param _return:
    :param bench_return:
    :return: 相对收益率
    """
    if not st_values or len(st_values) == 1:
        return None
    _return = get_accumulative_return(st_values)
    bm_return = get_accumulative_return(bm_values)
    relative_return = _return - bm_return
    return round(relative_return, 4)

def get_logarithm_return(values):
    """
    :param values:
    :return: 对数收益率
    """
    if not values or len(values) == 1:
        return None
    logarithm_return = math.log(values[-1] / values[0], math.e)
    return round(logarithm_return, 4)

# 风险指标
def get_max_drawdown(dates, st_values):
    """
    :param dates:
    :param st_values:
    :return: 最大回撤、开始时间、结束时间
    """
    if not st_values or len(st_values) == 1:
        return None,None,None
    # del dates[0]
    # del st_values[0]
    dates = dates[1:]
    st_values = st_values[1:]
    drawdowns_item = []
    drawdowns = []
    for i, v in enumerate(st_values):
        values_ = st_values[:i + 1]
        max_values_ = max(values_)
        start_index = values_.index(max_values_)
        drawdown = 1 - (v / max_values_)
        drawdowns_item.append({'drawdowm': drawdown, 'start_index': start_index, 'end_index': i})
        drawdowns.append(drawdown)
    try:
        max_drawdown = max(drawdowns)
    except:
        return None,None,None
    if max_drawdown == 0:
        return None,None,None
    start_date = None
    end_date = None
    for i in drawdowns_item:
        if i['drawdowm'] == max_drawdown:
            start_date = dates[i['start_index']]
            end_date = dates[i['end_index']]
    return round(max_drawdown, 4), start_date, end_date

def get_accumulative_returns(values):
    """
    :param values:
    :return: 每日 累积收益率
    """
    if not values or len(values) == 1:
        return None
    accumulative_returns = []
    for i in range(len(values) - 1):
        accumulative_return = (values[i + 1] / values[0]) - 1
        accumulative_returns.append(round(accumulative_return, 4))
    return accumulative_returns

def get_volatility(st_returns):
    """
    # 收益率波动率 = 每日收益率的年化标准差
    :param returns:
    :return: 波动率
    """
    if not st_returns or len(st_returns) == 1:
        return None
    std_i = []
    for i in st_returns:
        std_i.append((i - np.mean(st_returns)) ** 2)
    volatility = np.sqrt((250 / (len(st_returns))) * sum(std_i))
    return round(volatility, 4)

    # # volatility
    # volatility = np.std(st_returns, ddof=1) * 365 ** 0.5
    # if volatility in [-np.inf, np.inf] or np.isnan(st_vol):
    #     return None
    # else:
    #     return round(volatility, 4)

def get_annualized_return(values):
    # print(values)
    if not values or len(values) == 1:
        return None
    annualized_return = (values[-1] / values[0]) ** (250 / (len(values)-1)) - 1
    return round(annualized_return, 4)

def get_riskfree_rate():
    return 0.02

def get_CAPM(returns, bm_returns, annualized, bm_annualized, riskfree):
    if not returns or len(returns) == 1:
        return None, None
    mu_st = sum(returns) / len(returns)
    mu_bm = sum(bm_returns) / len(bm_returns)
    mul = [returns[i] * bm_returns[i] for i in range(len(returns))]
    cov = sum(mul) / len(returns) - mu_st * mu_bm
    var_bm = np.std(bm_returns) ** 2
    if np.isnan(cov / var_bm):
        return None, None
    beta = cov / var_bm
    if beta in [-np.inf, np.inf] or np.isnan(beta):
        return None, None
    alpha = (annualized - riskfree) - beta * (bm_annualized - riskfree)
    return round(alpha, 4), round(beta, 4)

def get_sharpe_ratio(annualized, volatility, riskfree):
    if not annualized or not volatility:
        return None
    sharpe = (annualized - riskfree) / volatility
    return round(sharpe, 4)

def get_information_ratio(returns, bm_returns, annualized, bm_annualized):
    if not returns or len(returns) == 1:
        return None
    diff = [returns[i] - bm_returns[i] for i in range(len(returns))]
    annulized_std = (np.var(diff, ddof=0) * 250) ** 0.5  # ddof=0 除以n
    IR = (annualized - bm_annualized) / annulized_std
    return round(IR, 4)


def get_daily_rate(values):
    if not values or len(values) == 1:
        return None
    win_daily_rate_nums = 0
    loss_daily_rate_nums = 0
    for i in range(len(values) - 1):
        pnl = values[i + 1]  - values[i]
        if pnl > 0:
            win_daily_rate_nums+=1
        if pnl < 0:
            loss_daily_rate_nums+=1
    try:
        win_daily_rate = round(win_daily_rate_nums/(win_daily_rate_nums+loss_daily_rate_nums), 4)
    except:
        win_daily_rate = 0
    return win_daily_rate

# def get_daily_rate(values):
#     if not values or len(values) == 1:
#         return None
#     win_daily_rate_nums = 0
#     for i in range(len(values) - 1):
#         pnl = values[i + 1]  - values[i]
#         if pnl > 0:
#             win_daily_rate_nums+=1
#     win_daily_rate = round(win_daily_rate_nums/len(values), 4)
#     return win_daily_rate


def get_win_rate(orders=None):
    win_times = 0
    for order in orders:
        if order['side'] in ['close_long','close_short']:
            pnl = order['pnl']
            commission = order['commission']
            if pnl > 2*commission:
                win_times+=1
    try:
        win_rate = round(win_times/len(orders), 4)
    except:
        win_rate = 0
    return win_rate


def calculate(dates=None, st_values=None, equitiesNoComm=None):
    daily_earning = get_daily_earning(st_values)
    daily_return = get_daily_return(st_values)
    max_drawdown, start, end = get_max_drawdown(dates, st_values)
    st_acc_returns = get_accumulative_return(st_values)
    st_returns = get_daily_returns(st_values)
    volatility = get_volatility(st_returns)
    riskfree = get_riskfree_rate()
    st_annualized = get_annualized_return(st_values)
    sharpe = get_sharpe_ratio(st_annualized, volatility, riskfree)
    st_acc_return_ = round(st_acc_returns,4) if st_acc_returns else None
    # 计算日胜率 扣手续费之前 扣手续费之后
    daily_rate_after = get_daily_rate(st_values)
    if equitiesNoComm:
        daily_rate_before = get_daily_rate(equitiesNoComm)
    else:
        daily_rate_before = 0

    data_ = {
        'st_d_return_value':daily_earning,
        'st_d_return': daily_return,
        'st_annualized':st_annualized,
        'st_acc_return_': st_acc_return_,
        'volatility': volatility,
        'sharpe': sharpe,
        'max_drawdown': [max_drawdown, start, end],
        'daily_win_rate':daily_rate_after,
        'daily_win_rate_before': daily_rate_before
    }
    return data_



if __name__ == '__main__':
    from pprint import pprint

    dates = ['2020-01-02', '2020-01-03', '2020-01-06', '2020-01-07', '2020-01-08', '2020-01-09', '2020-01-10', '2020-01-13',
     '2020-01-14', '2020-01-15', '2020-01-16', '2020-01-17', '2020-01-20', '2020-01-21', '2020-01-22', '2020-01-23',
     '2020-02-03', '2020-02-04', '2020-02-05', '2020-02-06', '2020-02-07', '2020-02-10', '2020-02-11', '2020-02-12',
     '2020-02-13', '2020-02-14', '2020-02-17', '2020-02-18', '2020-02-19', '2020-02-20', '2020-02-21', '2020-02-24',
     '2020-02-25', '2020-02-26', '2020-02-27', '2020-02-28', '2020-03-02', '2020-03-03', '2020-03-04', '2020-03-05',
     '2020-03-06', '2020-03-09', '2020-03-10', '2020-03-11', '2020-03-12', '2020-03-13', '2020-03-16', '2020-03-17',
     '2020-03-18', '2020-03-19', '2020-03-20', '2020-03-23', '2020-03-24', '2020-03-25', '2020-03-26', '2020-03-27',
     '2020-03-30', '2020-03-31', '2020-04-01', '2020-04-02', '2020-04-03', '2020-04-07', '2020-04-08', '2020-04-09',
     '2020-04-10', '2020-04-13', '2020-04-14', '2020-04-15', '2020-04-16', '2020-04-17', '2020-04-20', '2020-04-21',
     '2020-04-22', '2020-04-23', '2020-04-24', '2020-04-27', '2020-04-28', '2020-04-29', '2020-04-30', '2020-05-06',
     '2020-05-07', '2020-05-08', '2020-05-11', '2020-05-12', '2020-05-13', '2020-05-14', '2020-05-15', '2020-05-18',
     '2020-05-19', '2020-05-20', '2020-05-21', '2020-05-22', '2020-05-25', '2020-05-26', '2020-05-27', '2020-05-28',
     '2020-05-29', '2020-06-01', '2020-06-02', '2020-06-03', '2020-06-04', '2020-06-05', '2020-06-08', '2020-06-09',
     '2020-06-10', '2020-06-11']
    st_values = [2000000, 1984872.0, 1987076.0, 1982582.0, 1969937.0, 2002573.0, 2017798.0, 2023667.0, 1996146.0, 1972167.0,
     1979094.0, 2025248.0, 2040990.0, 1988913.0, 1980649.0, 1980649.0, 1980649.0, 2039127.0, 2108351.0, 2086989.0,
     2082027.0, 2069964.0, 2069964.0, 2214884.0, 2251083.0, 2312767.0, 2366141.0, 2370020.0, 2407904.0, 2486261.0,
     2514385.0, 2496288.0, 2496288.0, 2496288.0, 2496288.0, 2496288.0, 2496288.0, 2475797.0, 2506913.0, 2533198.0,
     2517201.0, 2466455.0, 2466455.0, 2421473.0, 2384545.0, 2384545.0, 2384545.0, 2384545.0, 2384545.0, 2384545.0,
     2384545.0, 2396736.0, 2442270.0, 2454519.0, 2440216.0, 2474972.0, 2489459.0, 2519250.0, 2519250.0, 2620347.0,
     2637851.0, 2683962.0, 2663367.0, 2675336.0, 2675336.0, 2675336.0, 2675336.0, 2675336.0, 2675336.0, 2675336.0,
     2676997.0, 2629841.0, 2618613.0, 2595770.0, 2592170.0, 2603170.0, 2623590.0, 2586002.0, 2586002.0, 2586002.0,
     2586002.0, 2586002.0, 2586002.0, 2568624.0, 2554081.0, 2546042.0, 2546042.0, 2559550.0, 2530683.0, 2518369.0,
     2514208.0, 2461382.0, 2474151.0, 2494558.0, 2499299.0, 2503835.0, 2467400.0, 2549807.0, 2564473.0, 2559921.0,
     2584843.0, 2623417.0, 2715309.0, 2699208.0, 2670905.0, 2633009.0]


    performace = calculate(dates, st_values)
    pprint(performace)

    a = (st_values[-1] / st_values[0]) - 1
    a = round(a, 4)
    print(a)

    print(len(st_values))
    b = (a/len(st_values))*250
    print(b)


    # a = get_daily_rate(st_values)
    # print(a)


    # get_win_rate(orders=None)


















