import io
import os
from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="oca-github-bot",
    use_scm_version=True,
    long_description=long_description,
    author="Odoo Community Association (OCA)",
    author_email="info@odoo-community.org",
    url="https://github.com/OCA/oca-github-bot",
    python_requires=">=3.6",
    setup_requires=["setuptools_scm"],
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=[
        # aiohttp ang gitgethub for the webhook app
        "aiohttp",
        "gidgethub",
        # GitHub client
        "github3.py",
        # celery and celery monitoring for the task queue
        "flower",
        "celery[redis]",
        # Sentry
        "raven",
    ],
    license="MIT",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
    ],
)
