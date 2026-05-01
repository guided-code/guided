from typer.testing import CliRunner

from guided.skills.command import app

runner = CliRunner()


def test_list_no_skills(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "No skills found" in result.output


def test_list_shows_markdown_skills(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    skill_file = tmp_path / ".guided" / "skills" / "deploy" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)
    skill_file.write_text("# deploy\n\nShip the service to Kubernetes.\n")

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "deploy" in result.output
    assert "Ship the service to Kubernetes." in result.output


def test_add_skill_creates_markdown_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app, ["add", "myskill", "--description", "Run the local workflow."]
    )

    assert result.exit_code == 0
    skill_file = tmp_path / ".guided" / "skills" / "myskill" / "SKILL.md"
    assert skill_file.is_file()
    assert "Run the local workflow." in skill_file.read_text()


def test_add_duplicate_skill(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    skill_file = tmp_path / ".guided" / "skills" / "myskill" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)
    skill_file.write_text("# myskill\n\nExisting\n")

    result = runner.invoke(app, ["add", "myskill", "--description", "desc"])

    assert result.exit_code == 1
    assert "already exists" in result.output


def test_add_invalid_skill_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["add", "bad.name"])

    assert result.exit_code == 1
    assert "Invalid skill name" in result.output


def test_remove_skill(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    skill_dir = tmp_path / ".guided" / "skills" / "myskill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# myskill\n\nA skill\n")

    result = runner.invoke(app, ["remove", "myskill"])

    assert result.exit_code == 0
    assert "myskill" in result.output


def test_remove_skill_deletes_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    skill_dir = tmp_path / ".guided" / "skills" / "myskill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# myskill\n\nA skill\n")

    runner.invoke(app, ["remove", "myskill"])

    assert not skill_dir.exists()


def test_remove_nonexistent_skill(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["remove", "ghost"])

    assert result.exit_code == 1
    assert "not found" in result.output
