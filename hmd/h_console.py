from rich.console import Console
from rich.theme import Theme


class HConsole(object):
    def __init__(self):
        hmd_theme = Theme({
            "info": "dodger_blue2",
            "success": "green1",
            "warning": "orange_red1",
            "danger": "red1",
            "normal": "bright_white"
        })

        self.console = Console(theme=hmd_theme)

    def info(self, message: str) -> None:
        self.console.print(message, style="info")

    def success(self, message: str) -> None:
        self.console.print(message, style="success")

    def warning(self, message: str) -> None:
        self.console.print(message, style="warning")

    def danger(self, message: str) -> None:
        self.console.print(message, style="danger")

    def print(self, message: str) -> None:
        self.console.print(message, style="normal")