from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from guided.configure.schema import Configuration, Skill
from guided.skills.command import app

runner = CliRunner()


@pytest.fixture
def empty_config():
    return Configuration()


@pytest.fixture
def config_with_skill():
    return Configuration(
        skills={
            "read_file": Skill(
                name="read_file",
                description="Read the contents of a local file",
                type="file_read",
            )
        }
    )


# list


def test_list_empty_shows_defaults(empty_config):
    result = runner.invoke(app, ["list"], obj=empty_config)
    assert result.exit_code == 0
    assert "read_file" in result.output
    assert "web_search" in result.output


def test_list_shows_skills(config_with_skill):
    result = runner.invoke(app, ["list"], obj=config_with_skill)
    assert result.exit_code == 0
    assert "read_file" in result.output
    assert "file_read" in result.output
    assert "Read the contents" in result.output


# add


def test_add_skill(empty_config):
    saved = MagicMock()
    with patch("guided.skills.command.save_config", saved):
        result = runner.invoke(
            app,
            ["add", "write_file", "file_write", "--description", "Write to a local file"],
            obj=empty_config,
        )
    assert result.exit_code == 0
    assert "added" in result.output
    saved.assert_called_once()
    config = saved.call_args[0][0]
    assert "write_file" in config.skills
    assert config.skills["write_file"].type == "file_write"
    assert config.skills["write_file"].description == "Write to a local file"


def test_add_duplicate_skill(config_with_skill):
    with patch("guided.skills.command.save_config") as saved:
        result = runner.invoke(
            app,
            ["add", "read_file", "file_read", "--description", "Duplicate"],
            obj=config_with_skill,
        )
    assert result.exit_code == 1
    assert "already exists" in result.output
    saved.assert_not_called()


# remove


def test_remove_skill(config_with_skill):
    saved = MagicMock()
    with patch("guided.skills.command.save_config", saved):
        result = runner.invoke(app, ["remove", "read_file"], obj=config_with_skill)
    assert result.exit_code == 0
    assert "removed" in result.output
    saved.assert_called_once()
    config = saved.call_args[0][0]
    assert "read_file" not in config.skills


def test_remove_nonexistent_skill(empty_config):
    with patch("guided.skills.command.save_config") as saved:
        result = runner.invoke(app, ["remove", "nonexistent"], obj=empty_config)
    assert result.exit_code == 1
    assert "not found" in result.output
    saved.assert_not_called()
