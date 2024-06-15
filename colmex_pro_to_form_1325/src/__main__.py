import argparse
import os.path
import sys

sys.path.append(os.path.dirname(__file__))

from config import Config
from form_1325_generator import Form1325CSVGenerator, Form1325PDFGenerator
from logger import logger
from utilities import Utilities


class Main:
    EXTENSION_TO_CLASS_MAP = {Config.CSV: Form1325CSVGenerator, Config.PDF: Form1325PDFGenerator}

    @staticmethod
    def _parse_args():
        """
        Parse the command-line arguments
        :return: A argparse.Namespace object
        """
        parser = argparse.ArgumentParser(description="Example class with command-line arguments")

        parser.add_argument("input_file", type=str, help="The CSV input file path")
        parser.add_argument("output_file", type=str, help="The output file path")
        parser.add_argument("--name", type=str, help="The name (for PDF output only)")
        parser.add_argument("--file_number", type=str, help="The file number (for PDF output only)")
        parser.add_argument("--asset_abroad", type=str, help="Whether the asset is abroad (for PDF output only)")

        return parser.parse_args()

    @staticmethod
    def _validate_input_file(input_file: str):
        """
        Validate the input file: Check if it exists and if its file extension is CSV
        """
        if not Utilities.file_exists(input_file):
            raise Exception(f"Input file not found: {input_file}")
        input_file_extension = Utilities.get_file_extension(input_file)
        if input_file_extension != Config.CSV:
            raise Exception(f"Unsupported input file format: {input_file_extension}")

    @staticmethod
    def _validate_args(args: argparse.Namespace, output_file_extension: str):
        """
         Validate the command-line arguments: Make sure that when using PDF output file, all arguments are required,
         and warn when the optional arguments are passed, but not required
        """
        if output_file_extension == Config.PDF:
            if args.name is None or args.file_number is None or args.asset_abroad is None:
                raise Exception("--name, --file_number, --asset_abroad are required when using PDF output file")
        else:
            if not (args.name is None and args.file_number is None and args.asset_abroad is None):
                logger.warning("--name, --file_number, --asset_abroad are ignored when not using PDF output file")

    @staticmethod
    def _validate_asset_abroad(asset_abroad: str):
        """
        Validate the Asset Abroad: Can be True or False only
        """
        asset_abroad = asset_abroad.capitalize()
        if asset_abroad not in ("True", "False"):
            raise Exception("Valid values for asset abroad are only 'True', 'False'")

    @staticmethod
    def _validate(args: argparse.Namespace, output_file_extension: str):
        """
        Make some validations
        """
        Main._validate_input_file(args.input_file)
        Main._validate_args(args, output_file_extension)
        if output_file_extension == Config.PDF:
            Main._validate_asset_abroad(args.asset_abroad)

    @staticmethod
    def _get_generator(output_file_extension: str) -> type:
        """
        Get the correct generator class according to the output file extension
        """
        cls = Main.EXTENSION_TO_CLASS_MAP.get(output_file_extension)
        if cls is None:
            raise Exception(f"Unsupported output file format: {output_file_extension}")
        return cls

    @staticmethod
    def run():
        """
        Run the app
        """
        try:
            args = Main._parse_args()
            output_file_extension = Utilities.get_file_extension(args.output_file)
            Main._validate(args, output_file_extension)
            cls = Main._get_generator(output_file_extension)
            cls(**args.__dict__).run()
            if Utilities.file_exists(args.output_file):
                logger.info(f"Output file ready at: {args.output_file}")
        except Exception as e:
            logger.exception(e)


if __name__ == '__main__':
    Main.run()
