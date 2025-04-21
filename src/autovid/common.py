import logging
import time
from typing import Any, Callable

import pandas as pd

lg = logging.getLogger(__name__)

# TODO: add wraps() later for retry


class LocalConfig:
    def __init__(self) -> None:
        # Order of oops
        # Check for file config values
        #
        ...

    def CONN_STRING(self) -> str:
        return ""


def term2site(term_str: str | list[str] | set[str]) -> str | None:
    config = LocalConfig()
    conn_string = config.CONN_STRING

    # TODO: Come back to this later...
    if isinstance(term_str, (list, set)):
        raise ValueError("Haven't implemented this year... come back later.")

    sql = """SELECT InUse, DvrCamera_ID, Dvr_ID, [Name], B.SiteName, B.LocationId, B.AddressStreet, B.AddressCity, B.PostalCode, B.AddressState, B.AddressCountry FROM DvrCameras as A LEFT JOIN Sites as B ON A.Dvr_ID = B.ID WHERE A.[Name] LIKE '%{}%';
    """.format(term_str)

    try:
        output: pd.DataFrame = pd.read_sql(sql, conn=conn_string)
    except Exception as err:
        raise err

    match len(output):
        case 0:
            return None
        case 1:
            return str(output.to_dict(orient="records")[0]["SiteName"]).strip()
        case _:
            raise ValueError(f"{term_str} return greater than 1 value... {output}")


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
