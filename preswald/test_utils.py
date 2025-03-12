import os
import pytest
import toml
import logging
from unittest.mock import mock_open, patch, MagicMock
from preswald.utils import (
    read_template,
    read_port_from_config,
    configure_logging,
    validate_slug,
    get_project_slug,
    generate_slug,
)


def test_read_template():
    mock_content = "Template content"
    with patch("pkg_resources.resource_filename") as mock_resource:
        with patch("builtins.open", mock_open(read_data=mock_content)):
            mock_resource.return_value = "mock/path/template.template"
            content = read_template("test_template")
            assert content == mock_content


def test_read_port_from_config_exists(tmp_path):
    config_path = tmp_path / "preswald.toml"
    config = {"project": {"port": 8000}}
    with open(config_path, "w") as f:
        toml.dump(config, f)

    port = read_port_from_config(str(config_path), 3000)
    assert port == 8000


def test_read_port_from_config_not_exists():
    port = read_port_from_config("nonexistent.toml", 3000)
    assert port == 3000


def test_read_port_from_config_invalid():
    with patch("toml.load") as mock_load:
        mock_load.side_effect = Exception("Invalid TOML")
        port = read_port_from_config("invalid.toml", 3000)
        assert port == 3000


def test_configure_logging_default():
    with patch("logging.basicConfig") as mock_basic_config:
        level = configure_logging()
        assert level == "INFO"
        mock_basic_config.assert_called_once()


def test_configure_logging_from_config(tmp_path):
    config_path = tmp_path / "preswald.toml"
    config = {"logging": {"level": "DEBUG", "format": "%(message)s"}}
    with open(config_path, "w") as f:
        toml.dump(config, f)

    level = configure_logging(str(config_path))
    assert level == "DEBUG"


def test_configure_logging_override_level():
    level = configure_logging(level="ERROR")
    assert level == "ERROR"


def test_validate_slug_valid():
    valid_slugs = ["test-slug", "my-project-123", "a1b", "abc-123-xyz"]
    for slug in valid_slugs:
        assert validate_slug(slug) is True


def test_validate_slug_invalid():
    invalid_slugs = [
        "-test",
        "test-",
        "Test",
        "te",
        "a" * 64,
        "test_slug",
        "test slug",
        "",
    ]
    for slug in invalid_slugs:
        assert validate_slug(slug) is False


def test_get_project_slug_valid(tmp_path):
    config_path = tmp_path / "preswald.toml"
    config = {"project": {"slug": "test-project"}}
    with open(config_path, "w") as f:
        toml.dump(config, f)

    slug = get_project_slug(str(config_path))
    assert slug == "test-project"


def test_get_project_slug_missing_file():
    with pytest.raises(Exception) as exc:
        get_project_slug("nonexistent.toml")
    assert "Config file not found" in str(exc.value)


def test_get_project_slug_missing_section(tmp_path):
    config_path = tmp_path / "preswald.toml"
    config = {"other": {"slug": "test-project"}}
    with open(config_path, "w") as f:
        toml.dump(config, f)

    with pytest.raises(Exception) as exc:
        get_project_slug(str(config_path))
    assert "Missing [project] section" in str(exc.value)


def test_get_project_slug_missing_field(tmp_path):
    config_path = tmp_path / "preswald.toml"
    config = {"project": {"name": "test"}}
    with open(config_path, "w") as f:
        toml.dump(config, f)

    with pytest.raises(Exception) as exc:
        get_project_slug(str(config_path))
    assert "Missing required field 'slug'" in str(exc.value)


def test_get_project_slug_invalid(tmp_path):
    config_path = tmp_path / "preswald.toml"
    config = {"project": {"slug": "Invalid Slug"}}
    with open(config_path, "w") as f:
        toml.dump(config, f)

    with pytest.raises(Exception) as exc:
        get_project_slug(str(config_path))
    assert "Invalid slug format" in str(exc.value)


def test_generate_slug():
    with patch("random.randint") as mock_random:
        mock_random.return_value = 123456
        slug = generate_slug("Test Project")
        assert slug == "test-project-123456"


def test_generate_slug_invalid_chars():
    with patch("random.randint") as mock_random:
        mock_random.return_value = 123456
        slug = generate_slug("!@#$%^")
        assert slug == "preswald-123456"


def test_generate_slug_length():
    base = "a" * 100
    slug = generate_slug(base)
    assert len(slug) <= 63
    assert validate_slug(slug)
