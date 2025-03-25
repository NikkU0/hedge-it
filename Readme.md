# Hedge It

## Prerequisites

- Python 3.10 installed.
- `venv` module installed (or `pyenv` as an alternative).
- `Polygon.io` API Key, used to fetch active tickers.

## Setup Instructions

1. **Clone the Repository**  
    Navigate to the directory where you want to clone the repository and run:  
    ```bash
    git clone <repository-url>
    cd hedge_it
    ```

2. **Create a Virtual Environment**  
    Create and activate a Python virtual environment:  
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install Dependencies**  
    Install all dependencies specified in `pyproject.toml`:  
    ```bash
    pip install .
    ```


4. **Run the Application**  
    Once inside the virtual environment, execute the following command:  
    ```bash
    cd hedge-it/src
    python -m hedge_it -pak=<API_KWY> -sl=100
    ```

## Parameters

- **`-pak` (Polygon API Key)**:  
  Used to fetch all active tickers. The free version has a limit of 5 API calls per second. Currently, only the `XNYS` stock exchange is used, which requires 2 API calls. Adding `XNAS` would require 6 API calls.

- **`-sl` (Stock Count)**[Optional]:  
  Specifies the number of stocks to fetch historical data and outstanding shares for. This is required due to the rate limiter. Although caching is enabled for yfinance api.
  Default value is `100`. Be warned using higher value can lead to failure.

- **`-l` (Log Level)**[Optional]:  
  Log level of application. By Default it `INFO`. Can be used
  to change log level.

## Alternate Setup Using Hatch

1. **Install Hatch**  
    Ensure you have Hatch installed. If not, install it by following the [Hatch Installation Guide](https://hatch.pypa.io/1.8/install/).

2. **Enter the Hatch Shell**  
    Navigate to the `hedge-it` directory and activate the Hatch environment:  
    ```bash
    cd hedge_it
    hatch shell
    ```

3. **Build the Project**  
    Build the project using Hatch:  
    ```bash
    hatch build
    ```
4. **Run the Project**  
    Once inside the virtual environment, execute the following command:  
    ```bash
    cd hedge-it/src
    python -m hedge_it -pak=<API_KWY> -sl=100
    ```

## Additional Notes

- **Data Sources**:  
  - `Polygon API` is used for fetching active tickers.  
  - `yfinance` is used to fetch stock history and outstanding share information.

- **Example Command**:  
  ```bash
  python -m hedge_it -pak=WUC7lMzSiLo9wdWAuM -sl=100
  ```