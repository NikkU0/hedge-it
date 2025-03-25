import ast
import os


from hedge_it.commons import CliArguments, CustomLogger, get_logger
from hedge_it.dashboards.index_board import build_data, plot

log = get_logger()


def parse_args():
    """
    Parse the command line arguments
    :return: CliArguments
    """
    cli_args_str = os.environ.get("HEDGE_ENV", "{}")
    cli_args_dict = ast.literal_eval(cli_args_str)
    return CliArguments(**cli_args_dict)


def start(cli_args: CliArguments):
    """
    Start the Hedge-It Application
    :param cli_args: CliArgs
    :return:
    """
    build_data(
        cli_args.polygon_api_key,
        exchanges=["XNYS"],
        stock_limit=int(cli_args.stock_limit),
    )
    plot(cli_args.polygon_api_key)


if __name__ == "__main__":
    cli_args = parse_args()
    log.info(f"CLI Arguments: {cli_args}")
    CustomLogger().setLevel(cli_args.log_level)
    start(cli_args)
