import os.path
import sys

sys.path.append(os.path.dirname(__file__))

from colmex_pro_orders_to_form_1325_df import ColmexProOrdersToForm1325DF
from form_1325_df_to_pdf import Form1325DFToPDF


class Form1325Generator:
    CSV_FORMAT = ".csv"
    PDF_FORMAT = ".pdf"

    def __init__(self, name: str, file_number: str, asset_abroad: str, year: str, input_file: str, output_file: str):
        self.NAME = name
        self.FILE_NUMER = file_number
        self.ASSET_ABROAD = asset_abroad
        self.YEAR = int(year)
        self.INPUT_FILE = input_file
        self.OUTPUT_FILE = output_file
        self.OUTPUT_FORMAT = os.path.splitext(self.OUTPUT_FILE)[1]

    def _validate_asset_abroad(self):
        asset_abroad = self.ASSET_ABROAD.capitalize()
        if asset_abroad not in ("True", "False"):
            raise Exception("Valid values for asset abroad are only 'True', 'False'")

    def _validate_output(self):
        if self.OUTPUT_FORMAT.lower() not in (self.CSV_FORMAT, self.PDF_FORMAT):
            raise Exception(f"Unsupported format: {self.OUTPUT_FORMAT}")

    def run(self):
        self._validate_asset_abroad()
        self._validate_output()

        df = ColmexProOrdersToForm1325DF(self.YEAR, self.INPUT_FILE).run()
        if self.OUTPUT_FORMAT == self.CSV_FORMAT:
            df.to_csv(self.OUTPUT_FILE, index=False, encoding='utf-8-sig')
            print(f"File ready at: {self.OUTPUT_FILE}")
        elif self.OUTPUT_FORMAT == self.PDF_FORMAT:
            Form1325DFToPDF(self.NAME, self.FILE_NUMER, eval(self.ASSET_ABROAD), df, self.OUTPUT_FILE).run()
            print(f"File ready at: {self.OUTPUT_FILE}")


if __name__ == '__main__':
    if len(sys.argv) == 7:
        g = Form1325Generator(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
        g.run()  # Run generator
