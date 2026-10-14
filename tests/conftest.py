"""Run every test twice: against the generated database and the built-in lists."""

import pytest

from argus import data


@pytest.fixture(autouse=True, params=["database", "fallback"])
def data_source(request):
    if request.param == "database" and not data.DB_PATH.is_file():
        pytest.skip("argus.db not built (run make data)")
    data.use_database(data.DB_PATH if request.param == "database" else None)
    yield request.param
    data.use_database()
