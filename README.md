Sure! Here's a `README.md` for your project that includes nice formatting and icons to make it more appealing.

```markdown
# AsyncSpeedtest

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

A Python script to perform asynchronous internet speed tests using the `aiohttp` library. This tool measures download and upload speeds and finds the best server for testing based on latency.

## Features

- 🌐 Asynchronous speed testing
- 🚀 Measures download and upload speeds
- 🔍 Finds the best server based on latency
- 🐍 Compatible with Python 3.7 and above
- 🛠️ Optional debug logging for detailed insights

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/adelabdegawad/async-speedtest.git
    cd async-speedtest
    ```

2. **Create a virtual environment and activate it:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. **Run the script:**
    ```bash
    python main.py
    ```

    This will start the asynchronous speed test, find the best server, and measure the download and upload speeds.

## Example Output

```plaintext
Testing internet speed...
Finding best server...
Best server: Server Name, Country (ID: server_id)
Starting download test...
Starting upload test...
Download speed: 100.00 Mbps
Upload speed: 50.00 Mbps
```

## Code Overview

The main components of the script are:

- **AsyncSpeedtest Class:**
    - `fetch`: Asynchronous method to fetch data from a URL.
    - `calculate_distance`: Calculates the distance between two geographic coordinates.
    - `get_best_server`: Finds the best server based on latency.
    - `measure_download_speed`: Measures download speed by fetching large chunks of data.
    - `measure_upload_speed`: Measures upload speed by sending large chunks of data.

- **run_speedtest Function:**
    - Initializes the `AsyncSpeedtest` class.
    - Finds the best server.
    - Measures download and upload speeds.
    - Prints the results.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

- GitHub: [yourusername](https://github.com/abdelgawad)
- Email: [tech.adel87@gmail.com](mailto:tech.adel87@gmail.com)
```

### Explanation:

- **Badges**: Icons for Python version and license for a professional touch.
- **Installation**: Step-by-step instructions to set up the project.
- **Usage**: Instructions to run the script and example output.
- **Code Overview**: A brief explanation of the main components.
- **Contributing**: Encouragement for contributions.
- **License**: Information about the project's license.
- **Contact**: Your GitHub profile and email for further contact.

Replace `yourusername` and `tech.adel87@gmail.com` with your actual GitHub username and email address. This `README.md` will provide clear and attractive documentation for your project.