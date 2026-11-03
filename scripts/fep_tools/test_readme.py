import pytest

from scripts.fep_tools import Readme, README_PATH


@pytest.mark.skip("Only is correct for main branch and not pull requests")
def test_readme():
    with open(README_PATH) as f:
        lines = f.readlines()

    expected = Readme().content

    assert lines == expected


def test_readme_can_be_created():
    content = Readme().content

    assert isinstance(content, list)
