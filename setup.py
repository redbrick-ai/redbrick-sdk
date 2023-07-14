"""Setup the python module."""
from setuptools import setup, find_packages  # type: ignore

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

install_requires = [
    "aiohttp<=3.8.4,>=3.7.4",
    "dicom2nifti<=2.4.8",
    "inquirerpy<=0.3.4,>=0.3.3",
    "natsort<=8.3.1,>=8.0.2",
    "nest-asyncio<=1.5.6,>=1.5.4",
    "nibabel<=5.1.0,>=3.2.2",
    "numpy<=1.24.3,>=1.15",
    "packaging<=23.1",
    "Pillow<=9.5.0,>=9.0.1",
    "python-dateutil<=2.8.2",
    "requests<=2.31.0,>=2.23.0",
    "Rich<=13.4.2",
    "rt-utils<=1.2.7",
    "shtab<=1.6.1",
    "tenacity<=8.2.2",
    "tqdm<=4.65.0,>=4.50.0",
]

setup(
    name="redbrick-sdk",
    url="https://github.com/redbrick-ai/redbrick-sdk",
    description="RedBrick platform Python SDK!",
    py_modules=["redbrick"],
    python_requires=">=3.8",
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
            "twine==4.0.2",
            "wheel==0.38.4",
            "pytest==7.2.0",
            "black==22.12.0",
            "mypy==0.991",
            "mypy-extensions==0.4.3",
            "pylint==2.15.9",
            "pycodestyle==2.8.0",
            "pydocstyle==6.2.2",
            "flake8==4.0.1",
            "flake8-print==5.0.0",
            "eradicate==1.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio==0.20.3",
            "pytest-eradicate==0.0.5",
            "pytest-pycodestyle==2.3.1",
            "pytest-pydocstyle==2.3.2",
            "pytest-black==0.3.12",
            "pytest-pylint==0.19.0",
            "pytest-mypy==0.10.3",
            "pytest-flake8==1.1.1",
            "pytest-randomly==3.12.0",
            "pytest-xdist==3.1.0",
            "pytest-xdist[psutil]==3.1.0",
        ]
    },
)
