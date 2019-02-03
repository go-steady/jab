from distutils.core import setup

VERSION = "0.1.0"

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
