"""The user interface for the chat client."""
from __future__ import annotations

import asyncio
import curses
import curses.textpad
import datetime
import os
import sys

from typing import TYPE_CHECKING

from chatfx.colors import COLORS
from chatfx.definitions import FormattedText
from chatfx.utils import scale_for_curses


if TYPE_CHECKING:
    from chatfx.output import Output


CTRLC = 3
CTRLS = 19
LF = 10
SPACE = 32
DELETE = 127
TILDE = 126


class Ui:
    """The main user interface."""

    def __init__(self: Ui) -> None:
        """Initialize the user interface."""
        self.textbox: curses.textpad.Textbox
        self.stdscr: curses.window
        self.textbox_win: curses.window
        self.clock_win: curses.window
        self.text: str = ""
        self.output: list[FormattedText] = []
        self.pad_pos: int
        self.lines: int = 0
        self.chat_send: callable[[str], None]

        self.stdscr = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        self._set_colors()
        curses.noecho()
        curses.curs_set(1)  # Show cursor
        curses.raw()

        # Enable mouse scrolling
        self.stdscr.keypad(True)  # noqa: FBT003
        self.stdscr.timeout(50)

    def _set_colors(self: Ui) -> None:
        """Set the colors for curses."""
        for color in COLORS:
            curses.init_color(
                color["id"],
                scale_for_curses(color["rgb"]["r"]),
                scale_for_curses(color["rgb"]["g"]),
                scale_for_curses(color["rgb"]["b"]),
            )
            curses.init_pair(color["id"], color["id"], -1)

    def init(self: Ui) -> None:
        """Initialize the user interface."""
        self.textbox_win = curses.newwin(2, self.cols, self.rows - 2, 0)
        self.textbox_win.keypad(True)  # noqa: FBT003
        self.clock_win = curses.newwin(1, self.cols, 0, 0)
        self.main_window = curses.newpad(10000, self.cols)
        self.main_window.scrollok(True)  # noqa: FBT003
        self.pad_pos = 0 if self.lines < self.mw_rows else self.lines - self.mw_rows

    @property
    def rows(self: Ui) -> int:
        """Get the number of rows in the terminal."""
        return self.stdscr.getmaxyx()[0]

    @property
    def cols(self: Ui) -> int:
        """Get the number of columns in the terminal."""
        return self.stdscr.getmaxyx()[1]

    @property
    def mw_rows(self: Ui) -> int:
        """Get the number of rows in the main window.

        Remove the clock line and the input line

        :returns: The number of rows available in the main window
        """
        return self.rows - 3

    def refresh_main_window(self: Ui) -> None:
        """Refresh the main window."""
        self.main_window.erase()
        lines = 0
        for entry in self.output:
            for line in entry.lines(width=self.cols):
                curses_line = line
                chars = 0
                for part in curses_line:
                    color_arg = part.color  # % curses.COLORS
                    cp = curses.color_pair(color_arg)
                    chars += len(part.string)
                    self.main_window.addstr(part.string, cp | part.decoration)
                self.main_window.addstr("\n")
                lines += chars // self.cols + 1

        if self.pad_pos == self.lines - self.mw_rows:
            self.pad_pos = lines - self.mw_rows
        self.lines = lines
        self.main_window.refresh(self.pad_pos, 0, 1, 0, self.mw_rows, self.cols)

    def refresh(self: Ui) -> None:
        """Refresh the user interface."""
        curses.curs_set(0)  # Hide cursor
        self.refresh_main_window()
        curses.curs_set(1)  # Show cursor

    async def clock(self: Ui) -> None:
        """Display the clock."""
        while True:
            curses.curs_set(0)  # Hide cursor
            location = curses.getsyx()
            max_y, max_x = self.stdscr.getmaxyx()
            now = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%H:%M:%S")
            self.clock_win.erase()
            self.clock_win.addstr(0, max_x - 9, now)
            self.clock_win.noutrefresh()
            curses.setsyx(location[0], location[1])
            curses.doupdate()
            curses.curs_set(1)
            await asyncio.sleep(0)

    def handle_command(self: Ui, text: str) -> None:
        """Handle a command."""
        if text in ("/quit", "/exit", "/q"):
            curses.endwin()
            sys.exit(0)
        if text in ("/clear", "/cls"):
            self.text = ""
            self.output = []
            self.refresh_main_window()
        if text.startswith(("/echo", "/e")):
            stripped = text.split(" ", 1)[1]
            self.output.append(FormattedText(content=stripped.splitlines()))
            self.refresh()
        if text.startswith("/restart"):
            curses.endwin()
            os.execv(sys.argv[0], sys.argv)

    async def run(self: Ui) -> None:  # noqa: C901
        """Run the user interface."""
        while True:
            char = await self.ainput()
            if char in (curses.KEY_ENTER, LF):
                if self.text.startswith("/"):
                    self.handle_command(self.text)
                elif self.text:
                    loop = asyncio.get_event_loop()
                    loop.create_task(self.chat_send(self.text))
                    await asyncio.sleep(0)
                self.text = ""
            elif char in (curses.KEY_BACKSPACE, DELETE):
                self.text = self.text[:-1]
            elif char == curses.KEY_RESIZE:
                self.init()
            elif char == curses.KEY_DOWN:
                if self.pad_pos < self.lines - self.mw_rows:
                    self.pad_pos += 1
            elif char == curses.KEY_UP:
                if self.pad_pos > 0:
                    self.pad_pos -= 1
            elif char >= SPACE and char <= TILDE:
                self.text += chr(char)
            elif char == CTRLC:
                self.handle_command("/quit")

            self.refresh_main_window()

            ml = (self.cols * 2) - 4  # >_ and last 2 cols
            show = self.text[-ml:] if len(self.text) > ml else self.text
            self.textbox_win.erase()
            self.textbox_win.addstr("> " + show)
            self.textbox_win.refresh()

    async def ainput(self: Ui) -> int:
        """Get input asynchronously."""
        await asyncio.sleep(0)
        return self.stdscr.getch()


async def run(output: Output, ui: Ui) -> None:
    """Run the user interface."""
    output.debug("Starting UI loop")

    loop = asyncio.get_event_loop()
    clock_task = loop.create_task(ui.clock())
    input_task = loop.create_task(ui.run())
    await asyncio.gather(clock_task, input_task)
