import asyncio
import unittest
from speedtest_async.speedtest import Speedtest


class TestSpeedtest(unittest.TestCase):
    def setUp(self):
        self.speedtest = Speedtest()

    def test_set_default_results(self):
        self.speedtest.set_default_results()
        expected_results = {
            "download": 0,
            "upload": 0,
            "ping": 0,
            "server": None,
            "timestamp": "",
            "bytes_received": 0,
            "bytes_sent": 0,
            "share": None,
            "client": {},
        }
        self.assertEqual(self.speedtest.results, expected_results)

    async def test_fetch_config(self):
        async with Speedtest() as speedtest:
            config = await speedtest.get_config()
            self.assertIn("client", config)


if __name__ == "__main__":
    unittest.main()
