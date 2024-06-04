# TaxUtilities
 
This repository contains `python` utility tools for assisting with tax-related calculations and form preparations:

## Converting Colmex Pro's orders report to form 1325
This tool automates the generation of tax form 1325 from Colmex Pro's orders CSV.

---

### Description
This tool parses the CSV report provided by Colmex Pro, and can generate either a form 1325 as a CSV file or a PDF file.

The tool parses each stock's orders into closed trades, then parses those trades into form 1325 rows, in addition to 
calculating the relevant currency rates (currently only supports USD), as described 
[here](https://fintranslator.com/israel-tax-return-example-2019/).

---

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`

---

### Usage
In order to generate the form, there are several arguments you need to pass:
1. Your full name
2. Your tax authorities file number (usually your ID number)
3. Whether the assets you are trading are abroad (Valid values are `True` and `False`)
4. The year for which you would like to generate the form
5. The path to your orders `csv` file from Colmex Pro 
6. The desired path of the output file (The tool currently supports `csv` and `pdf` file extensions only)

In order to run the tool you can use this command from your terminal: \
`python3 -m colmex_pro_to_form_1325.src [NAME] [FILE NUMBER] [ASSET ABROAD] [YEAR] [INPUT FILE] [OUTPUT FILE]`

For example: \
`python -m colmex_pro_to_form_1325.src 123456789 "ישראל ישראלי" True 2023 "/path/to/orders/file.csv" 
"/path/to/output/form_1325.pdf"`

---

### DISCLAIMER
This tool is provided for informational purposes only and is NOT a substitute for professional tax advice or services, 
nor does it provide legal, financial, or tax advice of any kind. 
The author of this tool is NOT a tax professional, so users should consult an accountant or a professional tax advisor 
to ensure the accuracy of tax information.

The author is not responsible for any errors or omissions, or for any losses or damages incurred as a result of using 
this tool.

By using this tool, you acknowledge and accept these terms.