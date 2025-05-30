from setuptools import setup, find_packages

setup(
    name="roam-semantic-search",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-multipart",
        "python-json-logger",
        "sentence-transformers",
        "faiss-cpu",
        "numpy",
        "requests",
        "aiohttp",
        "python-dotenv",
    ],
    python_requires=">=3.9",
) 