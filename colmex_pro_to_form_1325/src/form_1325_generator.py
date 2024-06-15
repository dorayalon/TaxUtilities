import pandas as pd

from colmex_pro_orders_csv_headers import ColmexProOrdersCSVColumns as Columns
from colmex_pro_orders_to_form_1325_df import ColmexProOrdersToForm1325DF
from form_1325_df_to_pdf import Form1325DFToPDF


class _Form1325Generator:
    def __init__(self, input_file: str, output_file: str, **kwargs):
        self.INPUT_FILE = input_file
        self.OUTPUT_FILE = output_file

    def _extract(self) -> pd.DataFrame:
        """
        Get a DataFrame with the Colmex Pro orders data
        :return: A DataFrame with the Colmex Pro orders data
        """
        df = pd.read_csv(self.INPUT_FILE, index_col=False)
        df = df.dropna(how='all')
        return df

    @staticmethod
    def _get_year(df: pd.DataFrame) -> int:
        """
        Get the year from the Colmex Pro orders DataFrame
        """
        years = set(pd.to_datetime(df[Columns.TRADE_DATE]).dt.year)
        if len(years) == 1:
            return years.pop()
        raise Exception("Error: Multiple years found in input file. Can only support files with orders from one year")

    @staticmethod
    def _transform(df: pd.DataFrame, year: int) -> pd.DataFrame:
        """
        Transform the Colmex Pro orders DataFrame to Form 1325 rows DataFrame
        :return: A pd.DataFrame object
        """
        transformed_df = ColmexProOrdersToForm1325DF.run(df, year)
        return transformed_df

    def _load(self, df: pd.DataFrame, **kwargs):
        """
        Load the DataFrame. This is an abstract method, that should be overridden by a subclass
        """
        pass

    def run(self):
        """
        Run the generator
        """
        df = self._extract()
        year = self._get_year(df)
        transformed_df = self._transform(df, year)
        if transformed_df is not None:
            self._load(transformed_df, year=year)
        else:
            raise Exception(f"Failed to transform the input file")


class Form1325CSVGenerator(_Form1325Generator):
    def __init__(self, input_file: str, output_file: str, **kwargs):
        super().__init__(input_file, output_file, **kwargs)

    def _load(self, df: pd.DataFrame, **kwargs):
        """
        Load the DataFrame to a CSV file
        """
        df.to_csv(self.OUTPUT_FILE, index=False, encoding='utf-8-sig')


class Form1325PDFGenerator(_Form1325Generator):
    def __init__(self, input_file: str, output_file: str, name: str, file_number: str, asset_abroad: str, **kwargs):
        super().__init__(input_file, output_file, **kwargs)
        self.NAME = name
        self.FILE_NUMER = file_number
        self.ASSET_ABROAD = eval(asset_abroad.capitalize())

    def _load(self, df: pd.DataFrame, **kwargs):
        """
        Load the DataFrame to a PDF file
        """
        year = kwargs.get("year")
        Form1325DFToPDF(year, self.NAME, self.FILE_NUMER, self.ASSET_ABROAD, df, self.OUTPUT_FILE).run()
