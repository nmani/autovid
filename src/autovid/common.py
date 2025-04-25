import logging
import os
import time
from typing import Any, Callable

import pandas as pd

lg = logging.getLogger(__name__)


class LocalConfig:
    # TODO: Add logic for other methods of config... you should probably use load_env().
    def __init__(self) -> None:
        min_env = ["AUTOVID_DB_CONN_STRING"]

        if not all([x in os.environ for x in min_env]):
            raise ValueError(
                f"Requires these minimum environmental variables to be set: {min_env}"
            )

    @property
    def CONN_STRING(self) -> str:
        if not (outvar := os.getenv("AUTOVID_DB_CONN_STRING")):
            raise ValueError("You shouldn't have arrived here...")

        return outvar


def term2site(term_str: str | list[str] | set[str]) -> str | None:
    config = LocalConfig()
    conn_string = config.CONN_STRING

    # TODO: Come back to this later...
    if isinstance(term_str, (list, set)):
        raise ValueError("Haven't implemented this year... come back later.")

    # TODO: VERINT only supports SQL Server + sqlite. No one uses sqllite but should abstract this to ORM models for more complex logic?
    # TODO: Fix not safe code...
    sql = """SELECT InUse, DvrCamera_ID, Dvr_ID, [Name], B.SiteName, B.LocationId, B.AddressStreet, B.AddressCity, B.PostalCode, B.AddressState, B.AddressCountry FROM DvrCameras as A LEFT JOIN Sites as B ON A.Dvr_ID = B.ID WHERE A.[Name] LIKE '%{}%';
    """.format(term_str)

    try:
        output: pd.DataFrame = pd.read_sql(sql, con=conn_string)
    except Exception as err:
        raise err

    match len(output):
        case 0:
            return None
        case 1:
            return str(output.to_dict(orient="records")[0]["SiteName"]).strip()
        case _:
            raise ValueError(f"{term_str} return greater than 1 value... {output}")


# TODO: add wraps() later for retry
def retry(max_retries: int = 3, wait_time: int = 5):
    def decorator(func: Callable[[Any, Any], Any]) -> Any:
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            if retries < max_retries:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as err:
                    retries += 1
                    lg.warning(
                        f"Retrying {func} in {wait_time} seconds due to error {err}"
                    )
                    time.sleep(wait_time)
            else:
                raise Exception(
                    f"Max retries ({max_retries}) for function {func} exceeded."
                )

        return wrapper

    return decorator
