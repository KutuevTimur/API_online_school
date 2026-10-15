"""Migration tests own schema setup; never use metadata.create_all/row cleaners."""
import pytest


@pytest.fixture(scope="session", autouse=True)
def start_test():
    yield


@pytest.fixture(autouse=True)
def clearing_db():
    yield
