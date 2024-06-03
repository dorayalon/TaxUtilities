import os
import uuid

from form_1325_hebrew_text import Form1325HebrewText as Heb
import pandas as pd
import pdfkit
import PyPDF2


class Form1325DFToPDF:
    def __init__(self, name: str, file_number: str, asset_abroad: bool, df: pd.DataFrame, output_path: str):
        self.NAME = name
        self.FILE_NUMBER = file_number
        self.ASSET_ABROAD = asset_abroad
        self.DF = df
        self.OUTPUT_PATH = output_path

    @staticmethod
    def round_number(num: float, decimals: int):
        if isinstance(num, float):
            num = round(num, decimals)
            if decimals == 0:
                num = int(num)
        return num

    @staticmethod
    def _add_thousands_separator(num: float) -> str:
        return "" if num == "" else f"{num:,}"

    def parse_df(self, df: pd.DataFrame) -> pd.DataFrame:
        # Round some float column values
        columns_to_round = {
            0: [Heb.BUY_AMOUNT, Heb.BUY_AMOUNT_ADJUSTED, Heb.SELL_AMOUNT, Heb.PROFIT, Heb.LOSS],
            2: [Heb.RATE_CHANGE]
        }
        for num_decimals, columns in columns_to_round.items():
            for column in columns:
                df[column] = df[column].apply(lambda x: self.round_number(x, num_decimals))

        # Add thousands separators
        for column in Heb.ROW_NUMBER, Heb.SHARES, Heb.BUY_AMOUNT, Heb.BUY_AMOUNT_ADJUSTED, Heb.SELL_AMOUNT, \
                Heb.PROFIT, Heb.LOSS:
            df[column] = df[column].apply(self._add_thousands_separator)

        # Add sub-header as 1st row
        sub_header = {col: Heb.SUB_HEADER[i] for i, col in enumerate(df.columns)}
        df = pd.concat([df.iloc[:0], pd.DataFrame([sub_header]), df.iloc[0:]]).reset_index(drop=True)

        return df

    @staticmethod
    def _tag(tag_name: str, text: str, cls: str = None) -> str:
        cls_str = '' if cls is None else f' class="{cls}"'
        return fr"<{tag_name}{cls_str}>{text}</{tag_name}>"

    def _p_tag(self, text: str, cls: str = None) -> str:
        return self._tag("p", text, cls)

    def _b_tag(self, text: str, cls: str = None) -> str:
        return self._tag("b", text, cls)

    def _span_tag(self, text: str, cls: str = None) -> str:
        return self._tag("span", text, cls)

    def _div_tag(self, text: str, cls: str = None) -> str:
        return self._tag("div", text, cls)

    def _get_asset_abroad_html(self):
        yes_span = self._span_tag(self._p_tag("X" if self.ASSET_ABROAD else ""), "checkbox")
        no_span = self._span_tag(self._p_tag("X" if not self.ASSET_ABROAD else ""), "checkbox")
        html = self._div_tag(
            f"{yes_span}&nbsp;{self._p_tag(Heb.YES)}&nbsp;&nbsp;&nbsp;&nbsp;{no_span}&nbsp;{self._p_tag(Heb.NO)}",
            "checkbox-container"
        )
        return html

    @staticmethod
    def _get_html_table(cls: str, data: list[list] = None, df: pd.DataFrame = None, columns: list = None, header=False):
        if df is None:
            df = pd.DataFrame(data, columns=columns)
        return df.to_html(index=False, escape=False, classes=[cls], header=header)

    def _personal_details_table(self) -> str:
        data = [[self.NAME, self.FILE_NUMBER, self._get_asset_abroad_html()]]
        cls = "personal_details_table"
        columns = [Heb.NAME, Heb.FILE_NUMBER, Heb.ASSET_ABROAD]
        return self._get_html_table(cls, data=data, columns=columns, header=True)

    def _data_table(self, df: pd.DataFrame):
        cls = "data_table"
        return self._get_html_table(cls, df=df, header=True)

    def _total_profit_loss_table(self, total_profit: str, total_loss: str) -> str:
        data = [[
            f"{self._b_tag(Heb.TOTAL_PROFIT_LOSS)}<br/>{self._p_tag(Heb.TOTAL_PROFIT_LOSS_COMMENT)}",
            self._b_tag(total_profit), self._b_tag(total_loss)
        ]]
        cls = "total_profit_loss_table"
        return self._get_html_table(cls, data=data)

    def _total_sales_table(self, total_sales: str) -> str:
        data = [[
            f"{self._b_tag(Heb.TOTAL_SALES)}<br/>{self._p_tag(Heb.TOTAL_SALES_COMMENT)}",
            self._b_tag(total_sales)
        ]]
        cls = "total_sales_table"
        return self._get_html_table(cls, data=data)

    def _signatures_table(self) -> str:
        data = [[self._p_tag(Heb.SIGNATURE_1), self._p_tag(Heb.SIGNATURE_2)]]
        cls = "signatures_table"
        return self._get_html_table(cls, data=data)

    @staticmethod
    def get_df_column_sum(df: pd.DataFrame, column_name: str) -> int:
        result = round(pd.to_numeric(df[column_name], errors="coerce").sum())
        return result

    def _df_to_html(self) -> str:
        total_profit = self._add_thousands_separator(self.get_df_column_sum(self.DF, Heb.PROFIT))
        total_loss = self._add_thousands_separator(self.get_df_column_sum(self.DF, Heb.LOSS))
        total_sales = self._add_thousands_separator(self.get_df_column_sum(self.DF, Heb.SELL_AMOUNT))

        return f"""<!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
            </head>
            <body>
                <br/><br/>
                <h3>{Heb.TITLE_1}</h3>
                <h1>{Heb.cite(Heb.TITLE_2)}</h1>
                <p class='title3'>{Heb.cite(Heb.TITLE_3)}</p>
                {self._personal_details_table()}
                <br/>
                {self._data_table(self.parse_df(self.DF))}
                <p class='comment'>{Heb.cite(Heb.COMMENT)}</p>
                {self._total_profit_loss_table(total_profit, total_loss)}
                <br/>
                {self._total_sales_table(total_sales)}
                <br/><br/><br/><br/><br/><br/>
                {self._signatures_table()}
            </body>
            </html>
            """

    @staticmethod
    def merge_pdfs(pdf_list, output_path):
        pdf_merger = PyPDF2.PdfMerger()

        for pdf in pdf_list:
            pdf_merger.append(pdf)

        with open(output_path, "wb") as output_file:
            pdf_merger.write(output_file)

    def _html_to_pdf(self, html: str):
        options = {
            'encoding': 'UTF-8',
            'load-error-handling': 'ignore',
            'page-size': 'A4',
            'orientation': 'Landscape',
            'footer-right': '[page] of [topage]',
            "footer-font-size": "8",
            "footer-font-name": "Trebuchet",
            "header-left": Heb.LEFT_HEADER,
            "header-font-size": "8",
            "header-font-name": "Trebuchet",
            "header-spacing": 6,
            "footer-spacing": 1,
        }
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        temp_pdf = f"{parent_dir}/temp/{uuid.uuid4()}.pdf"
        if pdfkit.from_string(html, temp_pdf, options=options, css=f"{parent_dir}/resources/form_1325.css"):
            explanations_pdf = f"{parent_dir}/resources/1325_explanations.pdf"
            self.merge_pdfs([temp_pdf, explanations_pdf], self.OUTPUT_PATH)
            os.remove(temp_pdf)

    def run(self):
        html = self._df_to_html()
        self._html_to_pdf(html)
