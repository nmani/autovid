import logging as lg
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from autovid.main import AutoVid

load_dotenv()

lg.basicConfig(level=lg.DEBUG)

# Single Camera Query
example = AutoVid(
    term_id="terminal-id", tran_dt=datetime.now(), outdir=Path().cwd() / "output"
)

# example.start_overlay()
example.pull_image()
