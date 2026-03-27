"""
Shared fixtures for Stratoptic test suite.
"""

import pytest
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from motor.rii_db import RIIDatabase

DB_ROOT = os.path.join(os.path.dirname(__file__), "..", "data", "rii_db")


@pytest.fixture(scope="session")
def db():
    return RIIDatabase(DB_ROOT)


@pytest.fixture(scope="session")
def air(db):
    return db.get("Air")


@pytest.fixture(scope="session")
def glass_bk7(db):
    return db.get("Glass_BK7")


@pytest.fixture(scope="session")
def sio2(db):
    return db.get("SiO2")


@pytest.fixture(scope="session")
def tio2(db):
    return db.get("TiO2")


@pytest.fixture(scope="session")
def ag(db):
    return db.get("Ag")
