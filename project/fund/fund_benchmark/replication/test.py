

from quant.stock.stock import Stock
from quant.stock.date import Date
import pandas as pd
pct = Stock().read_factor_h5("Pct_chg")
price = Stock().read_factor_h5("Price_Adjust")
pct_2 = price.T.pct_change(fill_method=None).T * 100

diff = pct.sub(pct_2)
date = diff.abs().max().argmax()
diff_date = diff[date]
stock = diff_date.abs().argmax()
beg_date = Date().get_trade_date_offset(date, -10)
end_date = Date().get_trade_date_offset(date, 4)
print(stock, date)
print(diff.loc[stock, beg_date:end_date])
print(pct.loc[stock, beg_date:end_date])
print(pct_2.loc[stock, beg_date:end_date])
print(price.loc[stock, beg_date:end_date])
print(price.loc[stock, beg_date:end_date].pct_change())