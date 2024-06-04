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

    def __init__(self, input_csv: str):
        self.INPUT_CSV = input_csv

    def get_shares(self, row) -> int:
        """
        Get the number of shares considering the side
        :param row: The row
        :return: The number of shares - positive for sell orders, negative for buy orders
        """
        if row[Columns.SIDE] == self.SELL:
            return int(row[Columns.SHARES])
        else:
            return -1 * int(row[Columns.SHARES])

    @staticmethod
    def _symbol_df_to_trade_dfs(df: pd.DataFrame) -> list[pd.DataFrame]:
        """
        Split the symbol DataFrame to trade DataFrames
        :param df: A DataFrame for a certain symbol
        :return: A list of DataFrames, split to trade DataFrames based on the Position column
        """
        dfs = []
        temp_df = pd.DataFrame(columns=df.columns)  # Create an empty temp DataFrame

        for index, row in df.iterrows():
            temp_df = pd.concat([temp_df, row.to_frame().T], ignore_index=True)  # Add the current row to temp_df
            if row[Columns.POSITION] == 0:  # If the Position value is 0, it means the trade is closed
                dfs.append(temp_df.copy())  # Save the trade df to dfs
                temp_df = pd.DataFrame(columns=df.columns)  # Reset the temp DataFrame

        # Append remaining rows if last Position != 0
        if not temp_df.empty:
            dfs.append(temp_df)

        return dfs

    def _get_trade_dfs(self, df: pd.DataFrame) -> list[pd.DataFrame]:
        """
        Split the DataFrame to symbol DataFrames, and then to trade DataFrames
        :param df: The DataFrame
        :return: A list of trade DataFrames
        """
        symbol_dfs = df.groupby([Columns.SYMBOL], sort=False)  # Split to DataFrames based on the symbol
        trade_dfs = []
        for key, symbol_df in symbol_dfs:
            symbol_df[Columns.POSITION] = symbol_df.apply(self.get_shares, axis=1).cumsum()  # Update Position column
            trade_dfs.extend(self._symbol_df_to_trade_dfs(symbol_df))  # Save the symbol's trade dfs to a list
        return trade_dfs

    def _trade_df_to_form1325_rows(self, df: pd.DataFrame, rates: dict) -> list[dict]:
        """
        Transform the trade DataFrame to a list of rows in form 1325 format
        :param df: The trade DataFrame
        :param rates: The rates dictionary
        :return: A list of form 1325 dictionary rows
        """
        results = []

        # Calculate total commissions and fees
        commissions_and_fees = df[Columns.COMMISSION].astype(float) + df[Columns.SEC_FEE].astype(float) + \
            df[Columns.TAF_FEE].astype(float) + df[Columns.ECN_FEE].astype(float) + \
            df[Columns.ROUTING_FEE].astype(float) + df[Columns.NSCC_FEE].astype(float)

        # Create a copy of the Shares column, for changing the value during iteration & also keeping the original number
        df[Columns.SHARES] = df[Columns.SHARES].astype(int)
        df[Columns.QUANTITY] = df[Columns.SHARES]

        # Separate Buy and Sell transactions
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
                buy = buys[buys[Columns.QUANTITY] > 0].iloc[0]  # Find the oldest relevant buy order
                buy_index = buy.name
                buy_rate = rates.get(buy[Columns.DATETIME].strftime(Config.DATE_FORMAT), 0)
                sell_rate = rates.get(sell[Columns.DATETIME].strftime(Config.DATE_FORMAT), 0)

                # Determine the shares and price for this transaction
                if buy[Columns.QUANTITY] <= shares_to_sell:  # There are more or same amount of shares bought as to sell
                    shares_sold = buy[Columns.QUANTITY]
                    shares_to_sell -= buy[Columns.QUANTITY]
                    buys.at[buy_index, Columns.QUANTITY] = 0  # All of this buy order is used up
                else:  # There are more buy shares than sell shares, meaning the sell order is complete
                    shares_sold = shares_to_sell
                    buys.at[buy_index, Columns.QUANTITY] -= shares_to_sell
                    shares_to_sell = 0  #

                rate_change = 1 + ((sell_rate - buy_rate) / buy_rate)  # Calculate the currency rate change
                # Calculate the amounts, the profit and the loss
                amount_sell = sell[Columns.AMOUNT] * (shares_sold / sell[Columns.SHARES]) * sell_rate
                amount_buy = buy[Columns.AMOUNT] * (shares_sold / buy[Columns.SHARES]) * buy_rate
                amount_buy_adjusted = amount_buy * rate_change
                profit_loss = self._get_profit_loss(amount_buy, amount_buy_adjusted, amount_sell)

                # Create a dictionary row in form 1325 format. Use Hebrew column headers
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
    def _get_profit_loss(amount_buy: float, amount_buy_adjusted: float, amount_sell: float) -> float:
        """
        The profit and loss can be calculated based on the buy amount and also based on the adjusted buy amount, so
        according to Israeli law, the calculation should be the value closer to 0 (positive or negative) between both
        of the options. If one of them is positive and one is negative, there is 0 profit and 0 loss
        :param amount_buy: The amount bought
        :param amount_buy_adjusted: The amount bought, adjusted by the rate change
        :param amount_sell: The amount sold
        :return: A float representing the profit or loss
        """
        if math.copysign(1, amount_sell - amount_buy_adjusted) != math.copysign(1, amount_sell - amount_buy):
            return 0
        sign = math.copysign(1, amount_sell - amount_buy_adjusted)
        return sign * min(abs(amount_sell - amount_buy_adjusted), abs(amount_sell - amount_buy))

    def extract(self) -> pd.DataFrame:
        """
        Get a DataFrame with the Colmex Pro orders data. We don't use pd.read_csv() because of the "Notes" column, which
        is completely empty, and causes the DataFrame to be incorrectly read from the file
        :return: A DataFrame with the Colmex Pro orders data
        """
        with open(self.INPUT_CSV, newline="\r\n") as f:
            data = f.readlines()
            data = [  # Parse the rows
                list(map(lambda col: col.replace('"', "").rstrip(" "), row.rstrip(",\r\n").split(",")))
                for row in data if row.strip()
            ]
        df = pd.DataFrame(data[1:], columns=data[0])
        return df

    def transform(self, df: pd.DataFrame, rates: dict) -> pd.DataFrame:
        """
        Transform the Colmex Pro orders DataFrame to form 1325 DataFrame
        :param df: The Colmex Pro orders DataFrame
        :param rates: The rates dictionary
        :return: A DataFrame with rows in form 1325 format
        """
        # Create a DateTime column and sort by it, then by symbol and then by price
        fmt = f"{Config.COLMEX_PRO_MTS_DATE_FORMAT} {Config.TIME_FORMAT}"
        df[Columns.DATETIME] = pd.to_datetime(df[Columns.TRADE_DATE] + " " + df[Columns.EXEC_TIME], format=fmt)
        df = df.sort_values(by=[Columns.DATETIME, Columns.SYMBOL, Columns.PRICE])

        trade_dfs = self._get_trade_dfs(df)  # Get a list of trade DataFrames
        form1325_rows = []
        for trade_df in trade_dfs:
            trade_1325_rows = self._trade_df_to_form1325_rows(trade_df, rates)  # Get the form 1325 rows
            form1325_rows.extend(trade_1325_rows)

        transformed_df = pd.DataFrame(form1325_rows)

        # Add a Row Number column and move it to the beginning
        transformed_df[Columns.ROW_NUMBER] = transformed_df.reset_index().index + 1
        transformed_df.insert(0, Columns.ROW_NUMBER, transformed_df.pop(Columns.ROW_NUMBER))

        # Reformat date columns
        for column in Heb.BUY_DATE, Heb.SELL_DATE:
            transformed_df[column] = pd.to_datetime(transformed_df[column]).\
                dt.strftime(Config.COLMEX_PRO_LOG_DATE_FORMAT)

        return transformed_df

    @staticmethod
    def _get_year(df: pd.DataFrame):
        years = set(pd.to_datetime(df[Columns.TRADE_DATE]).dt.year)
        if len(years) == 1:
            return years.pop()
        raise Exception("Error: Multiple years found in input file. Can only support files with orders from one year")

    def run(self) -> tuple[pd.DataFrame, int]:
        """
        Get a form 1325 rows DataFrame from a csv with Colmex Pro orders data
        :return: A DataFrame with the form 1325 rows data
        """
        df = self.extract()  # Get a Dataframe with the Colmex Pro orders data
        if df is not None:
            year = self._get_year(df)
            rates = BankOfIsraelRates.get_rates(year, self.COIN)  # Get the currency rates
            transformed_df = self.transform(df, rates)  # Transform the Dataframe to a Dataframe in form 1325 format
            return transformed_df, year
