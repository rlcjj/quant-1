from quant.utility.code_format import CodeFormat
from quant.source.wind_portfolio import *
from quant.source.wind_portfolio import WindPortUpLoad

""" 超预期30组合 """

def get_history_wind_portfolio():

    project_path = r'E:\Data\portfolio\other_portfolio\exceed_expectation'
    wind_port_path = WindPortUpLoad().path
    name = "超预期30"
    stock_ratio = 0.95

    file = os.path.join(project_path, "超预期30组合历史持仓.xlsx")
    data = pd.read_excel(file)
    data.columns = ["Date", "Code", "Weight", "Industry"]
    data["Code"] = data["Code"].map(CodeFormat().stock_code_add_postfix)
    data["Date"] = data["Date"].map(Date().change_to_str)
    data["Price"] = 0.0
    data["Direction"] = "Long"
    data["CreditTrading"] = "No"

    date_list = list(set(data["Date"]))
    date_list.sort()

    out_sub_path = os.path.join(wind_port_path, name)
    if not os.path.exists(out_sub_path):
        os.makedirs(out_sub_path)

    for i_date in range(len(date_list)):

        date = date_list[i_date]
        data_date = data[data["Date"] == date]
        data_date.index = data_date['Code']
        del data_date['Code']
        data_date['Weight'] *= stock_ratio
        data_date.loc['Cash', 'Weight'] = 1 - stock_ratio
        data_date["Price"] = 0.0
        data_date["Direction"] = "Long"
        data_date["CreditTrading"] = "No"
        data_date['Date'] = date
        out_file = os.path.join(out_sub_path, name + "_" + date + '.csv')
        data_date.to_csv(out_file)


def get_month_wind_portfolio(file_name, date):

    project_path = r'E:\Data\portfolio\other_portfolio\exceed_expectation'
    wind_port_path = WindPortUpLoad().path
    name = "超预期30"
    stock_ratio = 0.95

    file = os.path.join(project_path, file_name)
    data = pd.read_excel(file, index_col=[0])
    data.index.name = 'Code'

    data['Weight'] = 1 / len(data)
    data['Weight'] *= stock_ratio
    data.loc['Cash', 'Weight'] = 1 - stock_ratio

    data["CreditTrading"] = "No"
    data["Date"] = date
    data["Price"] = 0.0
    data["Direction"] = "Long"

    out_sub_path = os.path.join(wind_port_path, name)
    out_file = os.path.join(out_sub_path, name + "_" + date + '.csv')
    data.to_csv(out_file)

if __name__ == "__main__":

    #########################################################
    # get_history_wind_portfolio()
    # WindPortUpLoad().upload_weight_period("超预期30")
    #########################################################

    #########################################################
    # file_name = "超预期30组合持仓20180928.xlsx"
    # date = '20180928'
    # get_month_wind_portfolio(file_name, date)

    file_name = "超预期30组合持仓20181228.xlsx"
    date = '20181228'
    get_month_wind_portfolio(file_name, date)
    WindPortUpLoad().upload_weight_date('超预期30', date)
    #########################################################
