from setuptools import setup, find_packages

setup(
    name="matugen-sync",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "jinja2>=3.0.0",
        "hidapi>=0.12.0",
        "openrgb-python>=0.3.0",
        "requests>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "matugen-sync=matugen_sync.__main__:main",
        ],
    },
)
