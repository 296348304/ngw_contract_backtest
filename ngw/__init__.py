from ngw_contract_backtest.ngw.strategy.strategy import StrategyRunner


def create_strategy(info=None,initialize=None,create_universe=None,handle_data=None,run_daily=None):
    return StrategyRunner(info=info,initialize=initialize,create_universe=create_universe,handle_data=handle_data,run_daily=run_daily)










