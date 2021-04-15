import setuptools
import re

requirements = []
with open("requirements.txt", "r") as file:
    requirements = file.read().splitlines()

# Creds to Rapptz <3 https://github.com/Rapptz/discord.py/blob/master/setup.py#L8-L10
version = ''
with open('discord/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cheesyutils",
    version=version,
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