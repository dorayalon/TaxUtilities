import os
import time

import pandas as pd
import pytest
from colmex_pro_to_form_1325.src.__main__ import Main
from colmex_pro_to_form_1325.src.form_1325_hebrew_text import Form1325HebrewText as Heb
from colmex_pro_to_form_1325.src.logger import logger
import logging
from itertools import product


@pytest.fixture()
def content():
    content = \
        """Account,Trade Date,Currency,Account Type,Side,Symbol,Shares,Price,Exec Time,Commission,SEC Fee,TAF Fee,\
ECN Fee,Routing Fee,NSCC Fee,Clr Type,Clr Broker,Note
COLH95300,04/17/2023,USD,2,S,MARA,400,11.1518,9:42:42,0,0,0,0,0,0,Stoc,Stocks2,
COLH95300,04/17/2023,USD,2,B,MARA,400,11.3687,10:11:03,0,0,0,0,0,0,Stoc,Stocks2,
COLH95300,04/17/2023,USD,2,S,BTU,400,26.7823,10:29:52,0,0,0,0,0,0,Stoc,Stocks1,
COLH95300,04/17/2023,USD,2,B,BTU,300,26.5265,10:38:42,0,0,0,0,0,0,Stoc,Stocks1,
COLH95300,04/17/2023,USD,2,B,BTU,100,26.4888,10:46:01,0,0,0,0,0,0,Stoc,Stocks1,"""
    return content


@pytest.fixture(scope="function")
def tmpdir_func(tmpdir):
    yield tmpdir

    files_to_remove = ["input.csv", "input.c", "input", "output.csv", "output.pdf"]
    for filename in files_to_remove:
        file_path = tmpdir.join(filename)
        if file_path.check():
            logger.info(f"Deleting {file_path}")
            os.remove(str(file_path))


@pytest.fixture
def create_file(tmpdir_func):
    def _create_file(file_name, content):
        file_path = tmpdir_func.join(file_name)
        file_path.write(content)
        yield str(file_path)
    return _create_file


@pytest.fixture
def input_csv(create_file, content):
    yield from create_file("input.csv", content)


@pytest.fixture
def input_c(create_file, content):
    yield from create_file("input.c", content)


@pytest.fixture
def input_file(create_file, content):
    yield from create_file("input", content)


@pytest.fixture
def input_non_existing(create_file):
    yield "input"


def test_parse_csv_to_csv(input_csv, tmpdir_func, monkeypatch, caplog):
    output_file = tmpdir_func.join("output.csv")

    # Simulate command-line arguments
    monkeypatch.setattr('sys.argv', ['app.py', input_csv, str(output_file)])

    assert Main.run() is True

    # Verify output CSV
    assert os.path.exists(output_file)
    output_df = pd.read_csv(output_file)
    assert list(output_df.columns) == [
        "Unnamed: 0", Heb.SYMBOL, Heb.BOUGHT_DURING_PRE_MARKET, Heb.SHARES, Heb.BUY_DATE, Heb.BUY_AMOUNT,
        Heb.RATE_CHANGE, Heb.BUY_AMOUNT_ADJUSTED, Heb.SELL_DATE, Heb.SELL_AMOUNT, Heb.PROFIT, Heb.LOSS
    ]
    assert len(output_df) == 3


def test_parse_csv_to_pdf(input_csv, tmpdir_func, monkeypatch, caplog):
    output_file = tmpdir_func.join("output.pdf")

    # Simulate command-line arguments
    monkeypatch.setattr('sys.argv', [
        'app.py', input_csv, str(output_file),
        '--name', 'ישראל ישראלי',
        '--file_number', '123456789',
        '--asset_abroad', 'True'
    ])

    logger.info(f"Output file in: {output_file}")
    result = Main.run()
    time.sleep(3)
    assert result is True
    assert os.path.exists(output_file)


@pytest.mark.parametrize("output_file", [("out.invalid"), ("out")])
def test_invalid_output_file_extension(input_csv, tmpdir_func, monkeypatch, caplog, output_file):
    output_file = tmpdir_func.join(output_file)

    # Simulate command-line arguments with an invalid format
    monkeypatch.setattr('sys.argv', ['app.py', input_csv, str(output_file)])

    with caplog.at_level(logging.ERROR):
        assert Main.run() is False and (
                "Unsupported output file extension" in caplog.text or
                "Failed to get the file extension" in caplog.text
        )


@pytest.mark.parametrize("name, file_number, asset_abroad", [("ישראל ישראלי", "123456789", "True")])
def test_pdf_missing_params_combinations(tmpdir_func, monkeypatch, caplog, input_csv, name, file_number, asset_abroad):
    parameter_combinations = product([name, None], [file_number, None], [asset_abroad, None])
    output_file = tmpdir_func.join("output.pdf")

    parameter_combinations = list(filter(lambda params: any(p is None for p in params), parameter_combinations))
    for name, file_number, asset_abroad in parameter_combinations:
        logger.info(f"Current params: {name}, {file_number}, {asset_abroad}")
        args = ['app.py', input_csv, str(output_file)]
        if name is not None:
            args.extend(['--name', name])
        if file_number is not None:
            args.extend(['--file_number', file_number])
        if asset_abroad is not None:
            args.extend(['--asset_abroad', asset_abroad])
        # Simulate command-line arguments with an invalid format
        monkeypatch.setattr('sys.argv', args)

        with caplog.at_level(logging.ERROR):
            assert Main.run() is False \
                   and "--name, --file_number, --asset_abroad are required when using PDF output file" in caplog.text


@pytest.mark.parametrize("name, file_number, asset_abroad", [("ישראל ישראלי", "123456789", "True")])
def test_csv_missing_params_combinations(tmpdir_func, monkeypatch, caplog, input_csv, name, file_number, asset_abroad):
    parameter_combinations = product([name, None], [file_number, None], [asset_abroad, None])
    output_file = tmpdir_func.join("output.csv")

    parameter_combinations = list(filter(lambda params: any(p is not None for p in params), parameter_combinations))
    for name, file_number, asset_abroad in parameter_combinations:
        logger.info(f"Current params: {name}, {file_number}, {asset_abroad}")
        args = ['app.py', input_csv, str(output_file)]
        if name is not None:
            args.extend(['--name', name])
        if file_number is not None:
            args.extend(['--file_number', file_number])
        if asset_abroad is not None:
            args.extend(['--asset_abroad', asset_abroad])
        # Simulate command-line arguments with an invalid format
        monkeypatch.setattr('sys.argv', args)

        with caplog.at_level(logging.WARNING):
            assert Main.run() is True \
                   and "--name, --file_number, --asset_abroad are ignored when not using PDF output file" in caplog.text


@pytest.mark.parametrize("input_f", [("input_non_existing"), ("input_c"), ("input_file")])
def test_unsupported_input_file_extension(tmpdir_func, caplog, monkeypatch, input_f, request):
    fixture_value = request.getfixturevalue(input_f)
    output_file = tmpdir_func.join("output.csv")

    # Simulate command-line arguments with an invalid format
    monkeypatch.setattr('sys.argv', ['app.py', fixture_value, str(output_file)])
    with caplog.at_level(logging.ERROR):
        assert Main.run() is False and (
                "Input file not found" in caplog.text or
                "Unsupported input file extension" in caplog.text or
                "Failed to get the file extension" in caplog.text
        )


@pytest.mark.parametrize("asset_abroad", [("rue"), ("alse"), ("fff"), ("1234")])
def test_bad_asset_abroad(tmpdir_func, monkeypatch, caplog, input_csv, asset_abroad):
    output_file = tmpdir_func.join("output.pdf")

    # Simulate command-line arguments
    monkeypatch.setattr('sys.argv', [
        'app.py', input_csv, str(output_file),
        '--name', 'ישראל ישראלי',
        '--file_number', '123456789',
        '--asset_abroad', asset_abroad
    ])

    with caplog.at_level(logging.ERROR):
        assert Main.run() is False and "Valid values for asset abroad are only 'True', 'False'" in caplog.text
