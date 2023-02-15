import numpy as np
import pandas as pd
import datetime


class Portfolio:
    """
    Input: Fund Net Asset Value Time Series(pandas.Series), start_time(datetime.date), end_time(datetime.date)
        NAV:  dtype == 'float64', len(NAV) > 0
        Only daily NAV is supported(And non-trading days are not included in the time series)
            Split-adjusted net asset value is the best.
            Accumulative net asset value is alternative.
            Unadjusted net asset value is likely to be biased.

    Output: Performance Indicators
    """

    def __init__(self):


class FundPerformance:
    """
    Input: Fund Net Asset Value Time Series(pandas.Series), start_time(datetime.date), end_time(datetime.date)
        NAV:  dtype == 'float64', len(NAV) > 0
        Only daily nav is supported(And non-trading days are not included in the time series)
            Split-adjusted net asset value is the best.
            Accumulative net asset value is alternative.
            Unadjusted net asset value is likely to be biased.

    Output: Performance Indicators
    """

    def __init__(self, portfolio_nav: pd.Series, benchmark_nav: pd.Series):
        assert type(portfolio_nav)==pd.Series
        assert len(portfolio_nav) > 0
        assert portfolio_nav.dtype == 'float64'
        assert type(benchmark_nav) == pd.Series
        assert len(benchmark_nav) > 0
        assert benchmark_nav.dtype == 'float64'
        self.portfolio_nav = portfolio_nav.sort_index(ascending=True)
        self.benchmark_nav = benchmark_nav

    def raw_daily_return_series(self, start_time:datetime.date, end_time:datetime.date, use_portfolio_nav=True):
        if use_portfolio_nav == 1:
            p = self.portfolio_nav.loc[start_time: end_time]
        else:
            p = self.benchmark_nav.loc[start_time: end_time]
        # Convert the pd.Series into array before division, because the calculation is done based on the index
        # which means
        raw_daily_return_series = (p.diff(1)/p).dropna()
        return raw_daily_return_series

    def risk_free_rate(self, fixed_risk_free_rate, start_time: datetime.date, end_time: datetime.date, annual=1):
        p_ts = self.portfolio_nav.loc[start_time:end_time]
        holding_days = len(p_ts)
        risk_free_rate = fixed_risk_free_rate
        if annual == 1:
            risk_free_rate = (1 + fixed_risk_free_rate) ** (holding_days/252) - 1
        return risk_free_rate

    def holding_period_yield(self, start_time:datetime.date, end_time:datetime.date, annual=1):
        p_ts = self.portfolio_nav.loc[start_time:end_time]
        holding_days = len(p_ts)
        holding_period_yield = p_ts[end_time]/p_ts[start_time] - 1
        if annual == 1:
            holding_period_yield = (1 + holding_period_yield) ** (252/holding_days) - 1
        return holding_period_yield

    def holding_period_vol(self, start_time:datetime.date, end_time:datetime.date, annual=1):
        daily_return_series = self.raw_daily_return_series(start_time, end_time, use_portfolio_nav=True)
        # numpy.ndarray.std() and pandas.Series.std() give sample standard deviation
        # (i.e.  SS divided by n-1 ,not n) if ddof=1
        holding_period_vol = daily_return_series.std(ddof=1)
        if annual == 1:
            holding_period_vol = holding_period_vol * (252 ** 0.5)
        return holding_period_vol

    def sharpe(self, start_time:datetime.date, end_time:datetime.date, fixed_risk_free_rate=0.02):
        holding_period_yield = self.holding_period_yield(start_time, end_time, annual=1)
        holding_period_vol = self.holding_period_vol(start_time, end_time, annual=1)
        risk_free_rate = self.risk_free_rate(fixed_risk_free_rate, start_time, end_time, annual=1)
        return (holding_period_yield - risk_free_rate)/holding_period_vol

    def drawdown(self, start_time:datetime.date, end_time:datetime.date):
        p_ts = self.portfolio_nav.loc[start_time: end_time]
        drawdown = min([p_ts[end_time]/p_ts.max() - 1, 0])
        return drawdown

    def drawdown_series(self, start_time:datetime.date, end_time:datetime.date):
        p_ts = self.portfolio_nav.loc[start_time: end_time]
        holding_days = len(p_ts)
        # The dtype of empty pd.Series must be object now
        drawdown_series = pd.Series(dtype=object)
        for i in range(2, holding_days):
            date = p_ts.index[i-1]
            pi_ts = p_ts[0:i]
            drawdown_series[date] = min([pi_ts[date]/pi_ts.max() - 1, 0])
        return pd.Series(drawdown_series, dtype='float64')

    def maximum_drawdown(self, start_time:datetime.date, end_time:datetime.date):
        drawdown_series = self.drawdown_series(start_time, end_time)
        return min(drawdown_series)

    def calmar(self, start_time:datetime.date, end_time:datetime.date, fixed_risk_free_rate=0.02):
        maximum_drawdown = self.maximum_drawdown(start_time, end_time)
        risk_free_rate = self.risk_free_rate(fixed_risk_free_rate, start_time, end_time)
        calmar = (self.holding_period_yield(start_time, end_time, annual=1) - risk_free_rate)/maximum_drawdown
        return calmar

    def benchmark_return(self, start_time:datetime.date, end_time:datetime.date, annual=1):
        p_ts = self.benchmark_nav.loc[start_time: end_time]
        benchmark_return = p_ts[end_time]/p_ts[start_time] - 1
        holding_days = len(p_ts)
        if annual == 1:
            benchmark_return = (1 + benchmark_return) ** (252/holding_days) - 1
        return benchmark_return

    def tracking_error(self, start_time:datetime.date, end_time:datetime.date, annual=1):
        r_ts = self.raw_daily_return_series(start_time, end_time, use_portfolio_nav=True)
        r1_ts = self.raw_daily_return_series(start_time, end_time, use_portfolio_nav=False)
        diff = r_ts - r1_ts
        tracking_error = diff.std(ddof=1)
        if annual == 1:
            tracking_error = tracking_error * (252 ** 0.5)
        return tracking_error

    def information_ratio(self, start_time:datetime.date, end_time:datetime.date):
        benchmark_return = self.benchmark_return(start_time, end_time, annual=1)
        holding_period_yield = self.holding_period_yield(start_time, end_time, annual=1)
        tracking_error = self.tracking_error(start_time, end_time, annual=1)
        information_ratio = (holding_period_yield - benchmark_return)/tracking_error
        return information_ratio

    def std_downside(self, start_time: datetime.date, end_time: datetime.date, minimum_acceptable_annual_return=0):
        r_ts = self.raw_daily_return_series(start_time, end_time, use_portfolio_nav=True)
        r1_ts = self.raw_daily_return_series(start_time, end_time, use_portfolio_nav=False)

        if minimum_acceptable_annual_return == 0:
            diff = r_ts - r1_ts
        else:
            daily_mar = minimum_acceptable_annual_return/252
            diff = r_ts - daily_mar

        for i in range(0, len(diff)):
            diff[i] = min([diff[i], 0])
        std_downside = diff.std(ddof=1)
        return std_downside

    def sortino(self, start_time: datetime.date, end_time: datetime.date, fixed_risk_free_rate=0.02):
        risk_free_rate = self.risk_free_rate(fixed_risk_free_rate, start_time, end_time, annual=1)
        holding_period_yield = self.holding_period_yield(start_time, end_time, annual=1)
        std_downside = self.std_downside(start_time, end_time)
        sortino_ratio = (holding_period_yield - risk_free_rate)/std_downside
        return sortino_ratio


if __name__ == "__main__":
    df = pd.read_excel("D:/Raychill Capital/Inboard/JinxinNo1/港曾-晋奕定投计划1号.xlsx", sheet_name='晋信私募基金1号-估值表')
    date = df.日期.copy()
    for i in range(0, len(date)):
        date[i] = date[i].date()
    portfolio_nav = pd.Series(df['晋信1号单位净值'].values, index=date)
    label = df.columns[1]
    benchmark_nav = pd.Series(df[label].values, index=date)
    back_test_1 = FundPerformance(portfolio_nav, benchmark_nav)
    # print(back_test_1.raw_daily_return_series(datetime.date(2022, 9, 13), datetime.date(2023, 1, 13)))
    # print('risk_free_rate:')
    # print(back_test_1.risk_free_rate(0.02, datetime.date(2022, 9, 13), datetime.date(2023, 1, 13)))
    # print('holding_period_vol:')
    # print(back_test_1.holding_period_vol(datetime.date(2022, 9, 13), datetime.date(2023, 1, 13)))
    # print('sharpe:')
    # print(back_test_1.sharpe(datetime.date(2022, 9, 13), datetime.date(2023, 1, 13)))
    # print('maximum_drawdown:')
    # print(back_test_1.maximum_drawdown(datetime.date(2022, 9, 13), datetime.date(2023, 1, 13)))
    # print('calmar:')
    # print(back_test_1.calmar(datetime.date(2022, 9, 13), datetime.date(2023, 1, 13)))
    # print('std_downside:')
    # print(back_test_1.std_downside(datetime.date(2022, 9, 13), datetime.date(2023, 1, 13)))
    # print('sortino:')
    # print(back_test_1.sortino(datetime.date(2022, 9, 13), datetime.date(2023, 1, 13)))
    print('information_ratio:')
    print(back_test_1.information_ratio(datetime.date(2022, 9, 13), datetime.date(2023, 1, 13)))


