# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name="hypatia-py",
    description=(
        "An Operation and Planning Energy System Modelling Framework in Python"
    ),
    long_description=open("README.rst").read(),
    url="https://github.com/SESAM-Polimi/hypatia",
    author="Negar Namazifard",
    author_email="negarnamazifard@gmail.com",
    version="0.1.1",
    packages=find_packages(),
    license="Apache 2.0",
    python_requires=">.3.7.0",
    package_data={"": ["*.txt", "*.dat", "*.doc", "*.rst", "*.xlsx"]},
    install_requires=[
        "pandas >= 1.3.3",
        "numpy >= 1.21.2",
        "xlsxwriter <= 1.3.7",
        "plotly >= 4.12.0",
        "openpyxl >= 3.0.6",
        "IPython >= 7.22.0",
        "cvxopt >= 1.2.7",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering",
    ],
)
