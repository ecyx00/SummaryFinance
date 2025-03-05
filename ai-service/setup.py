from setuptools import setup, find_packages

setup(
    name="summaryfinance-ai",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi==0.109.2",
        "uvicorn==0.27.1",
        "google-generativeai==0.3.2",
        "python-dotenv==1.0.1",
        "requests==2.31.0",
        "pydantic==2.6.1",
        "aiohttp==3.9.3"
    ],
)
