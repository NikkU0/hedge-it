import sys
from argparse import ArgumentParser

from hedge_it.commons.constants import LOG_LEVEL, POLYGON_API_KEY, STOCK_LIMIT


class CustomArgumentParser(ArgumentParser):
    """
    Custom ArgumentParser to throw helpful parsing error
    """

    def error(self, message):
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)


class CliArgParser(object):
    def __init__(self):
        self._base_parser = CustomArgumentParser(
            description="Hedge It argument  Base parser"
        )

        self._common_parser = CustomArgumentParser(
            description="Commons arguments", add_help=False
        )
        self._set_common_arguments()

    def _set_common_arguments(self):
        self._common_parser.add_argument(
            "-l",
            f"--{LOG_LEVEL}",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            required=False,
            help="Logging level for the Application.",
        )
        self._common_parser.add_argument(
            "-pak", f"--{POLYGON_API_KEY}", required=True, help="Polygon API Key."
        )
        self._common_parser.add_argument(
            "-sl", f"--{STOCK_LIMIT}", required=False,default=2000, help="Stock Limit, Limit to avoid rate limiting of yfin."
        )

    def _set_common_local_args(self):
        pass

    @property
    def base_parser(self):
        return self._base_parser

    @property
    def common_parser(self):
        return self._common_parser
