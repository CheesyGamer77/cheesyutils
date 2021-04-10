import setuptools

requirements = []
with open("requirements.txt", "r") as file:
    requirements = file.read().splitlines()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cheesyutils",
    version="0.0.3",
    author="CheesyGamer77",
    description="A python package of miscelanious utilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CheesyGamer77/cheesyutils",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=requirements,
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)