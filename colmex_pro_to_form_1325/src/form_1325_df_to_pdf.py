import os
import uuid

import pandas as pd
import pdfkit
import pypdf

from form_1325_hebrew_text import Form1325HebrewText as Heb


class Form1325DFToPDF:
    def __init__(self, year: int, name: str, file_number: str, asset_abroad: bool, df: pd.DataFrame, output_path: str):
        self.YEAR = year
        self.NAME = name
        self.FILE_NUMBER = file_number
        self.ASSET_ABROAD = asset_abroad
        self.DF = df
        self.OUTPUT_PATH = output_path

    @staticmethod
    def round_number(num: float, decimals: int) -> float:
        """
        Round a float based on the number of decimals
        :param num: The number to round
        :param decimals: The number of decimals
        :return: The rounded number - int if decimals is 0, float otherwise
        """
        if isinstance(num, float):
            num = round(num, decimals)
            if decimals == 0:
                num = int(num)
        return num

    @staticmethod
    def _add_thousands_separator(num: float) -> str:
        """
        Get a string representing a number with thousands separator
        :param num: The number
        :return: The number as a string with thousands separator
        """
        return "" if num == "" else f"{num:,}"

    def parse_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse the DataFrame columns for a good-looking PDF representation
        :param df: The DataFrame
        :return: The parsed DataFrame
        """
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
        """
        Create an HTML tag string
        :param tag_name: The tag name
        :param text: The text (or HTML) to put inside the tag
        :param cls: The tag's class name
        :return: A string with the HTML tag
        """
        cls_str = '' if cls is None else f' class="{cls}"'
        return fr"<{tag_name}{cls_str}>{text}</{tag_name}>"

    def _p_tag(self, text: str, cls: str = None) -> str:
        """
        Create an HTML p tag
        :param text: The text
        :param cls: The tag's class
        :return: The HTML p tag string
        """
        return self._tag("p", text, cls)

    def _b_tag(self, text: str, cls: str = None) -> str:
        """
        Create an HTML b tag
        :param text: The text
        :param cls: The tag's class
        :return: The HTML b tag string
        """
        return self._tag("b", text, cls)

    def _span_tag(self, text: str, cls: str = None) -> str:
        """
        Create an HTML span tag
        :param text: The text
        :param cls: The tag's class
        :return: The HTML span tag string
        """
        return self._tag("span", text, cls)

    def _div_tag(self, text: str, cls: str = None) -> str:
        """
        Create an HTML div tag
        :param text: The text
        :param cls: The tag's class
        :return: The HTML div tag string
        """
        return self._tag("div", text, cls)

    def _get_asset_abroad_html(self) -> str:
        """
        Create an HTML string for the asset abroad data
        :return: The HTML string
        """
        yes_span = self._span_tag(self._p_tag("X" if self.ASSET_ABROAD else ""), "checkbox")
        no_span = self._span_tag(self._p_tag("X" if not self.ASSET_ABROAD else ""), "checkbox")
        html = self._div_tag(
            f"{yes_span}&nbsp;{self._p_tag(Heb.YES)}&nbsp;&nbsp;&nbsp;&nbsp;{no_span}&nbsp;{self._p_tag(Heb.NO)}",
            "checkbox-container"
        )
        return html

    @staticmethod
    def _get_html_table(
            cls: str, data: list[list] = None, df: pd.DataFrame = None, columns: list = None, header: bool = False
    ) -> str:
        """
        Create an HTML string for a table. Pass either data (with columns) or df (without columns).
        :param cls: The table's HTML class name
        :param data: The data
        :param df: The DataFrame
        :param columns: The columns (relevant only when passing data)
        :param header: Should put the header in the html or not
        :return: The HTML table string
        """
        if df is None:
            df = pd.DataFrame(data, columns=columns)
        return df.to_html(index=False, escape=False, classes=[cls], header=header)

    def _personal_details_table(self) -> str:
        """
        Create an HTML table for the personal details table
        :return: The HTML table string
        """
        data = [[self.NAME, self.FILE_NUMBER, self._get_asset_abroad_html()]]
        cls = "personal_details_table"
        columns = [Heb.NAME, Heb.FILE_NUMBER, Heb.ASSET_ABROAD]
        return self._get_html_table(cls, data=data, columns=columns, header=True)

    def _data_table(self, df: pd.DataFrame) -> str:
        """
        Create and HTML table for the data table
        :param df: The DataFrame containing the data
        :return: The HTML table string
        """
        cls = "data_table"
        return self._get_html_table(cls, df=df, header=True)

    def _total_profit_loss_table(self, total_profit: str, total_loss: str) -> str:
        """
        Create an HTML table for the total profit & loss table
        :return: The HTML table string
        """
        data = [[
            f"{self._b_tag(Heb.TOTAL_PROFIT_LOSS)}<br/>{self._p_tag(Heb.TOTAL_PROFIT_LOSS_COMMENT)}",
            self._b_tag(total_profit), self._b_tag(total_loss)
        ]]
        cls = "total_profit_loss_table"
        return self._get_html_table(cls, data=data)

    def _total_sales_table(self, total_sales: str) -> str:
        """
        Create an HTML table for the total sales table
        :return: The HTML table string
        """
        data = [[
            f"{self._b_tag(Heb.TOTAL_SALES)}<br/>{self._p_tag(Heb.TOTAL_SALES_COMMENT)}",
            self._b_tag(total_sales)
        ]]
        cls = "total_sales_table"
        return self._get_html_table(cls, data=data)

    def _signatures_table(self) -> str:
        """
        Create an HTML table for the signatures table
        :return: The HTML table string
        """
        data = [[self._p_tag(Heb.SIGNATURE_1), self._p_tag(Heb.SIGNATURE_2)]]
        cls = "signatures_table"
        return self._get_html_table(cls, data=data)

    @staticmethod
    def get_df_column_sum(df: pd.DataFrame, column_name: str) -> int:
        """
        Get a total sum of a column from the DataFrame
        :param df: The DataFrame
        :param column_name: The columns name
        :return: An integer with the sum total of the column values
        """
        result = round(pd.to_numeric(df[column_name], errors="coerce").sum())
        return result

    def _df_to_html(self) -> str:
        """
        Get the whole document's HTML string
        :return: The HTML document string
        """
        # Calculate some column totals
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
    def merge_pdfs(pdf_list: list, output_path: str):
        """
        Merge multiple PDF files
        :param pdf_list: A list with paths to PDF files
        :param output_path: The output path of the merged PDF file
        """
        # pdf_merger = PyPDF2.PdfMerger()
        pdf_writer = pypdf.PdfWriter()

        for pdf in pdf_list:
            pdf_writer.append(pdf)

        with open(output_path, "wb") as output_file:
            pdf_writer.write(output_file)

    def _html_to_pdf(self, html: str):
        """
        Write the document's HTML string to a PDF file
        :param html: The HTML string
        """
        options = {
            'encoding': 'UTF-8',
            'load-error-handling': 'ignore',
            'page-size': 'A4',
            'orientation': 'Landscape',
            'footer-right': '[page] of [topage]',
            "footer-font-size": "8",
            "footer-font-name": "Trebuchet",
            "header-left": Heb.LEFT_HEADER.replace("[YEAR]", f"{self.YEAR}"),
            "header-font-size": "8",
            "header-font-name": "Trebuchet",
            "header-spacing": 6,
            "footer-spacing": 1,
        }
        # Create the temp PDF file with a uuid as its name
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        temp_pdf = f"{parent_dir}/temp/{uuid.uuid4()}.pdf"
        # Generate the temp PDF file with a css file for a good-looking output
        if pdfkit.from_string(html, temp_pdf, options=options, css=f"{parent_dir}/resources/form_1325.css", verbose=True):
            # Add the explanations PDF page to the temp PDF file
            explanations_pdf = f"{parent_dir}/resources/1325_explanations.pdf"
            self.merge_pdfs([temp_pdf, explanations_pdf], self.OUTPUT_PATH)
            os.remove(temp_pdf)  # Remove the temp file

    def run(self):
        """
        Convert the object's DataFrame (self.DF) to HTML, and then from HTML to PDF
        """
        html = self._df_to_html()
        self._html_to_pdf(html)
