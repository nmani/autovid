from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def tmp_conf(tmp_path_factory) -> Path:
    tmp_dir = tmp_path_factory.mktemp("config")
    out_fl = tmp_dir / "config.yml"

    with out_fl.open("w") as f:
        f.write(
            r'CONN_STRING="mssql+pyodbc://server:port/dbname?trusted_connection=yes&driver=SQL+Server"'
        )

    return out_fl


@pytest.fixture()
def _env() -> None:
    pass


def test_config() -> None:
    pass
