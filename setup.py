from setuptools import setup, find_packages

setup(
    name="pyele",  # Name of your package
    version="0.1",  # Version number
    description="A Python module for fetching and processing digital elevation model (DEM) data",
    author="Wataru Uda",
    author_email="udawtr@gmail.com",
    url="https://github.com/udawtr/pyele",
    packages=find_packages(),  # Automatically find all packages
    install_requires=[
        "numpy",
        "Pillow",
        "requests"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',  # Minimum version requirement of the package
)
