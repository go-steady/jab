import sys
from distutils.core import setup

if not (sys.version_info.major >= 3 and sys.version_info.minor >= 7):
    raise Exception("jab only works with Python 3.7+")

VERSION = "0.3.1"

DEPENDENCIES = ["typing_extensions", "toposort", "uvloop"]

setup(
    name="jab",
    author="Niels Lindgren",
    version=VERSION,
    packages=["jab"],
    platforms="ANY",
    url="https://github.com/stntngo/jab",
    install_requires=DEPENDENCIES,
)
