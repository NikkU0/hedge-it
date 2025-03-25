from dataclasses import dataclass


@dataclass
class CliArguments:
    """
    Class to hold the CLI arguments.
    """

    log_level: str
    polygon_api_key: str
    stock_limit: int

    def __init__(self, log_level: str, polygon_api_key: str,stock_limit:int):
        self.log_level = log_level
        self.polygon_api_key = polygon_api_key
        self.stock_limit = stock_limit
