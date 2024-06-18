import aiohttp
import asyncio
import time
import re
import math
import logging
from typing import Optional, Dict, List, Any
from statistics import mean


class AsyncSpeedtest:
    """
    A class to perform asynchronous speed tests to measure download and upload speeds.

    Attributes:
        CONFIG_URL (str): URL for the speed test configuration.
        SERVER_LIST_URL (str): URL for the speed test server list.
        DOWNLOAD_CHUNK_SIZES (List[int]): List of chunk sizes for download test.
        UPLOAD_CHUNK_SIZE (int): Chunk size for upload test.
        TEST_COUNT (int): Number of tests to perform.
        LATENCY_TEST_COUNT (int): Number of latency tests to perform.
        TIMEOUT (int): Timeout for each test in seconds.
        source_address (Optional[str]): Source address for the tests.
        debug (bool): Flag to enable debug logging.
        download (float): Measured download speed.
        upload (float): Measured upload speed.
        ping (float): Measured ping.
        best_server (Optional[Dict[str, Any]]): Best server for the tests.
    """

    CONFIG_URL = "https://www.speedtest.net/speedtest-config.php"
    SERVER_LIST_URL = "https://www.speedtest.net/speedtest-servers-static.php"
    DOWNLOAD_CHUNK_SIZE = 100 * 1024  # 100 KB
    UPLOAD_CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB
    TEST_COUNT = 3
    LATENCY_TEST_COUNT = 3
    TIMEOUT = 60  # 1 minute timeout

    def __init__(
        self, source_address: Optional[str] = None, debug: bool = False
    ) -> None:
        self.best_server: Optional[Dict[str, Any]] = None
        self.source_address: Optional[str] = source_address
        self.debug: bool = debug
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        self.download: float = 0.0
        self.upload: float = 0.0
        self.ping: float = 0.0

    async def fetch(
        self,
        session: aiohttp.ClientSession,
        url: str,
        method: str = "GET",
        data: Optional[bytes] = None,
    ) -> str:
        """
        Fetches data from the given URL using the specified method.

        Args:
            session (aiohttp.ClientSession): The aiohttp client session.
            url (str): The URL to fetch data from.
            method (str): The HTTP method to use for the request.
            data (Optional[bytes]): The data to send with the request, if any.

        Returns:
            str: The response text from the request.
        """
        async with session.request(method, url, data=data) as response:
            result: str = await response.text()
            if self.debug:
                logging.debug(f"Fetched {url} with method {method}")
            return result

    def calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculates the distance between two geographic coordinates.

        Args:
            lat1 (float): Latitude of the first coordinate.
            lon1 (float): Longitude of the first coordinate.
            lat2 (float): Latitude of the second coordinate.
            lon2 (float): Longitude of the second coordinate.

        Returns:
            float: The distance between the coordinates in kilometers.
        """
        R: float = 6371  # Radius of the earth in km
        dlat: float = math.radians(lat2 - lat1)
        dlon: float = math.radians(lon1 - lon2)
        a: float = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c: float = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance: float = R * c
        if self.debug:
            logging.debug(f"Calculated distance: {distance} km")
        return distance

    async def get_best_server(self) -> Optional[Dict[str, Any]]:
        """
        Finds the best server based on latency tests.

        Returns:
            Optional[Dict[str, Any]]: The best server's details, or None if no suitable server is found.
        """
        async with aiohttp.ClientSession() as session:
            response: str = await self.fetch(session, self.SERVER_LIST_URL)

        servers: List[Dict[str, Any]] = []
        for line in response.splitlines():
            match = re.search(
                r'<server url="(http://.*?)" lat="(.*?)" lon="(.*?)" name="(.*?)" country="(.*?)" id="(.*?)"',
                line,
            )
            if match:
                servers.append(
                    {
                        "url": match.group(1),
                        "lat": float(match.group(2)),
                        "lon": float(match.group(3)),
                        "name": match.group(4),
                        "country": match.group(5),
                        "id": match.group(6),
                    }
                )

        best: Optional[Dict[str, Any]] = None
        best_latency: float = float("inf")
        user_lat: float = servers[0]["lat"]
        user_lon: float = servers[0]["lon"]

        async with aiohttp.ClientSession() as session:
            for server in servers:
                distance: float = self.calculate_distance(
                    user_lat, user_lon, server["lat"], server["lon"]
                )
                if distance > 500:
                    continue

                latencies: List[float] = []
                for _ in range(self.LATENCY_TEST_COUNT):
                    try:
                        start: float = time.time()
                        await self.fetch(session, server["url"] + "?latency")
                        latency: float = time.time() - start
                        latencies.append(latency)
                    except Exception:
                        latencies.append(float("inf"))

                avg_latency: float = mean(latencies)
                if avg_latency < best_latency:
                    best_latency = avg_latency
                    best = server

        self.best_server = best
        if self.debug:
            logging.debug(f"Best server: {best}")
        self.server = best
        return best

    async def measure_download_speed(self) -> None:
        """
        Measures the download speed by fetching large chunks of data.

        Updates the instance's download attribute with the measured speed in bytes per second.
        """
        speeds: List[float] = []
        connector: Optional[aiohttp.TCPConnector] = (
            aiohttp.TCPConnector(local_addr=(self.source_address, 0))
            if self.source_address
            else None
        )
        url = self.server["url"]
        async with aiohttp.ClientSession(connector=connector) as session:
            for _ in range(self.TEST_COUNT):
                try:
                    start: float = time.time()
                    async with session.get(
                        url + "/random4000x4000.jpg", timeout=self.TIMEOUT
                    ) as response:
                        content_length: int = 0
                        while True:
                            chunk = await response.content.read(
                                self.DOWNLOAD_CHUNK_SIZE
                            )
                            if not chunk:
                                break
                            content_length += len(chunk)
                            if time.time() - start > self.TIMEOUT:
                                break
                    elapsed: float = time.time() - start
                    if content_length:
                        speed: float = content_length / elapsed
                        speeds.append(speed)
                        if self.debug:
                            logging.debug(f"Download speed test {url}: {speed} Bps")
                except Exception as e:
                    if self.debug:
                        logging.debug(f"Download speed test {url} failed: {e}")
                    continue
        self.download = mean(speeds) if speeds else 0.0

    async def measure_upload_speed(self) -> None:
        """
        Measures the upload speed by sending large chunks of data.

        Updates the instance's upload attribute with the measured speed in bytes per second.
        """
        speeds: List[float] = []
        data: bytes = b"0" * self.UPLOAD_CHUNK_SIZE
        connector: Optional[aiohttp.TCPConnector] = (
            aiohttp.TCPConnector(local_addr=(self.source_address, 0))
            if self.source_address
            else None
        )
        url = self.server["url"]

        async with aiohttp.ClientSession(connector=connector) as session:
            for _ in range(self.TEST_COUNT):
                try:
                    start: float = time.time()
                    async with session.post(
                        url + "/upload", data=data, timeout=self.TIMEOUT
                    ) as response:
                        await response.read()
                    elapsed: float = time.time() - start
                    speed: float = self.UPLOAD_CHUNK_SIZE / elapsed
                    speeds.append(speed)
                    if self.debug:
                        logging.debug(f"Upload speed test {url}: {speed} Bps")
                except Exception as e:
                    if self.debug:
                        logging.debug(f"Upload speed test {url} failed: {e}")
                    continue
        self.upload = mean(speeds) if speeds else 0.0


async def run_speedtest() -> None:
    """
    Runs the speed test to measure download and upload speeds, and prints the results.
    """
    st = AsyncSpeedtest(debug=True)
    print("Testing internet speed...")

    print("Finding best server...")
    best_server = await st.get_best_server()
    if not best_server:
        raise Exception("Could not find a suitable server.")

    print("Starting download test...")
    await st.measure_download_speed()

    print("Starting upload test...")
    await st.measure_upload_speed()

    download = st.download * 8 / (1024 * 1024)
    upload = st.upload * 8 / (1024 * 1024)

    print(f"Download speed: {download:.2f} Mbps")
    print(f"Upload speed: {upload:.2f} Mbps")


if __name__ == "__main__":
    asyncio.run(run_speedtest())
