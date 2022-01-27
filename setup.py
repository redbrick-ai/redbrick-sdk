"""Setup the python module."""
from setuptools import setup, find_packages  # type: ignore

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

install_requires = [
    "requests==2.23.0",
    "tqdm==4.50.0",
    "aiohttp==3.7.4",
    "cchardet==2.1.7",
    "aiodns==3.0.0",
    "Pillow==8.3.2",
    "shapely==1.8.0",
    "numpy>=1.15",
    "matplotlib>=3.2",
    "scikit-image==0.18.3",
    "pyparsing==2.4.7",
    "aiofiles==0.8.0",
    "rasterio==1.2.10; sys_platform=='darwin'",
    "rasterio==1.2.10; sys_platform=='linux'",
    "InquirerPy==0.3.0",
    "halo==0.0.31",
    "nest-asyncio==1.5.4",
    "tenacity==8.0.1",
    "natsort==8.0.2",
]

setup(
    name="redbrick-sdk",
    url="https://github.com/redbrick-ai/redbrick-sdk",
    description="RedBrick platform Python SDK!",
    py_modules=["redbrick"],
    python_requires=">=3.7.0, <3.10",
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=install_requires,
    entry_points={
        "console_scripts": ["redbrick=redbrick.cli:cli_main"],
    },
    extras_require={
        "dev": [
            "twine==3.1.1",
            "wheel==0.35.1",
            "pytest-mock==3.3.1",
            "pytest==6.1.2",
            "black==21.7b0",
            "mypy==0.790",
            "mypy-extensions==0.4.3",
            "pylint==2.11.1",
            "pycodestyle==2.6.0",
            "pydocstyle==5.1.1",
            "flake8==3.8.4",
            "flake8-print==3.1.4",
            "eradicate==1.0",
            "pytest-cov>=2.8.1",
            "pytest-asyncio==0.12.0",
            "pytest-eradicate==0.0.5",
            "pytest-pycodestyle==2.2.0",
            "pytest-pydocstyle==2.2.0",
            "pytest-black==0.3.12",
            "pytest-pylint==0.17.0",
            "pytest-mypy==0.7.0",
            "pytest-flake8==1.0.6",
            "pytest-randomly==3.4.1",
        ]
    },
)
