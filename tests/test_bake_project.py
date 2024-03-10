from pathlib import Path

import pytest
from pytest import param

from tests.utils import (
    bake_in_temp_dir,
    run_precommit,
    run_project_tests,
    template_dirs,
)


@pytest.mark.parametrize(["template_dir"], template_dirs(), ids=lambda x: x.name)
@pytest.mark.parametrize(
    ["extra_context"],
    [
        param({}, id="default"),
        param({"full_name": 'name "quote" name'}, id="with-special-chars"),
        param({"full_name": "O'connor"}, id="with-apostrophe"),
    ],
)
def test_bake(cookies, template_dir: Path, extra_context: dict):
    """Test baking all the templates with different context overrides."""
    with bake_in_temp_dir(
        cookies, template_dir=template_dir, extra_context=extra_context
    ) as result:
        if result.exception:
            print(result.exception)
        assert result.exit_code == 0
        assert result.exception is None
        assert result.project_path.is_dir()

        run_project_tests(result.project_path)
        run_precommit(result.project_path, tool=extra_context.get("packaging_tool", "pip"))
