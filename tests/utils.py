import functools
import os
import pprint
import shlex
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Tuple, List

from cookiecutter.utils import rmtree
from pytest_cookies.plugin import Cookies, Result


@contextmanager
def inside_dir(dir_path: Path):
    """
    Execute code from inside the given directory.

    Args:
        dir_path: Path of the directory the command is being run.
    """
    old_path = os.getcwd()
    try:
        os.chdir(dir_path)
        yield
    finally:
        os.chdir(old_path)


@contextmanager
def bake_in_temp_dir(
    cookies: Cookies, template_dir: Path, extra_context: Optional[dict] = None
) -> Result:
    """
    Delete the temporal directory that is created when executing the tests.

    Args:
        cookies: cookie to be baked and its temporal files will be removed
        template_dir: Template directory
        extra_context: Keyword argument that will be passed to cookiecutter

    Yields:
        The cookie fixture result
    """
    result = cookies.bake(template=str(template_dir), extra_context=extra_context)
    try:
        yield result
    except Exception as e:
        pprint.pprint(result)
        pprint.pprint(e)
        raise e
    finally:
        rmtree(str(result.project_path))


def run_inside_dir(command: str, dir_path: Path, split_cmd=True) -> subprocess.CompletedProcess:
    """
    Run a command from inside a given directory, returning the exit status.

    Args:
        command: Command that will be executed
        dir_path: String, path of the directory the command is being run.
        split_cmd: Split the command in an argument list

    Returns:
        The return code from executing command
    """
    with inside_dir(dir_path):
        cmd = shlex.split(command) if split_cmd else command
        return subprocess.run(cmd, shell=True, check=True)


def check_output_inside_dir(command: str, dir_path: Path, split_cmd=True) -> Tuple:
    """Run a command from inside a given directory, returning the command output"""
    cmd = shlex.split(command) if split_cmd else command
    result = subprocess.run(
        cmd, cwd=dir_path, encoding="utf8", capture_output=True
    )
    return result.returncode, result.stdout, result.stderr


def project_info(result):
    """Get toplevel dir, project_slug, and project dir from baked cookies"""
    project_path = str(result.project_path)
    project_slug = os.path.split(project_path)[-1]
    project_dir = os.path.join(project_path, project_slug)
    return project_path, project_slug, project_dir


def run_precommit(project_path, tool: str):
    """Run pre-commit tests in the generated project."""
    gitignore = Path(project_path) / ".gitignore"
    gitignore.touch(exist_ok=True)
    with gitignore.open("a") as f:
        f.write("venv\n")

    if not Path(project_path).joinpath("venv").exists():
        install_venv(project_path, tool)

    returncode, stdout, stderr = check_output_inside_dir(f"{project_path}/venv/bin/python -m pip install pre-commit", project_path)

    if returncode != 0:
        print(stdout)
        print(stderr)
        assert returncode == 0
    # pre-commit needs to be run inside a git repo
    returncode, stdout, stderr = check_output_inside_dir("git init", project_path)
    if returncode != 0:
        print(stdout)
        assert returncode == 0
    returncode, stdout, stderr = check_output_inside_dir("git add .", project_path)
    if returncode != 0:
        print(stdout)
        assert returncode == 0
    returncode, stdout, stderr = check_output_inside_dir(
            f"./venv/bin/pre-commit install -c {PRE_COMMIT_CONFIG}", project_path
        )
    if returncode != 0:
        print(stdout)
        assert returncode == 0

    returncode, stdout, stderr = check_output_inside_dir(
        f"./venv/bin/pre-commit run -c {PRE_COMMIT_CONFIG} --all-files", project_path
    )

    if returncode != 0:
        print(stdout)
        assert returncode == 0


def run_project_tests(project_path: Path, tool="pip"):
    """Run the generated project's tests."""
    install_venv(project_path, tool)


    if tool.lower() == "pip":
        if not (project_path / "requirements" / "test.txt").exists():
            return
        cmd = "./venv/bin/python -m pip install -r requirements/test.txt"
        print("  - Installing test requirements with pip...")
        print(f"    {cmd}\n")
        assert run_inside_dir(cmd, project_path).returncode == 0
        test_cmd = "pytest"
    elif tool.lower() == "poetry":
        print("  - Installing poetry...")
        cmd = f"{project_path}/bin/python -m pip install -U poetry"
        print(f"    {cmd}\n\n")
        assert run_inside_dir(cmd, project_path).returncode == 0

        print("  - Installing test requirements with poetry...")
        cmd = "./venv/bin/poetry install --with test"
        print(f"    {cmd}\n\n")
        returncode, stdout, stderr = check_output_inside_dir(cmd, project_path)
        print(stdout)
        print(stderr)
        assert returncode == 0
        test_cmd = "./venv/bin/poetry run pytest"
    else:
        return

    print("\n  - Baked project layout\n")
    print(run_inside_dir("ls", project_path).stdout)

    print(f"\n  - Running tests with {test_cmd}...\n\n")
    returncode, stdout, stderr = check_output_inside_dir(test_cmd, project_path)
    print(stdout)
    print(stderr)
    assert returncode == 0


def install_venv(project_path, tool):
    print(f"\nTesting project {project_path} with {tool}...\n")
    print("  - Installing venv...")
    venv_location = project_path / "venv"
    returncode, stdout, stderr = check_output_inside_dir(f"python -m venv {venv_location}", project_path)

    if returncode != 0:
        print(stdout)
        print(stderr)
        assert returncode == 0
    assert venv_location.exists()


PRE_COMMIT_CONFIG = Path(__file__).parent / "pre-commit-config-testing.yaml"


@functools.lru_cache
def template_dirs() -> List[Tuple[Path]]:
    """Find the cookiecutter templates in the repo."""
    root_path = Path(__file__).parent.parent
    return [
        (p,)
        for p in root_path.glob("cookiecutter-*")
        if p.is_dir() and (p / "cookiecutter.json").exists()
    ]
