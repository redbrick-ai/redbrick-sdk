"""Test getting image size."""

from redbrick.utils.image import get_image_size, url_to_image


def test_get_image_size() -> None:
    """Test getting image size."""
    # arrange
    url = "https://cdn.mos.cms.futurecdn.net/wtqqnkYDYi2ifsWZVW2MT4-1200-80.jpg"

    # action
    type_, width, height = get_image_size(url)

    # assert
    assert type_ == "jpg"
    assert width == 1000
    assert height == 667


def test_url_to_image() -> None:
    """Test getting an image from a url."""
    # arrange
    url = "https://cdn.mos.cms.futurecdn.net/wtqqnkYDYi2ifsWZVW2MT4-1200-80.jpg"

    # action
    result = url_to_image(url)

    # assert
    assert result.size
