from setuptools import setup, find_packages

setup(
    name="speedtest_async",
    version="0.1.0",
    description="A Python library for performing speed tests using asyncio.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Adel AbdElGawad",
    author_email="tech.adel87@gmail.com",
    url="https://github.com/adelabdelgawad/AsyncSpeedTest",
    packages=find_packages(),
    install_requires=[
        "aiohttp",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
