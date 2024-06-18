
[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/yourusername/AsyncSpeedTest/blob/main/LICENSE)


AsyncSpeedTest is a Python library for performing speed tests using asynchronous programming with `aiohttp`. It allows you to measure download and upload speeds, ping, and find the best server with low latency.

## Features

- **Asynchronous operations:** Fully async with `aiohttp` for non-blocking speed tests.
- **Server selection:** Automatically finds the best server with the lowest latency.
- **Speed measurement:** Measures download and upload speeds, and ping.
- **Custom exception handling:** Provides clear error messages for configuration, server, upload, and download errors.

## Installation

### Prerequisites

- Python 3.6 or higher
- `aiohttp` library

### Install via pip

You can install AsyncSpeedTest via pip:

```bash
pip install asyncspeedtest
```

### Install from source

Clone the repository and install:

```bash
git clone git@github.com:yourusername/AsyncSpeedTest.git
cd AsyncSpeedTest
pip install -r requirements.txt
```

## Usage

Here's a basic example of how to use AsyncSpeedTest to perform a speed test:

```python
import asyncio
from speedtest_async.speedtest import Speedtest

async def main():
    async with Speedtest() as speedtest:
        await speedtest.get_config()
        await speedtest.get_best_server()
        ping = await speedtest.ping()
        download = await speedtest.download()
        upload = await speedtest.upload()

        print(f"Ping: {ping:.2f} ms | Download: {download:.2f} Mbps | Upload: {upload:.2f} Mbps")

if __name__ == "__main__":
    asyncio.run(main())
```

### Detailed Steps

1. **Initialize Speedtest**:
   ```python
   async with Speedtest() as speedtest:
   ```

2. **Get Configuration**:
   ```python
   await speedtest.get_config()
   ```

3. **Find Best Server**:
   ```python
   await speedtest.get_best_server()
   ```

4. **Measure Ping**:
   ```python
   ping = await speedtest.ping()
   ```

5. **Measure Download Speed**:
   ```python
   download = await speedtest.download()
   ```

6. **Measure Upload Speed**:
   ```python
   upload = await speedtest.upload()
   ```

## Contributing

We welcome contributions to AsyncSpeedTest! Please read our [contributing guidelines](CONTRIBUTING.md) before submitting a pull request.

### Setting up Development Environment

1. **Clone the repository**:
   ```bash
   git clone git@github.com:yourusername/AsyncSpeedTest.git
   cd AsyncSpeedTest
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows, use `env\Scripts\activate`
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run tests**:
   ```bash
   python -m unittest discover
   ```

## Running Tests

To run the tests, use:

```bash
python -m unittest discover
```

or with `tox` for multiple environments:

```bash
tox
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by [speedtest-cli](https://github.com/sivel/speedtest-cli)
- Uses [aiohttp](https://github.com/aio-libs/aiohttp) for asynchronous HTTP requests
```

This `README.md` file includes the following sections:
- Project name and badges for license and build status.
- A brief description of the project and its features.
- Detailed installation instructions, including prerequisites and installation via pip or from source.
- Example usage with detailed steps.
- Contribution guidelines and instructions for setting up the development environment.
- Instructions for running tests.
- License information.
- Acknowledgments for inspiration and libraries used.
