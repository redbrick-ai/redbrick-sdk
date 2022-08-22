"""Setup the python module."""
from setuptools import setup, find_packages  # type: ignore

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

install_requires = [
    "aiofiles<=0.8.0",
    "aiohttp<=3.8.1,>=3.7.4",
    "inquirerpy<=0.3.4,>=0.3.3",
    "matplotlib<=3.5.2,>=3.2",
    "natsort<=8.1.0,>=8.0.2",
    "nest-asyncio<=1.5.5,>=1.5.4",
    "nibabel<=4.0.1,>=3.2.2",
    "numpy<=1.23.0,>=1.15",
    "packaging<=21.3",
    "Pillow<=9.2.0,>=9.0.1",
    "rasterio<=1.3.0.post1,>=1.2.10; sys_platform=='darwin'",
    "rasterio<=1.3.0.post1,>=1.2.10; sys_platform=='linux'",
    "rasterio<=1.3.0.post1,>=1.2.10; python_version>='3.8'",
    "requests<=2.28.1,>=2.23.0",
    "Rich<=12.4.4",
    "scikit-image<=0.19.3,>=0.17.2",
    "Shapely<=1.8.2,>=1.8.0",
    "tenacity<=8.0.1",
    "tqdm<=4.64.0,>=4.50.0",
]

setup(
    name="redbrick-sdk",
    url="https://github.com/redbrick-ai/redbrick-sdk",
    description="RedBrick platform Python SDK!",
    py_modules=["redbrick"],
    python_requires=">=3.7, <3.10",
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
            "twine==4.0.1",
            "wheel==0.37.1",
            "pytest-mock==3.7.0",
            "pytest==7.1.2",
            "black==22.3.0",
            "mypy==0.961",
            "mypy-extensions==0.4.3",
            "pylint==2.14.3",
            "pycodestyle==2.8.0",
            "pydocstyle==6.1.1",
            "flake8==4.0.1",
            "flake8-print==5.0.0",
            "eradicate==1.0",
            "pytest-cov>=2.8.1",
            "pytest-asyncio==0.18.3",
            "pytest-eradicate==0.0.5",
            "pytest-pycodestyle==2.3.0",
            "pytest-pydocstyle==2.3.0",
            "pytest-black==0.3.12",
            "pytest-pylint==0.18.0",
            "pytest-mypy==0.9.1",
            "pytest-flake8==1.1.1",
            "pytest-randomly==3.12.0",
            "pytest-xdist==2.5.0",
            "pytest-xdist[psutil]==2.5.0",
        ]
    },
)
