import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from autovid.common import retry

sys.coinit_flags = 2  # Single-threaded COM helps with stability

from pywinauto import Application, Desktop, WindowSpecification, findwindows

lg = logging.getLogger(__name__)


class VERINT:
    """
    A class used to help manipulate the VERINT UI using WIN32 + UIA COM commands

    Methods
    -------
    login()
        Clicks the login button at the initial VERINT application launch. Assumes prefilled + AD login
    reset_state()
        Culls all Dashboard and Video UI elements to reduce memory usage, speed execution, and provide consistent state for automation
    select_site()
        Select the specific site used for analysis
    site_time_range()
        Sets the time range for the video
    save_image()
        Saved an copy of the image
    """

    def __init__(
        self,
        outdir: Path | str,
        verint_path: Path | str = Path(
            r"C:\\Program Files (x86)\\Verint\\Video Investigator"
        ),
        verint_exe: str = r"Verint.VideoInvestigator.exe",
        verint_title: str = r"Video Inspector",
    ) -> None:
        """
        Parameters
        ----------

        outdir: Path | str
            Output directory of images / videos
        verint_path: Path | str, optional
            Location in Windows of the VERINT application directory
        verint_exec: str, optional
            Name of VERINT application executable located in application directory
        verint_title:  str, optionai
            Application title. Used to find multiple instances of VERINT.
        """

        if isinstance(verint_path, str):
            verint_path = Path(verint_path)

        self.verint_path: Path = verint_path
        self.verint_exe: str = verint_exe
        self.verint_title: str = verint_title
        self.verint_full_path: Path = self.verint_path / self.verint_exe

        self.outdir: Path | str | None = outdir

        self.app: Application = None
        self.verint: WindowSpecification = None

        self._chk_exec()

    def _chk_exec(self) -> None:
        lg.info(f"Checking if executable exists at: {self.verint_full_path}")
        if not self.verint_full_path.exists():
            raise FileNotFoundError(
                f"Unable to find VERINT executable at: {self.verint_full_path}"
            )

        self._chk_multi_instances()

    def init_app(self, wm: tuple[int, int, int, int] | None = None) -> None:
        app = Application(backend="uia").start(
            cmd_line=str(self.verint_full_path), work_dir=str(self.verint_path)
        )

        app.wait_cpu_usage_lower(threshold=5, timeout=30)
        verint: WindowSpecification = app.VideoInspect

        if wm:
            verint.move_window(
                x=wm[0],
                y=wm[1],
                width=wm[2],
                height=wm[3],
            )

        self.app = app
        self.verint = verint

    @retry(max_retries=5, wait_time=5)
    def login(self) -> None:
        self.verint.set_focus()
        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)
        login_button = self._ret_login_button()

        if login_button.is_visible():
            login_button.click()

    def _kill_app(self, restart: bool = False) -> None:
        lg.info("Killing VERINT instance.")
        try:
            self.app.kill()
        except Exception as err:
            lg.error("Failed to stop VERINT instance. Please kill it manually.")
            raise err
        else:
            self.app = None
            self.verint = None

        if restart:
            lg.info("Restarting VERINT. Please wait...")
            self._chk_exec()

    def _chk_multi_instances(self, clear: bool = True) -> None:
        lg.info("Checking for multiple instances of VERINT..")
        instances = Desktop(backend="uia").windows(title=self.verint_title)

        if len(instances) > 0:
            if not clear:
                raise SystemError(
                    f"Found {len(instances)} VERINT instances but expected none. Close all VERINT instances and try again..."
                )

            lg.info(f"Killing {len(instances)} instances of VERINT.")
            for instance in instances:
                pid = instance.process_id()
                inst_process = Application(backend="uia").connect(process=pid)
                inst_process.kill()

    @retry(max_retries=10, wait_time=1)
    def _ret_login_button(self) -> WindowSpecification:
        out_val = (
            self.verint.children(class_name="TabControl")[0]
            .children()[0]
            .children(class_name="LoginDialog")[0]
            .children(title="Login")[0]
        )

        return out_val

    @retry(max_retries=10, wait_time=1)
    def _ret_video_tab(self) -> WindowSpecification:
        out_val = self.verint.children(class_name="TabControl")[0].children(
            class_name="TabItem"
        )[1]

        return out_val

    @retry(max_retries=10, wait_time=1)
    def _ret_verint_tab(self) -> WindowSpecification:
        out_val = self.verint.children(class_name="TabControl")[0].children(
            class_name="TabItem"
        )[0]

        return out_val

    @retry(max_retries=10, wait_time=1)
    def _ret_video_tabcontainer(self) -> WindowSpecification:
        out_val = (
            (self._ret_video_tab())
            .children(class_name="VideoTabControl")[0]
            .children()[1]
            .children(class_name="VideoRequest")[0]
        )

        return out_val

    @retry(max_retries=10, wait_time=1)
    def _ret_searchbox(self) -> WindowSpecification:
        out_val = (self._ret_verint_tab()).children(class_name="TextBox")[0]

        return out_val

    @retry(max_retries=3, wait_time=5)
    def reset_state(self) -> None:
        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)

        verint_tab = self._ret_verint_tab()
        video_tab = self._ret_video_tab()

        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)
        self.verint.set_focus()
        video_tab.click_input()
        self._clear_tabs()

        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)
        self.verint.set_focus()
        verint_tab.click_input()
        self._clear_dashboard()

    def _clear_dashboard(self) -> None:
        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)

        self.verint.set_focus()
        (self._ret_verint_tab()).click_input()

        cards_menu = (
            (self._ret_verint_tab())
            .children(class_name="Menu")[0]
            .children(class_name="MenuItem")[0]
        )

        if (self._ret_searchbox()).is_visible():
            self.verint.set_focus()
            (self._ret_searchbox()).click_input()
            (self._ret_searchbox()).type_keys(r"^a {BACKSPACE}")  # Ctrl+A and Backspace

        if cards_menu.is_visible():
            self.verint.set_focus()
            cards_menu.click_input()
            time.sleep(1)
            cards_menu.type_keys(r"{DOWN}{DOWN}{ENTER}")

    def _clear_tabs(self) -> None:
        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)
        video_tab = self._ret_video_tab()

        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)
        open_tabs = (
            video_tab.parent()
            .children()[1]
            .children()[0]
            .children()[1]
            .children(class_name="VideoTabItem")
        )

        for open_tab in open_tabs:
            self.verint.set_focus()
            close_btn = open_tab.children(class_name="Button")[0]
            close_btn.click_input()
            time.sleep(1)

        sidebar = (
            (self._ret_video_tab())
            .children(class_name="VideoTabControl")[0]
            .children(class_name="Expander")[0]
            .children(class_name="DvrTree")[0]
        )

        workspace_tab = sidebar.children(class_name="TabControl")[0].children(
            class_name="TabItem"
        )[1]
        workspace_tab.click_input()

        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)
        open_workspaces = (
            workspace_tab.children(class_name="ScrollViewer")[0]
            .children(class_name="TreeView")[0]
            .children(
                class_name="TreeViewItem",
                title="Verint.Database.WrapperClasses.DvrNode",
            )
        )

        for open_workspace in open_workspaces:
            open_workspace.children(class_name="Menu")[0].click_input()
            open_workspace.set_focus()
            open_workspace.type_keys(r"{DOWN}{DOWN}{DOWN}{DOWN}{ENTER}")
            time.sleep(1)

    @retry(max_retries=2, wait_time=2)
    def select_site(self, site_id: str) -> None:
        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)

        (self._ret_searchbox()).type_keys(
            r"^a {BACKSPACE}" + str(site_id) + r"{ENTER}", with_spaces=True
        )  # Don't use f-strings

        returned_results = (
            (self._ret_verint_tab())
            .children(class_name="ListView")[0]
            .children(class_name="ListBoxItem")
        )

        # TODO: Add logic for graceful Exceptionfor 0 results
        if len(returned_results) != 1:
            raise ValueError(
                f"The site_id: {site_id} returned more than 1 result or none..."
            )

        returned_result = returned_results[0]
        site_result = returned_result.children(class_name="Expander")[0]
        site_btn = site_result.children(class_name="Button")[0]

        site_btn.toggle()
        request_video = site_result.children(class_name="ListBox")[0].children(
            class_name="ListBoxItem"
        )[0]

        request_video.click_input()

    def set_time_range(self, event_dt: datetime, event_td_range: timedelta) -> None:
        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)
        prompt1_text = f"{(event_dt - event_td_range).strftime('%x %H:%M')} to {(event_dt + event_td_range).strftime('%x %H:%M')}"

        video_tabcontainer = self._ret_video_tabcontainer()
        datebox = video_tabcontainer.children(
            class_name="Expander", title="Recorded Video"
        )[0].children(class_name="TextBox")[0]

        datebox.set_focus()
        datebox.click_input()
        datebox.type_keys(
            r"^a {BACKSPACE}" + str(prompt1_text) + r"{SPACE}{BACKSPACE}",
            with_spaces=True,
        )

        datebox.click_input()
        datebox.set_focus()
        datebox.type_keys(r"{SPACE}{BACKSPACE}")  # Help prevents edge case

    @retry(max_retries=3, wait_time=1)
    def select_camera(self, camera_name: str) -> None:
        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)

        video_tabcontainer = (
            (self._ret_video_tab())
            .children(class_name="VideoTabControl")[0]
            .children()[1]
            .children(class_name="VideoRequest")[0]
        )

        camera_pane = video_tabcontainer.children(class_name="ScrollViewer")[0]
        camera_textbox = camera_pane.children(class_name="TextBox")[0]

        camera_textbox.type_keys(
            r"^a {BACKSPACE}" + str(camera_name) + r"{ENTER}", with_spaces=True
        )

        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)
        camera_button = camera_pane.children(class_name="ListBox")[0].children(
            class_name="ListBoxItem"
        )[0]

        self.verint.set_focus()
        camera_button.click_input()

    def click_recorded_button(self) -> None:
        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)
        time.sleep(2)
        recorded_button = (
            (self._ret_video_tabcontainer())
            .children(class_name="Expander", title="Recorded Video")[0]
            .children(class_name="Button")[1]
        )

        recorded_button.set_focus()
        recorded_button.input_click()

    @retry(max_retries=3, wait_time=15)
    def videoview(self) -> None:
        # TODO: Actual error handling...
        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)

        # TODO: Below does full search and take too long.. Need to rewrite...
        video_notfound = self.verint.child_window(
            title="Video not found", control_type="Text", found_index=0, depth=3
        )

        if video_notfound.exists():
            raise FileNotFoundError("Video could not be found")

        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)
        dvr_player = (
            (self._ret_video_tab())
            .children()[0]
            .children()[1]
            .children(class_name="DvrVideoPlayer")[0]
        )

        dvr_player.set_focus()
        dvr_player.type_keys(r"{SPACE}")

        # TODO: Map all buttons later...
        skiptobeginning = dvr_player.children(class_name="Button")[6]
        skiptobeginning.click_input()

    @retry(max_retries=3, wait_time=1)
    def save_image(self, fl_name: str | None = None, overwrite: bool = True) -> None:
        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)

        img_hwnd = self.verint.children(class_name="Window", title="Save Image")[0]
        flname_textbox = img_hwnd.children(class_name="ExportFrameDialog")[0].children(
            class_name="TextBox"
        )[0]

        if not self.outdir.exists():
            raise FileNotFoundError(
                f"Image output directory does not exist: {self.outdir}"
            )

        # Use the auto generated name
        if not fl_name:
            fl_name = flname_textbox.texts()[0]

        full_flname: Path = self.outdir / str(fl_name) / ".jpg"
        if full_flname.exists() and not overwrite:
            raise ValueError(
                f"{full_flname} exists already but you disabled overwriting..."
            )

        # Using this keyboard sequence is faster than finding + filling each field window
        # More error-prine unfortunately
        img_hwnd.set_focus()
        img_hwnd.type_keys(
            "{TAB}{TAB}"
            + "^a{BACKSPACE}"
            + str(fl_name)
            + "{TAB}{DOWN}{DOWN}"
            + "{TAB}^a{BACKSPACE}"
            + str(self.outdir)
            + "{TAB}{TAB}"
            + "{SPACE}"
            + "{TAB}{TAB}{TAB}"
            + "{ENTER}",
            with_spaces=True,
        )

        try:
            overwrite_prompt = (
                Desktop(backend="uia")
                .window(title="", class_name="Popup", depth=1)
                .children()[0]
                .children(class_name="Button", title="Yes")[0]
            )

            if overwrite_prompt.is_visible():
                overwrite_prompt.click_input()

        except findwindows.ElementNotFoundError:
            pass

    @retry(max_retries=3, wait_time=10)
    def export_image_click(self) -> None:
        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)

        dvr_player = (
            (self._ret_video_tab())
            .children()[0]
            .children()[1]
            .children(class_name="DvrVideoPlayer")[0]
        )

        vid_menu = (
            dvr_player.children(class_name="VideoContainer")[0]
            .children(class_name="Menu")[0]
            .children()[0]
        )

        dvr_player.set_focus()
        vid_menu.click_input()

        self.app.wait_cpu_usage_lower(threshold=5, timeout=30)
        Desktop(backend="uia").window(title="", class_name="Popup").child_window(
            class_name="TextBlock", title="Export Image", depth=5
        ).click_input()
