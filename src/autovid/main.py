import logging
import math
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from threading import Event, Thread

from autovid.common import term2site
from autovid.overlay import Overlay
from autovid.verint import VERINT

lg = logging.getLogger(__name__)
kill_thread = Event()


class AutoVid(VERINT):
    def __init__(
        self,
        term_id: str,
        tran_dt: datetime,
        lookback_buffer: timedelta | int | None = timedelta(seconds=5),
        jira_id: str | None = None,
        outdir: Path | str | None = None,
        w_percent: int = 80,
    ) -> None:
        super().__init__(outdir=outdir)

        if isinstance(lookback_buffer, int):
            lookback_buffer = timedelta(seconds=lookback_buffer)

        self.term_id = term_id
        self.tran_dt = tran_dt
        self.lookback_td = lookback_buffer
        self.jira_id = jira_id
        self.w_percent = w_percent

        if not (50 <= w_percent <= 80):
            raise ValueError(f"w_percent value {w_percent} should be between 50 and 80")

    def start_overlay(self) -> None:
        global kill_thread
        overlay_width = math.floor(100 - self.w_percent)
        self.overlay = Overlay(w_percent=overlay_width)
        self.overlay.after(5000, self._start_thread, self.overlay)
        self.overlay.mainloop()
        kill_thread.set()

    def _start_thread(self, overlay_obj: Overlay) -> None:
        self.thread = Thread(target=self.pull_image, args=(overlay_obj,), daemon=True)
        self.thread.start()

    def pull_image(self, overlay_obj: Overlay | None = None) -> None:
        def update_status(msg: str):
            if overlay_obj:
                if kill_thread.is_set():
                    raise ConnectionAbortedError("Command to Kill Thread Received")

                status_label: tk.StringVar = overlay_obj.status_label
                status_label.set(msg)

            lg.info(msg)

        try:
            update_status("Querying Database To Convert ATM ID to SITE Name")
            site_id = term2site(self.term_id)
            if not site_id:
                raise ValueError(
                    f"Could not return a valid site from: {self.term_id}. Please double check the value"
                )
            update_status(f"Linked Terminal: {self.term_id} to {site_id}")

            update_status("Starting VERINT. Please wait...")
            self.init_app()

            update_status("Finding and Clicking Login Button")
            self.login()

            update_status("Resetting the State")
            self.reset_state()

            update_status(f"Found Site: {site_id}")
            self.select_site(site_id)

            update_status(f"Finding DVR Camera: {self.term_id}")
            self.select_camera(camera_name=self.term_id)

            update_status("Input Datetime Range")
            self.set_time_range(event_dt=self.tran_dt, event_td_range=self.lookback_td)

            update_status("Clicking the Recorded Button")
            self.click_recorded_button()

            update_status("Pulling Up Video. Please wait...")
            self.videoview()

            update_status("Starting the Export Image Process")
            self.export_image_click()

            update_status("Saving the Image to {self.outdir}")
            self.save_image()

            update_status("Resetting State")
            self.reset_state()

        except KeyboardInterrupt as err:
            raise err

        except Exception as err:
            raise err

        else:
            update_status("Successfully Finished Execution...")
            lg.info("Finish pulling the image...")

        finally:
            if overlay_obj:
                self.overlay.destroy()
                lg.info("Successfully destroyed thread")
