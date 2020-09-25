import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="k8s-healthcheck",
    version="0.0.1",
    author="Chris McCoy",
    author_email="chris@chr.is",
    description="A quick and dirty health checker",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chris-mccoy/k8s-healthcheck",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

