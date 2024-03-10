"""Test that the FastAPI composition works."""
import pathlib

from cookie_composer.commands import create

from tests.utils import run_project_tests, run_precommit

root_dir = pathlib.Path(__file__).parent.parent.resolve()


def test_bake(tmp_path: pathlib.Path):
    template_path = root_dir / "package-composition.yaml"

    project_path = create.create_cmd(str(template_path), tmp_path, no_input=True, overwrite_if_exists=True)

    assert project_path.is_dir()

    run_project_tests(project_path)
    run_precommit(project_path, tool="pip")
