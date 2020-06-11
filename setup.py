from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name="redbrick-sdk",
    url="https://github.com/dereklukacs/redbrick-sdk",
    version="0.0.7",
    description="RedBrick platform python SDK!",
    py_modules=["redbrick"],
    packages=find_packages(),
    # package_dir={"": "redbrick"},
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "opencv-python==4.2.0.34",
        "numpy==1.18.5",
        "matplotlib==3.2.1",
        "requests==2.23.0",
    ],
    extras_require={
        "dev": [
            "pytest>=3.7",
            "black==19.10b0",
            "pydocstyle==5.0.2",
            "pycodestyle==2.6.0",
            "twine==3.1.1",
        ]
    },
)
