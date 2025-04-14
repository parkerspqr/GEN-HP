from setuptools import setup, find_packages

setup(
    name="autohprust",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy==2.0.2",
        "opencv-python==4.11.0.86",
        "mss==10.0.0",
        "pynput==1.8.1",
        "pyobjc-framework-Cocoa==11.0",
        "paddlepaddle==2.7.0",
        "paddleocr==2.9.0",
        "loguru==0.7.2",
    ],
    author="Jordan Grand",
    description="Automation tool for Rust item usage",
    python_requires=">=3.10",
)