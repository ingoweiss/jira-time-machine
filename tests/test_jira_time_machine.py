import sys
print(sys.path)

from .mocks import MockJira
import pytest

@pytest.fixture
def mock_jira():
    return MockJira("tests/mock_data/mock_jira_data.json")

def test_mock_jira(mock_jira):
    assert mock_jira is not None
    issues = mock_jira.search_issues("project = TEST")
    assert len(issues) > 0
    assert issues[0].key == "SEAH-2668"
