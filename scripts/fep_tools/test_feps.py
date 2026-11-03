import datetime
import pytest

from urllib.parse import urlparse

from scripts.fep_tools import (
    get_fep_ids,
    get_registered_fep_ids,
    title_to_slug,
    FepFile,
)


def is_valid_url(url: str):
    result = urlparse(url)
    if result.netloc == '':
        return False
    elif result.netloc.endswith(".example"):
        return False
    return True


@pytest.fixture(scope="session")
def registered_fep_ids():
    return get_registered_fep_ids()


@pytest.mark.parametrize("fep_id", list(get_fep_ids()))
def test_fep_front_matter(fep_id, registered_fep_ids):
    fep_file = FepFile(fep_id)
    parsed_frontmatter = fep_file.parsed_frontmatter
    is_registered = fep_id in registered_fep_ids

    assert "status" in parsed_frontmatter
    assert parsed_frontmatter["status"] in ["DRAFT", "FINAL", "WITHDRAWN"]
    assert parsed_frontmatter["slug"] == fep_id
    assert "dateReceived" in parsed_frontmatter
    assert "discussionsTo" in parsed_frontmatter
    if is_registered:
        assert "trackingIssue" in parsed_frontmatter

    assert isinstance(parsed_frontmatter["authors"], list)

    if "relatedFeps" in parsed_frontmatter:
        assert isinstance(parsed_frontmatter["relatedFeps"], list)

    discussions_to = parsed_frontmatter["discussionsTo"]
    assert is_valid_url(discussions_to), (
        "Update discussionsTo to a valid URL for a discussion topic"
    )

    if "trackingIssue" in parsed_frontmatter:
        assert is_valid_url(parsed_frontmatter["trackingIssue"])

    if parsed_frontmatter["status"] == "FINAL":
        assert "dateFinalized" in parsed_frontmatter
    if parsed_frontmatter["status"] == "WITHDRAWN":
        assert "dateWithdrawn" in parsed_frontmatter

    for field_name in ["dateReceived", "dateFinalized", "dateWithdrawn"]:
        if field_name in parsed_frontmatter:
            assert isinstance(parsed_frontmatter[field_name], datetime.date)

    if "type" in parsed_frontmatter:
        assert parsed_frontmatter["type"] in ["informational", "implementation"]

    if "tags" in parsed_frontmatter:
        assert type(parsed_frontmatter["tags"] == list)
        assert all(type(item) == str for item in parsed_frontmatter["tags"])


@pytest.mark.parametrize("fep_id", list(get_fep_ids()))
def test_fep_content(fep_id):
    fep_file = FepFile(fep_id)

    content = fep_file.content

    assert "## Summary" in content
    assert "## Copyright" in content

    titles = [x for x in content if x.startswith("# ")]
    assert len(titles) > 0

    title = titles[0]

    begin_title = f"# FEP-{fep_id}: "

    assert title.startswith(begin_title)
    true_title = title.removeprefix(begin_title)

    expected_slug = title_to_slug(true_title)

    assert expected_slug == fep_id
