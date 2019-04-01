import pandas as pd
import numpy as np
import os
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.utility.factor_preprocess import FactorPreProcess

class BackTestStockAlpha(object):

    def __init__(self):
        pass

    def backtest_alpha_factor(self, factor_name):

        # 参数
        ####################################################################################################
        ipo_min_days = 90
        # factor_name = 'ROERankYOY'
        input_stock_pool = None
        input_backtest_date_series = None
        tradedays_yearly = 250
        transaction_cost = 0.0008
        stamp_tax = 0.001
        min_trade_volume = 0.0
        min_free_mv = 0.0
        need_alpha_norm_inv = True
        lead_lag_length = 50
        group_number = 10
        beg_date = "20040101"
        end_date = "20181001"
        backtest_period = "W"
        backtest_period_days = 5
        path = r'E:\3_Data\5_stock_data\3_alpha_model\backtest_alpha'
        ####################################################################################################

        # 所需要的数据
        ####################################################################################################
        alpha_factor = Stock().read_factor_h5(factor_name, Stock().get_h5_path(",y_alpha"))
        alpha_post = factor_name[-3:]
        alpha_factor_date_series = list(alpha_factor.columns)
        if need_alpha_norm_inv:
            alpha_factor = FactorPreProcess().inv_normalization(alpha_factor)

        trade_status = Stock().read_factor_h5("TradingStatus")
        trade_status_date_series = list(trade_status.columns)

        if alpha_post != 'Res':
            stock_pct = Stock().read_factor_h5("Pct_chg")
            stock_pct_date_series = list(stock_pct.columns)
        else:
            stock_pct = Stock().read_factor_h5("PctRes", Stock().get_h5_path("my_alpha"))
            stock_pct_date_series = list(stock_pct.columns)

        price_adjust = Stock().read_factor_h5("PriceCloseAdjust")
        price_adjust_date_series = list(price_adjust.columns)

        trade_volume = Stock().read_factor_h5("TradeVolumn")
        trade_volume_date_series = list(trade_volume.columns)

        free_mv = Stock().read_factor_h5("Mkt_freeshares")
        free_mv_date_series = list(free_mv.columns)

        ipo_days = Stock().get_ipo_date()
        ipo_days.columns = ['IpoDate', 'DelistDate']

        # 回测日期
        ####################################################################################################
        bt_beg_date = max(beg_date, trade_status_date_series[0], stock_pct_date_series[0], alpha_factor_date_series[0],
                          price_adjust_date_series[0], trade_volume_date_series[0], free_mv_date_series[0])
        bt_end_date = min(end_date, trade_status_date_series[-1], stock_pct_date_series[-1], alpha_factor_date_series[-1],
                          price_adjust_date_series[-1], trade_volume_date_series[-1], free_mv_date_series[-1])

        if input_backtest_date_series is None:
            backtest_date_series = Date().get_trade_date_series(bt_beg_date, bt_end_date, backtest_period)
        else:
            backtest_date_series = Date().get_trade_date_series(bt_beg_date, bt_end_date, "D")
            backtest_date_series = list(set(input_backtest_date_series) & set(backtest_date_series))
            backtest_date_series.sort()

        backtest_date_series = set(trade_status_date_series) & set(stock_pct_date_series) & \
                               set(alpha_factor_date_series) & set(price_adjust_date_series) & \
                               set(backtest_date_series) & set(trade_volume_date_series) & set(free_mv_date_series)
        backtest_date_series = list(backtest_date_series)
        backtest_date_series.sort()
        ####################################################################################################

        # 开始每日回测
        ####################################################################################################
        result = pd.DataFrame([], columns=['ValDate', "BuyDate", "SellDate"], index=backtest_date_series)
        lag_result = pd.DataFrame([], index=backtest_date_series)
        labels = ["Gp_" + str(x) for x in range(1, group_number + 1)]
        group_result = pd.DataFrame([], columns=labels, index=backtest_date_series)

        for i_date in range(0, len(backtest_date_series) - 1):

            # 日期
            ##############################################################################
            alpha_date = backtest_date_series[i_date]
            trade_date = Date().get_trade_date_offset(alpha_date, 1)
            next_alpha_date = backtest_date_series[i_date + 1]
            next_trade_date = Date().get_trade_date_offset(next_alpha_date, 1)
            print("BackTest Stock Alpha At %s" % alpha_date)
            ##############################################################################

            # 合并数据
            ##############################################################################
            alpha_factor_date = pd.DataFrame(alpha_factor[alpha_date])
            alpha_factor_date.columns = ['Alpha']

            next_alpha_factor_date = pd.DataFrame(alpha_factor[next_alpha_date])
            next_alpha_factor_date.columns = ['NextAlpha']

            trade_status_date = pd.DataFrame(trade_status[trade_date])
            trade_status_date.columns = ['Status']

            price_adjust_date = pd.DataFrame(price_adjust[trade_date])
            price_adjust_date.columns = ['Price']

            next_price_adjust_date = pd.DataFrame(price_adjust[next_trade_date])
            next_price_adjust_date.columns = ['NextPrice']

            all_data = pd.concat([alpha_factor_date, next_alpha_factor_date, trade_status_date,
                                  price_adjust_date, next_price_adjust_date, ipo_days], axis=1)
            all_data = all_data.dropna()
            ##############################################################################

            # 股票池
            # 剔除不能交易的股票
            # 剔除新股（还可以剔除流通市值或者交易额比较少的股票）
            # 是否有外部股票池
            ##############################################################################
            can_trade_code = all_data['Status'].map(lambda x: x in [0, 1])
            all_data = all_data.loc[can_trade_code, :]
            the_ipo_date = Date().get_trade_date_offset(alpha_date, -ipo_min_days)
            all_data = all_data.loc[all_data['IpoDate'] < the_ipo_date, :]
            all_data = all_data.dropna()

            if input_stock_pool is None:
                stock_pool = list(all_data.index)
                stock_pool.sort()
            else:
                stock_pool = list(set(input_stock_pool) & set(list(all_data.index)))
                stock_pool.sort()

            all_data = all_data.loc[stock_pool, :]
            all_data['Pct'] = all_data['NextPrice'] / all_data['Price'] - 1.0
            ##############################################################################

            # 计算因子的时滞性
            ##############################################################################
            # for i in np.arange(-lead_lag_length, lead_lag_length):
            #
            #     lag_alpha_date = Date().get_trade_date_offset(alpha_date, -i)
            #
            #     if lag_alpha_date in exposure.columns:
            #         alpha_factor_date = pd.DataFrame(exposure[lag_alpha_date])
            #         alpha_factor_date.columns = ['Alpha']
            #
            #         lag_all_data = all_data.copy()
            #         lag_all_data['Alpha'] = alpha_factor_date.loc[lag_all_data.index, 'Alpha']
            #
            #         lag_all_data['AlphaStand'] = lag_all_data['Alpha'] - lag_all_data['Alpha'].mean()
            #         lag_all_data['AlphaStand'] /= lag_all_data['Alpha'].std()
            #         lag_all_data['Weight'] = lag_all_data['AlphaStand'] / lag_all_data['AlphaStand'].abs().sum()
            #         ls_factor_return = (lag_all_data['Weight'] * lag_all_data['Pct']).sum()
            #         lag_result.loc[alpha_date, "Lag_" + str(i)] = ls_factor_return
            #     else:
            #         lag_result.loc[alpha_date, "Lag_" + str(i)] = np.nan
            ##############################################################################

            # 计算因子收益率 IC等
            ##############################################################################
            ic = all_data['Pct'].corr(all_data['Alpha'])
            rank_ic = all_data['Pct'].corr(all_data['Alpha'], method='spearman')
            all_data['AlphaStand'] = (all_data['Alpha'] - all_data['Alpha'].mean()) / all_data['Alpha'].std()
            all_data['Weight'] = all_data['AlphaStand'] / all_data['AlphaStand'].abs().sum()
            ls_factor_return = (all_data['Weight'] * all_data['Pct']).sum()
            port_alpha_exposure = (all_data['AlphaStand'] * all_data['AlphaStand']).sum()
            ls_factor_return_2 = (all_data['AlphaStand'] * all_data['Pct']).sum() / port_alpha_exposure
            auto_rank_corr = all_data['NextAlpha'].corr(all_data['Alpha'], method='spearman')
            ##############################################################################

            # 计算分组收益率
            ##############################################################################
            all_data_sort = all_data.sort_values(by=['Alpha'], ascending=False)
            labels = ["Gp_" + str(x) for x in range(1, group_number + 1)]
            all_data_sort['Gp'] = pd.qcut(all_data_sort['Alpha'], q=group_number, labels=labels)
            all_mean = all_data_sort['Pct'].mean()
            group_result.loc[alpha_date, labels] = all_data_sort.groupby(by=['Gp'])['Pct'].mean() - all_mean
            ##############################################################################

            # LongTopShortOtherReturn
            ##############################################################################
            all_data_sort = all_data.sort_values(by=['Alpha'], ascending=False)
            top_end_index = int(len(all_data) / group_number)
            all_data_sort['Score'] = 0.0
            all_data_sort.loc[all_data_sort.index[0:top_end_index], "Score"] = 1.0
            all_data_sort['Score'] -= all_data_sort['Score'].mean()
            all_data_sort['Score'] /= all_data_sort['Score'].abs().sum()
            long_top_short_other_return = (all_data_sort['Score'] * all_data_sort['Pct']).sum()
            ##############################################################################

            # ShortBottomLongOtherReturn
            ##############################################################################
            all_data_sort = all_data.sort_values(by=['Alpha'], ascending=True)
            top_end_index = int(len(all_data) / group_number)
            all_data_sort['Score'] = 0.0
            all_data_sort.loc[all_data_sort.index[0:top_end_index], "Score"] = -1.0
            all_data_sort['Score'] -= all_data_sort['Score'].mean()
            all_data_sort['Score'] /= all_data_sort['Score'].abs().sum()
            short_bottom_long_other_return = (all_data_sort['Score'] * all_data_sort['Pct']).sum()
            ##############################################################################

            # 写入Result
            ##############################################################################
            result.loc[alpha_date, "ValDate"] = alpha_date
            result.loc[alpha_date, "BuyDate"] = trade_date
            result.loc[alpha_date, "SellDate"] = next_trade_date
            result.loc[alpha_date, "RankIC"] = rank_ic
            result.loc[alpha_date, "IC"] = ic
            result.loc[alpha_date, "LSFactorReturn"] = ls_factor_return
            result.loc[alpha_date, 'AutoRankCorr'] = auto_rank_corr
            result.loc[alpha_date, 'StockNumber'] = len(all_data)
            result.loc[alpha_date, 'StdPct'] = all_data['Pct'].std()
            result.loc[alpha_date, 'ShortBottomLongOtherReturn'] = short_bottom_long_other_return
            result.loc[alpha_date, 'LongTopShortOtherReturn'] = long_top_short_other_return
            # LSFactorReturn = IC*std(AlphaStand)*std(StdPct)*(N-1)
            ##############################################################################

        # 每日循环结束 输出文件
        ####################################################################################################
        result['CumLSFactorReturn'] = result["LSFactorReturn"].cumsum()
        result['CumRankIC'] = result["RankIC"].cumsum()
        result['CumShortBottomLongOtherReturn'] = result["ShortBottomLongOtherReturn"].cumsum()
        result['CumLongTopShortOtherReturn'] = result["LongTopShortOtherReturn"].cumsum()

        group_result_cumsum = group_result.cumsum()
        lag_result_cumsum = lag_result.cumsum()
        ##############################################################################
        summary = pd.DataFrame([], columns=['Summary'])
        year_factor_return = result['LSFactorReturn'].mean() * tradedays_yearly / backtest_period_days
        year_factor_std = result['LSFactorReturn'].std() * np.sqrt(tradedays_yearly / backtest_period_days)
        ic_mean = result['RankIC'].mean()
        ic_std = result['RankIC'].std()
        mean_antocorr = result['AutoRankCorr'].mean()

        ####################################################################################################
        summary.loc["YearFactorReturn", 'Summary'] = year_factor_return
        summary.loc["YearFactorStd", 'Summary'] = year_factor_std
        summary.loc["YearFactorIR", 'Summary'] = year_factor_return / year_factor_std
        summary.loc["ICMean", 'Summary'] = ic_mean
        summary.loc["ICstd", 'Summary'] = ic_std
        summary.loc["ICIR", 'Summary'] = ic_mean / ic_std
        summary.loc["AntoCorr", 'Summary'] = mean_antocorr
        ####################################################################################################

        sub_path = os.path.join(path, factor_name)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)
        result.to_csv(os.path.join(sub_path, factor_name + '_Result.csv'))
        group_result_cumsum.to_csv(os.path.join(sub_path, factor_name + '_GroupResult.csv'))
        lag_result_cumsum.to_csv(os.path.join(sub_path, factor_name + '_LagResult.csv'))
        summary.to_csv(os.path.join(sub_path, factor_name + '_Summary.csv'))
        ####################################################################################################


if __name__ == '__main__':

    factor_name = 'HolderBySFIfRes'
    date = '20171229'
    BackTestStockAlpha().backtest_alpha_factor(factor_name)
