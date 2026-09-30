import pytest
from mission_agent.clock import FakeClock
from mission_agent.config import Config
from mission_agent.db.repository import Repository


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def config(tmp_path):
    return Config(tmp_path)


@pytest.fixture
def repo(tmp_path,clock):
    value=Repository(tmp_path/'mission.sqlite',clock)
    yield value
    value.close()
