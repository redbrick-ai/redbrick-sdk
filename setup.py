from setuptools import setup, find_packages  # type: ignore
import os

with open("README.md", "r") as fh:
    long_description = fh.read()

with open(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "redbrick", "VERSION"),
    "r",
    encoding="utf-8",
) as f:
    version = f.read().strip()

setup(
    name="redbrick-sdk",
    url="https://github.com/redbrick-ai/redbrick-sdk",
    version=version,
    description="RedBrick platform Python SDK!",
    py_modules=["redbrick"],
    packages=find_packages(),
    # package_dir={"": "redbrick"},
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=[
        "requests==2.23.0",
        "tqdm==4.50.0",
        "termcolor==1.1.0",
        "requests==2.23.0",
        "aiohttp==3.7.4.post0",
        "cchardet==2.1.7",
        "aiodns==3.0.0",
        "Pillow==8.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=3.7",
            "black==19.10b0",
            "pydocstyle==5.0.2",
            "pycodestyle==2.6.0",
            "twine==3.1.1",
            "wheel==0.35.1",
            "mypy==0.790",
            "pytest-mock==3.3.1",
        ]
    },
)
