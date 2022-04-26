from contextlib import contextmanager
import shlex
import os
import subprocess

import pytest
from cookiecutter.utils import rmtree


@contextmanager
def inside_dir(dirpath):
    """
    Execute code from inside the given directory
    :param dirpath: String, path of the directory the command is being run.
    """
    old_path = os.getcwd()
    try:
        os.chdir(dirpath)
        yield
    finally:
        os.chdir(old_path)


@contextmanager
def bake_in_temp_dir(cookies, *args, **kwargs):
    """
    Delete the temporal directory that is created when executing the tests
    :param cookies: pytest_cookies.Cookies,
        cookie to be baked and its temporal files will be removed
    """
    result = cookies.bake(*args, **kwargs)
    try:
        yield result
    except Exception as e:
        import pprint
        pprint.pprint(result)
        pprint.pprint(e)
    finally:
        rmtree(str(result.project_path))


def run_inside_dir(command, dirpath):
    """
    Run a command from inside a given directory, returning the exit status

    Args:
        command: Command that will be executed
        dirpath: String, path of the directory the command is being run.

    Returns:

    """
    with inside_dir(dirpath):
        return subprocess.check_call(shlex.split(command))


def check_output_inside_dir(command, dirpath):
    """Run a command from inside a given directory, returning the command output"""
    with inside_dir(dirpath):
        try:
            output = subprocess.call(shlex.split(command))
        except subprocess.CalledProcessError as e:
            return e, output
    result = subprocess.run(
        shlex.split(command), cwd=dirpath, encoding="utf8", capture_output=True
    )
    return result.returncode, result.stdout, result.stderr


def project_info(result):
    """Get toplevel dir, project_slug, and project dir from baked cookies"""
    project_path = str(result.project_path)
    project_slug = os.path.split(project_path)[-1]
    project_dir = os.path.join(project_path, project_slug)
    return project_path, project_slug, project_dir


def test_bake_with_defaults(cookies):
    with bake_in_temp_dir(cookies) as result:
        assert result.project_path.isdir()
        assert result.exit_code == 0
        assert result.exception is None

        found_toplevel_files = [f.basename for f in result.project_path.listdir()]
        assert "setup.py" in found_toplevel_files


def test_bake_and_run_tests(cookies):
    with bake_in_temp_dir(cookies) as result:
        assert result.project_path.isdir()
        assert (
            run_inside_dir("pip install -r requirements/test.txt", str(result.project_path))
            == 0
        )
        returncode, stdout, stderr = check_output_inside_dir(
            "pytest", str(result.project_path)
        )
        if returncode != 0:
            print("test_bake_and_run_tests pytest error:", stdout, stderr)
            assert returncode == 0


def test_bake_withspecialchars_and_run_tests(cookies):
    """Ensure that a `full_name` with double quotes does not break setup.py"""
    with bake_in_temp_dir(
        cookies, extra_context={"full_name": 'name "quote" name'}
    ) as result:
        assert result.project_path.isdir()
        assert (
            run_inside_dir("pip install -r requirements/test.txt", str(result.project_path))
            == 0
        )
        returncode, stdout, stderr = check_output_inside_dir(
            "pytest", str(result.project_path)
        )
        if returncode != 0:
            print(
                "test_bake_withspecialchars_and_run_tests pytest error:", stdout, stderr
            )
            assert returncode == 0


def test_bake_with_apostrophe_and_run_tests(cookies):
    """Ensure that a `full_name` with apostrophes does not break setup.py"""
    with bake_in_temp_dir(cookies, extra_context={"full_name": "O'connor"}) as result:
        assert result.project_path.isdir()
        assert (
            run_inside_dir("pip install -r requirements/test.txt", str(result.project_path))
            == 0
        )
        returncode, stdout, stderr = check_output_inside_dir(
            "pytest", str(result.project_path)
        )
        if returncode != 0:
            print(
                "test_bake_with_apostrophe_and_run_tests pytest error:", stdout, stderr
            )
            assert returncode == 0
