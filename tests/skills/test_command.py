from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from guided.configure.schema import Configuration, Skill
from guided.skills.command import app

runner = CliRunner()


def make_skill(name="myskill", description="A skill") -> Skill:
    return Skill(name=name, description=description, parameters={}, handler=None)


# list


def test_list_no_skills():
    result = runner.invoke(app, ["list"], obj=Configuration())
    assert result.exit_code == 0
    assert "No skills configured" in result.output


# remove


def test_remove_skill():
    skill = make_skill(name="myskill")
    config = Configuration(skills={"myskill": skill})
    with patch("guided.skills.command.save_config") as mock_save:
        result = runner.invoke(app, ["remove", "myskill"], obj=config)
    assert result.exit_code == 0
    assert "myskill" in result.output
    mock_save.assert_called_once()


def test_remove_skill_deletes_from_config():
    skill = make_skill(name="myskill")
    config = Configuration(skills={"myskill": skill})
    with patch("guided.skills.command.save_config"):
        runner.invoke(app, ["remove", "myskill"], obj=config)
    assert "myskill" not in config.skills


def test_remove_nonexistent_skill():
    config = Configuration()
    result = runner.invoke(app, ["remove", "ghost"], obj=config)
    assert result.exit_code == 1
    assert "not found" in result.output


# add


def test_add_duplicate_skill():
    skill = make_skill(name="myskill")
    config = Configuration(skills={"myskill": skill})
    result = runner.invoke(
        app, ["add", "myskill", "tooltype", "--description", "desc"], obj=config
    )
    assert result.exit_code == 1
    assert "already exists" in result.output
