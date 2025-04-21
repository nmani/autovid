# AutoVid - VERINT GUI Automation Tool

## Overview

VERINT Video Investigator is a tool used to access and view DVR footage. This tool is designed to automate the more tedious parts of VERINT used GUI automation.

This tool works by emulating mouse and keyboards inputs on the GUI itself. It's a blocking process meaning you cannot use your device while it's running it's workflow though we provide a mechanism to abort the current workflow.

## Minimum Requirements
1) Properly installed and configured VERINT VI application
2) Python 3.12+
3) The uv tool
    > pip install --user uv

## Basic Installation

```bash
uv pip install git@https://github.com/nmani/autovid
```

## Examples

### Single Terminal Lookup 

```python
from datetime import datetime
from pathlib import Path

from autovid.main import AutoVid

example = AutoVid(
    term_id = "terminal-name",
    tran_dt = datetime.now(),
    outdir = Path(r"C:\\TEMP\\TESTING")
)
```

### Batch Terminal Lookup (TBD) - Experimental

### Site Survey (TBD) - Experimental

This will query multiple cameras based ona regex within a singel site based on a specific time or time range.

## Face Extraction (TDB) - Experimental

Will extract faces and save them into a database

### Design Considerations

Searching the entire tree for a WindowSpecification is very slow. It's MUCH MUCH faster to emurate down a specific tree path which is what is done here. If there's a updates to to the VERINT UI, this might cause issues 
