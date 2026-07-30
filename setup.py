from setuptools import setup, find_packages

setup(
    name="recon-framework",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "click>=8.0",
        "rich>=13.0",
        "sqlalchemy>=2.0",
        "pydantic>=2.0",
        "pydantic-settings>=2.0",
        "structlog>=23.0",
        "httpx>=0.25",
        "tenacity>=8.0",
        "dnspython>=2.4",
        "matplotlib>=3.7",
        "jinja2>=3.1",
        "tomli>=2.0",
        "tomli-w>=1.0",
    ],
    entry_points={
        "console_scripts": [
            "recon=recon.cli.main:cli",
        ],
    },
)
