import asyncio
import aiohttp
import time
import math
import xml.etree.ElementTree as ET
import os
import logging
from typing import Dict, List, Optional, Tuple

# Set up logging
logger = logging.getLogger("Speedtest")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class SpeedtestException(Exception):
    """Base exception class for Speedtest."""

    pass


class SpeedtestConfigError(SpeedtestException):
    """Exception raised for errors in the Speedtest configuration."""

    pass


class SpeedtestServersError(SpeedtestException):
    """Exception raised for errors in retrieving Speedtest servers."""

    pass


class SpeedtestUploadError(SpeedtestException):
    """Exception raised for errors during upload in Speedtest."""

    pass


class SpeedtestDownloadError(SpeedtestException):
    """Exception raised for errors during download in Speedtest."""

    pass


class ConfigRetrievalError(SpeedtestException):
    """Exception raised for errors in retrieving the configuration."""

    pass


class Speedtest:
    """A class to perform speed tests using asynchronous programming with aiohttp."""

    MAX_DOWNLOAD_SIZE = 20 * 1024 * 1024  # 20 MB
    MAX_DOWNLOAD_TIME = 30  # 30 seconds

    def __init__(
        self,
        source_address: Optional[str] = None,
        timeout: int = 10,
        secure: bool = False,
        debug: bool = False,
    ):
        """
        Initialize the Speedtest class.

        Args:
            source_address (Optional[str]): The source address for the connection.
            timeout (int): Timeout for HTTP requests.
            secure (bool): Use HTTPS for connections.
            debug (bool): Enable debug logging.
        """
        self.config: Dict[str, any] = {}
        self._source_address = source_address
        self._timeout = timeout
        self._secure = secure
        self._debug = debug
        if self._debug:
            logger.setLevel(logging.DEBUG)
        self.total_downloaded: int = 0
        self.total_uploaded: int = 0
        self.servers: Dict[float, List[Dict[str, any]]] = {}
        self.closest: List[Dict[str, any]] = []
        self._best: Dict[str, any] = {}
        self.results: Dict[str, any] = {
            "download": 0,
            "upload": 0,
            "ping": 0,
            "server": None,
            "timestamp": "",
            "bytes_received": 0,
            "bytes_sent": 0,
            "public_ip": "0.0.0.0",
        }
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """
        Enter the asynchronous context manager.

        Returns:
            Speedtest: The Speedtest instance.
        """
        connector = (
            aiohttp.TCPConnector(local_addr=(self._source_address, 0))
            if self._source_address
            else None
        )
        self.session = aiohttp.ClientSession(connector=connector)
        self.config = await self.get_config()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the asynchronous context manager and close the session."""
        if self.session:
            await self.session.close()

    async def fetch(self, url: str, headers: Optional[Dict[str, str]] = None) -> str:
        """
        Fetch the content from the specified URL.

        Args:
            url (str): The URL to fetch content from.
            headers (Optional[Dict[str, str]]): Optional headers for the request.

        Returns:
            str: The content of the response.

        Raises:
            ConfigRetrievalError: If fetching the content fails.
        """
        if not self.session:
            raise RuntimeError("Session not initialized.")
        logger.debug(f"Fetching URL: {url}")
        async with self.session.get(
            url, headers=headers, timeout=self._timeout
        ) as response:
            if response.status != 200:
                raise ConfigRetrievalError(f"Failed to fetch {url}")
            return await response.text()

    async def get_config(self) -> Dict[str, any]:
        """
        Retrieve the Speedtest configuration.

        Returns:
            Dict[str, any]: The configuration dictionary.

        Raises:
            SpeedtestConfigError: If retrieving the configuration fails.
        """
        url = "https://www.speedtest.net/speedtest-config.php"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(
                            f"Failed to get configuration: HTTP {response.status}"
                        )
                        raise SpeedtestConfigError()
                    configxml = await response.read()

            root = ET.fromstring(configxml)
            server_config = root.find("server-config").attrib
            download = root.find("download").attrib
            upload = root.find("upload").attrib
            client = root.find("client").attrib

            ignore_servers = [
                int(i) for i in server_config["ignoreids"].split(",") if i
            ]
            ratio = int(upload["ratio"])
            upload_max = int(upload["maxchunkcount"])
            up_sizes = [32768, 65536, 131072, 262144, 524288, 1048576, 7340032]

            sizes = {
                "upload": up_sizes[ratio - 1 :],
                "download": [350, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000],
            }
            size_count = len(sizes["upload"])
            upload_count = int(math.ceil(upload_max / size_count))

            self.config.update(
                {
                    "client": client,
                    "ignore_servers": ignore_servers,
                    "sizes": sizes,
                    "counts": {
                        "upload": upload_count,
                        "download": int(download["threadsperurl"]),
                    },
                    "threads": {
                        "upload": int(upload["threads"]),
                        "download": int(server_config["threadcount"]) * 2,
                    },
                    "length": {
                        "upload": int(upload["testlength"]),
                        "download": int(download["testlength"]),
                    },
                    "upload_max": upload_count * size_count,
                }
            )

            self.lat_lon = (float(client["lat"]), float(client["lon"]))
            self.results["public_ip"] = client["ip"]
            return self.config

        except aiohttp.ClientConnectorError as e:
            logger.error(f"Client connector error: {e}")
            raise SpeedtestConfigError(e)
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
            raise SpeedtestConfigError()

    async def get_best_server(self) -> None:
        """
        Retrieve the best server based on latency.

        Raises:
            SpeedtestServersError: If retrieving servers fails.
        """
        headers = {"Accept-Encoding": "gzip"}
        SERVERS_API_URL = "https://www.speedtest.net/api/js/servers?engine=js&limit=5&https_functional=true"

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(SERVERS_API_URL) as response:
                    if response.status != 200:
                        logger.error(f"Failed to get servers: HTTP {response.status}")
                        raise SpeedtestServersError()
                    servers = await response.json()

                    latencies = []
                    for server in servers:
                        url = os.path.dirname(server["url"]) + "/latency.txt"
                        start_time = time.time()
                        try:
                            async with session.get(url) as resp:
                                if resp.status == 200:
                                    duration = (time.time() - start_time) * 1000
                                    latencies.append((duration, server))
                                    logger.debug(
                                        f"Server {server['name']} latency: {duration:.2f} ms"
                                    )
                                else:
                                    latencies.append((float("inf"), server))
                                    logger.debug(
                                        f"Server {server['name']} is not reachable."
                                    )
                        except Exception as e:
                            latencies.append((float("inf"), server))
                            logger.debug(f"Error pinging server {server['name']}: {e}")

                    # Select the server with the lowest latency
                    best_latency, best_server = min(latencies, key=lambda x: x[0])
                    self.server = best_server
                    self.results["server"] = best_server["host"]
                    logger.info(
                        f"Best server selected: {self.server['host']} with latency {best_latency:.2f} ms"
                    )
        except Exception as e:
            logger.error(f"Error fetching servers: {e}")
            raise SpeedtestServersError()

    async def ping(self) -> float:
        """
        Measure the latency (ping) to the best server.

        Returns:
            float: The measured ping in milliseconds.
        """
        url = os.path.dirname(self.server["url"]) + "/latency.txt"
        logger.debug(f"Pinging {url}")
        try:
            start = time.time()
            async with self.session.get(url):
                duration = time.time() - start
            ping = duration * 1000  # convert to milliseconds
            self.results["ping"] = ping
            return ping
        except Exception as e:
            logger.error(f"Error pinging {url}: {e}")
            return 0.0

    async def download(self) -> float:
        start_time = time.time()
        urls = [
            f"{os.path.dirname(self.server['url'])}/random{size}x{size}.jpg"
            for size in self.config["sizes"]["download"]
            for _ in range(self.config["counts"]["download"])
        ]
        self.total_downloaded = 0

        try:
            async with aiohttp.ClientSession() as session:
                tasks = [self._download_file(session, url) for url in urls]
                await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise SpeedtestDownloadError(e)  # Raise custom download error

        end_time = time.time()
        download_speed = self._calculate_download_speed(start_time, end_time)
        self.results["download"] = download_speed
        self.results["bytes_received"] = self.total_downloaded
        self.results["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        return download_speed

    async def _download_file(self, session: aiohttp.ClientSession, url: str) -> None:
        try:
            async with session.get(url) as response:
                while True:
                    chunk = await response.content.read(10240)
                    if not chunk or self.total_downloaded >= self.MAX_DOWNLOAD_SIZE:
                        break
                    self.total_downloaded += len(chunk)
        except Exception as e:
            logger.error(f"Unexpected error downloading file from {url}: {e}")
            raise SpeedtestDownloadError(e)  # Raise custom download error

    def _calculate_download_speed(self, start_time: float, end_time: float) -> float:
        elapsed_time = end_time - start_time
        speed_mbps = (self.total_downloaded * 8) / (elapsed_time * 1_000_000)
        return float(f"{speed_mbps:.2f}")

    async def upload(self) -> float:
        """
        Measure the upload speed to the best server.

        Returns:
            float: The measured upload speed in Mbps.
        """
        sizes = self.config["sizes"]["upload"]

        self.start_time = time.time()
        self.total_uploaded = 0

        if not self.session:
            raise RuntimeError("Session not initialized.")
        for size in sizes:
            data = b"0" * size
            retries = 3
            while retries > 0:
                try:
                    async with self.session.post(
                        self.server["url"], data=data
                    ) as response:
                        self.total_uploaded += size
                    logger.debug(f"Uploaded size: {size} bytes")
                    break  # exit retry loop if successful
                except (aiohttp.ClientPayloadError, aiohttp.ClientOSError) as e:
                    retries -= 1
                    logger.debug(
                        f"Failed to upload size: {size} bytes, retries left: {retries}, error: {e}"
                    )
                    if retries == 0:
                        logger.error(f"Failed to upload to {self.server['url']}: {e}")
                        raise SpeedtestUploadError(e)  # Raise custom upload error
                    continue
                except Exception as e:
                    logger.error(
                        f"Unexpected error uploading file to {self.server['url']}: {e}"
                    )
                    raise SpeedtestUploadError(e)  # Raise custom upload error

        end_time = time.time()
        upload_speed = self._calculate_upload_speed(
            self.total_uploaded, self.start_time, end_time
        )
        self.results["upload"] = upload_speed
        self.results["bytes_sent"] = self.total_uploaded
        return upload_speed

    def _calculate_upload_speed(
        self, total_bytes: int, start_time: float, end_time: float
    ) -> float:
        """
        Calculate the speed in Mbps.

        Args:
            total_bytes (int): The total bytes transferred.
            start_time (float): The start time of the transfer.
            end_time (float): The end time of the transfer.

        Returns:
            float: The calculated speed in Mbps.
        """
        elapsed_time = end_time - start_time
        if elapsed_time == 0:
            logger.warning("Elapsed time is zero during speed calculation.")
            return 0.0
        speed_mbps = (total_bytes * 8) / (elapsed_time * 1_000_000)
        logger.debug(
            f"Calculated speed: {speed_mbps:.2f} Mbps over {elapsed_time:.2f} seconds."
        )
        return float(f"{speed_mbps:.2f}")

    def distance(
        self, origin: Tuple[float, float], destination: Tuple[float, float]
    ) -> float:
        """
        Calculate the distance between two geographical points.

        Args:
            origin (Tuple[float, float]): The latitude and longitude of the origin point.
            destination (Tuple[float, float]): The latitude and longitude of the destination point.

        Returns:
            float: The distance in kilometers.
        """
        lat1, lon1 = origin
        lat2, lon2 = destination
        radius = 6371  # km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius * c


async def main() -> None:
    """Main function to run the speed test."""
    source_address = None
    debug = False
    speedtest = None  # Define speedtest here to ensure it's accessible in finally block
    try:
        async with Speedtest(source_address=source_address, debug=debug) as speedtest:
            print("Fetching configuration...")
            await speedtest.get_config()

            print("Finding best server...")
            await speedtest.get_best_server()

            print("Pinging server...")
            ping = await speedtest.ping()

            print("Starting download test...")
            download = await speedtest.download()

            print("Starting upload test...")
            upload = await speedtest.upload()

            print(
                f"Ping: {ping:.2f} ms | Download: {download:.2f} Mbps | Upload: {upload:.2f} Mbps"
            )

            # Include final results details
            print(f"Public Address: {speedtest.results['public_ip']}")
            print(f"Timestamp: {speedtest.results['timestamp']}")
            print(f"Bytes Received: {speedtest.results['bytes_received']}")
            print(f"Bytes Sent: {speedtest.results['bytes_sent']}")
    except Exception as e:
        print(e)
    finally:
        if speedtest:
            print(speedtest.results)
        else:
            print("Speedtest object was not created successfully.")


if __name__ == "__main__":
    start_time = time.time()  # Record the start time

    asyncio.run(main())

    end_time = time.time()  # Record the end time
    execution_time = end_time - start_time  # Calculate the execution time
    logger.info(f"Execution time: {execution_time:.2f} seconds")
