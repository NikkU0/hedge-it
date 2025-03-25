import os
import subprocess
import sys

from hedge_it.commons import CliArgParser, CliArguments, CustomLogger
from hedge_it.start import start


def main():
    """
    Main Entrypoint for the Hedge-It Application.
    """
    common_parser = CliArgParser().common_parser

    args = common_parser.parse_args()
    print(f"CLI Arguments: {args}")
    sys.argv = [sys.argv[0], args]
    print(f"System Arguments: {sys.argv}")
    os.environ["PYTHONPATH"] = os.pathsep.join(sys.path)
    os.environ["HEDGE_ENV"] = str(vars(args))
    #For Debugging
    # start(CliArguments(**vars(args)))

def run_streamlit():
    """
    Run the Streamlit app.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    #streamlit_args = sys.argv[1:]
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    streamlit_app_path = os.path.join(base_dir, "start.py")
    subprocess.run(["streamlit", "run", streamlit_app_path])


if __name__ == "__main__":
    main()
    run_streamlit()
