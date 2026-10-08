from pathlib import Path
import subprocess

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QMessageBox


def installed_version():
    result = subprocess.run(
        ["/usr/bin/rpm", "-q", "--qf", "%{EVR}", "nimvex"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode:
        raise RuntimeError("The installed Nimvex RPM could not be identified.")
    return result.stdout.strip()


class Updater:
    def __init__(self, browser, root=None):
        self.browser = browser
        self.process = None
        self.phase = None
        self.before = None
        self.restarted_needed = False
        self.action = browser.browser_menu.addAction(
            "Check for updates…", self.open
        )

    def message(self, title, text, warning=False):
        method = QMessageBox.warning if warning else QMessageBox.information
        method(self.browser, title, text)

    def open(self):
        if self.process is not None:
            self.message("Nimvex updates", "An update operation is already running.")
            return
        if self.restarted_needed:
            self.message("Nimvex updates", "Quit and reopen Nimvex to use the update.")
            return
        if not Path("/etc/yum.repos.d/nimvex.repo").is_file():
            self.message(
                "Update repository missing",
                "The official Nimvex update repository is not configured. "
                "Use the official release installation instructions.",
                warning=True,
            )
            return
        try:
            self.before = installed_version()
        except Exception as error:
            self.message("Nimvex updates", str(error), warning=True)
            return
        self.launch(
            "check", "/usr/bin/dnf",
            ["--refresh", "check-upgrade", "nimvex"],
        )

    def launch(self, phase, program, arguments):
        self.phase = phase
        self.action.setEnabled(False)
        self.action.setText(
            "Checking for updates…" if phase == "check"
            else "Refreshing update information…" if phase == "refresh"
            else "Installing update…"
        )
        process = QProcess(self.browser)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.finished.connect(
            lambda code, status, p=process: self.finished(p, code, status)
        )
        process.errorOccurred.connect(
            lambda error, p=process: self.failed(p, error)
        )
        self.process = process
        process.start(program, arguments)

    def reset(self, process):
        if self.process is not process:
            return
        self.process = None
        self.action.setEnabled(True)
        self.action.setText("Check for updates…")
        process.deleteLater()

    def failed(self, process, error):
        if self.process is not process:
            return
        if error == QProcess.ProcessError.FailedToStart:
            detail = process.errorString()
            self.reset(process)
            self.message("Update operation failed", detail, warning=True)

    def finished(self, process, code, status):
        if self.process is not process:
            return
        phase = self.phase
        output = bytes(process.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        ).strip()
        self.reset(process)

        normal = status == QProcess.ExitStatus.NormalExit
        if phase == "check" and normal and code == 0:
            self.message("Nimvex updates", "No Nimvex update is currently available.")
            return

        if phase == "check" and normal and code == 100:
            answer = QMessageBox.question(
                self.browser,
                "Nimvex update available",
                "An update is available. Install it now?\n\n"
                "System authentication may be required. Keep Nimvex and "
                "your computer running until the operation finishes.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.launch("refresh", "/usr/bin/pkcon",
                            ["--noninteractive", "refresh", "force"])
            return

        if not normal or code != 0:
            self.message(
                "Update operation did not complete",
                (output[-6000:] or f"Operation exited with code {code}.")
                + "\n\nNo successful update was confirmed.",
                warning=True,
            )
            return

        if phase == "refresh":
            self.launch("install", "/usr/bin/pkcon",
                        ["--noninteractive", "update", "nimvex"])
            return

        try:
            after = installed_version()
        except Exception as error:
            self.message("Could not verify installation", str(error), warning=True)
            return

        if after != self.before:
            self.restarted_needed = True
            self.action.setText("Update installed — restart Nimvex")
            self.message(
                "Nimvex updated",
                f"Installed package: {after}\n\n"
                "Quit Nimvex from its menu, then reopen it to use the update.",
            )
        else:
            self.message(
                "Nimvex updates",
                "The operation finished, but the installed package version "
                "did not change. No new installation was confirmed.",
            )
