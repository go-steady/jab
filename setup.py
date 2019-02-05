import sys
from distutils.core import setup

if not (sys.version_info.major >= 3 and sys.version_info.minor >= 7):
    raise Exception("jab only works with Python 3.7+")

VERSION = "0.2.0"

dependencies = ["typing_extensions", "toposort"]

setup(
    name="jab",
    author="Steady",
    version=VERSION,
    packages=["jab"],
    platforms="ANY",
    url="https://github.com/go-steady/jab",
    install_requires=dependencies,
)
