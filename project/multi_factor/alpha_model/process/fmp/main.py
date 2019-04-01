import os

import pandas as pd
from project.multi_factor.alpha_model.process.fmp import FMP

if __name__ == '__main__':

    # params
    #####################################################################################
    params_file = r'E:\3_Data\5_stock_data\3_alpha_model\fmp\input_file\neutral_list.xlsx'
    path = r'E:\3_Data\5_stock_data\3_alpha_model\fmp'
    stock_pool_list = ['000905.SH', 'Astock', '000300.SH']
    beg_date = "20070105"
    end_date = "20181009"
    periods = "W"

    params = pd.read_excel(params_file, index_col=[0])
    alpha_factor_list = list(set(params.index))

    #####################################################################################
    # neutralize = 'Raw'
    # W_mat = 'Equal'
    #
    # for i_factor in range(0, len(alpha_factor_list)):
    #     for i_stock_pool in range(len(stock_pool_list)):
    #
    #         stock_pool = stock_pool_list[i_stock_pool]
    #         alpha_factor_name = alpha_factor_list[i_factor]

    #         print(stock_pool, alpha_factor_name)
    #         fmp = FMP()
    #         fmp.get_data(alpha_factor_name, beg_date, end_date, periods)
    #         fmp.cal_fmp(neutralize, W_mat, stock_pool)
    #         fmp.alpha_contribution(neutralize, W_mat, stock_pool)

    #####################################################################################
    params = pd.read_excel(params_file)
    neutralize = 'Res'
    W_mat = 'Equal'
    params = params.dropna()

    for i_factor in range(1, len(params)):
        stock_pool = params.loc[params.index[i_factor], 'market']
        alpha_factor_name = params.loc[params.index[i_factor], 'name']
        sub_path = os.path.join(path, 'summary')
        filename = os.path.join(sub_path, '%s_%s_%s_%s_Summary.xlsx' % (alpha_factor_name, neutralize, W_mat, stock_pool))
        if os.path.exists(filename):
            pass
        else:
            print(stock_pool, alpha_factor_name)
            fmp = FMP()
            fmp.get_data(alpha_factor_name, beg_date, end_date, periods)
            fmp.cal_fmp(neutralize, W_mat, stock_pool)
            fmp.alpha_contribution(neutralize, W_mat, stock_pool)


