import math

import pandas as pd

from config import Config
from bank_of_israel_rates import BankOfIsraelRates
from colmex_pro_orders_csv_headers import ColmexProOrdersCSVColumns as Columns
from form_1325_hebrew_text import Form1325HebrewText as Heb


class ColmexProOrdersToForm1325DF:
    COIN = "USD"
    BUY = "B"
    SELL = "S"

    def __init__(self, year: int, input_csv: str):
        self.YEAR = year
        self.INPUT_CSV = input_csv

    def get_shares(self, row):
        if row[Columns.SIDE] == self.SELL:
            return int(row[Columns.SHARES])
        else:
            return -1 * int(row[Columns.SHARES])

    @staticmethod
    def _symbol_df_to_trade_dfs(df: pd.DataFrame) -> list[pd.DataFrame]:
        dfs = []
        temp_df = pd.DataFrame(columns=df.columns)

        for index, row in df.iterrows():
            temp_df = pd.concat([temp_df, row.to_frame().T], ignore_index=True)
            if row[Columns.POSITION] == 0:
                dfs.append(temp_df.copy())
                temp_df = pd.DataFrame(columns=df.columns)

        # Append remaining rows if last Position != 0
        if not temp_df.empty:
            dfs.append(temp_df)

        return dfs

    def _get_trade_dfs(self, df: pd.DataFrame):
        symbol_dfs = df.groupby([Columns.SYMBOL], sort=False)
        trade_dfs = []
        for key, symbol_df in symbol_dfs:
            # Find the last row of each closed trade (identified by "Position" == 0)
            symbol_df[Columns.POSITION] = symbol_df.apply(self.get_shares, axis=1).cumsum()
            # Split the symbol df by rows where "Position" == 0 (which means the trade is closed)
            trade_dfs.extend(self._symbol_df_to_trade_dfs(symbol_df))
        return trade_dfs

    def _trade_df_to_form1325_rows(self, df: pd.DataFrame, rates: dict) -> list[dict]:
        results = []

        # Calculate total commissions and fees
        commissions_and_fees = df[Columns.COMMISSION].astype(float) + df[Columns.SEC_FEE].astype(float) + \
            df[Columns.TAF_FEE].astype(float) + df[Columns.ECN_FEE].astype(float) + \
            df[Columns.ROUTING_FEE].astype(float) + df[Columns.NSCC_FEE].astype(float)

        # Create a copy of the Shares column, for changing the value during iteration & also keeping the original number
        df[Columns.SHARES] = df[Columns.SHARES].astype(int)
        df[Columns.QUANTITY] = df[Columns.SHARES]

        # Separate Buy and Sell transactions and sort by Date
        buys = df[df[Columns.SIDE] == self.BUY].copy()
        sells = df[df[Columns.SIDE] == self.SELL].copy()

        # Calculate amount including commissions
        buys[Columns.AMOUNT] = buys[Columns.QUANTITY] * buys[Columns.PRICE].astype(float) + commissions_and_fees
        sells[Columns.AMOUNT] = sells[Columns.QUANTITY] * sells[Columns.PRICE].astype(float) - commissions_and_fees

        # Iterate over sell orders
        for sell_index, sell in sells.iterrows():
            shares_to_sell = sell[Columns.QUANTITY]

            # Iterate over buy orders
            while shares_to_sell > 0:
                # Find the oldest buy order for the same security
                buy = buys[buys[Columns.QUANTITY] > 0].iloc[0]
                buy_index = buy.name
                buy_rate = rates.get(buy[Columns.DATETIME].strftime(Config.DATE_FORMAT), 0)
                sell_rate = rates.get(sell[Columns.DATETIME].strftime(Config.DATE_FORMAT), 0)

                # Determine the shares and price for this transaction
                if buy[Columns.QUANTITY] <= shares_to_sell:
                    shares_sold = buy[Columns.QUANTITY]
                    shares_to_sell -= buy[Columns.QUANTITY]
                    buys.at[buy_index, Columns.QUANTITY] = 0  # All of this buy order is used up
                else:
                    shares_sold = shares_to_sell
                    buys.at[buy_index, Columns.QUANTITY] -= shares_to_sell
                    shares_to_sell = 0

                rate_change = 1 + ((sell_rate - buy_rate) / buy_rate)
                # Calculate average amount
                amount_sell = sell[Columns.AMOUNT] * (shares_sold / sell[Columns.SHARES]) * sell_rate
                amount_buy = buy[Columns.AMOUNT] * (shares_sold / buy[Columns.SHARES]) * buy_rate
                amount_buy_adjusted = amount_buy * rate_change
                profit_loss = self._get_profit_loss(amount_buy, amount_buy_adjusted, amount_sell)

                row = {
                    Heb.SYMBOL: sell[Columns.SYMBOL],
                    Heb.BOUGHT_DURING_PRE_MARKET: "",
                    Heb.SHARES: shares_sold,
                    Heb.BUY_DATE: buy[Columns.TRADE_DATE],
                    Heb.BUY_AMOUNT: amount_buy,
                    Heb.RATE_CHANGE: rate_change,
                    Heb.BUY_AMOUNT_ADJUSTED: amount_buy_adjusted,
                    Heb.SELL_DATE: sell[Columns.TRADE_DATE],
                    Heb.SELL_AMOUNT: amount_sell,
                    Heb.PROFIT: "" if profit_loss <= 0 else profit_loss,
                    Heb.LOSS: "" if profit_loss >= 0 else profit_loss,
                }
                results.append(row)
        return results

    @staticmethod
    def _get_profit_loss(amount_buy: float, amount_buy_adjusted: float, amount_sell: float):
        if math.copysign(1, amount_sell - amount_buy_adjusted) != math.copysign(1, amount_sell - amount_buy):
            return 0
        sign = math.copysign(1, amount_sell - amount_buy_adjusted)
        return sign * min(abs(amount_sell - amount_buy_adjusted), abs(amount_sell - amount_buy))

    def extract(self):
        with open(self.INPUT_CSV, newline="\r\n") as f:
            data = f.readlines()
            data = [
                list(map(lambda col: col.replace('"', "").rstrip(" "), row.rstrip(",\r\n").split(",")))
                for row in data if row.strip()
            ]
        df = pd.DataFrame(data[1:], columns=data[0])
        return df

    def transform(self, df: pd.DataFrame, rates: dict) -> pd.DataFrame:
        fmt = f"{Config.COLMEX_PRO_MTS_DATE_FORMAT} {Config.TIME_FORMAT}"
        df[Columns.DATETIME] = pd.to_datetime(df[Columns.TRADE_DATE] + " " + df[Columns.EXEC_TIME], format=fmt)
        df = df.sort_values(by=[Columns.DATETIME, Columns.SYMBOL, Columns.PRICE])

        trade_dfs = self._get_trade_dfs(df)
        form1325_rows = []
        for trade_df in trade_dfs:
            trade_1325_rows = self._trade_df_to_form1325_rows(trade_df, rates)
            form1325_rows.extend(trade_1325_rows)

        transformed_df = pd.DataFrame(form1325_rows)
        transformed_df[Columns.ROW_NUMBER] = transformed_df.reset_index().index + 1  # Add row number column
        transformed_df.insert(0, Columns.ROW_NUMBER, transformed_df.pop(Columns.ROW_NUMBER))  # Move to beginning

        # Reformat date columns
        for column in Heb.BUY_DATE, Heb.SELL_DATE:
            transformed_df[column] = pd.to_datetime(transformed_df[column]).\
                dt.strftime(Config.COLMEX_PRO_LOG_DATE_FORMAT)

        return transformed_df

    def run(self):
        df = self.extract()
        if df is not None:
            rates = BankOfIsraelRates.get_rates(self.YEAR, self.COIN)
            transformed_df = self.transform(df, rates)
            return transformed_df
