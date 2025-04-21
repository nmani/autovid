import logging as lg
from datetime import datetime
from pathlib import Path

from autovid.main import AutoVid

lg.basicConfig(level=lg.DEBUG)

# Single Camera Query
example = AutoVid(
    terminal_id="adfasdf", tran_dt=datetime.now(), outdir=Path().cwd() / "output"
)

example.start_overlay()
