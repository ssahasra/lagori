import json
import pytest
from unittest.mock import patch, Mock
from gh_stack import getPullRequest, getPullRequestsForAuthor, printAllStacksForAuthor

def createPR(headRefName, baseRefName, number):
    return {
        'number': number,
        'headRefName': headRefName,
        'baseRefName': baseRefName,
        'url': 'url',
        'title': 'Test PR',
        'author': {'login': 'testuser'}
    }

def createStack(branchNames: list[str]):
    return [
        createPR(
            headRefName=branchNames[i],
            baseRefName=branchNames[i + 1],
            number=i + 1
        ) for i in range(len(branchNames) - 1)
    ]

@pytest.fixture
def mock_pr_data():
    return createPR('feature-branch', 'main', 123)

@pytest.fixture
def mock_pulls_data():
    return createStack(['f2', 'f1', 'main'])

class TestBasicPullRequest:
    @patch('subprocess.run')
    def test_get_pull_request(self, mock_run, mock_pr_data):
        mock_run.return_value = Mock(returncode=0, stdout=json.dumps(mock_pr_data))
        result = getPullRequest('123')
        assert result == mock_pr_data

    @patch('subprocess.run')
    def test_get_pull_requests_for_author(self, mock_run, mock_pulls_data):
        mock_run.return_value = Mock(returncode=0, stdout=json.dumps(mock_pulls_data))
        result = getPullRequestsForAuthor('testuser')
        assert len(result) == len(mock_pulls_data)
        for pr in mock_pulls_data:
            assert result[pr['headRefName']] == pr

@patch('subprocess.run')
def test_print_all_stacks_for_author(mock_run, mock_pulls_data, capsys):
    mock_run.return_value = Mock(returncode=0, stdout=json.dumps(mock_pulls_data))
    printAllStacksForAuthor('testuser')
    captured = capsys.readouterr()
    assert 'Stack 1:' in captured.out
    assert 'Test PR [#1]' in captured.out
    assert 'Test PR [#2]' in captured.out
    # assert that the PR numbers are in order
    # (this is a bit of a hack, but it works for the test)
    lines = captured.out.split('\n')
    prNums = []
    for line in lines:
        if 'Test PR' in line:
            prNum = line.split('[')[1].split(']')[0][1:]
            prNums.append(int(prNum))
    assert prNums == sorted(prNums)

