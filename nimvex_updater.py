import json
import os
import subprocess
import time
from pathlib import Path

from PySide6.QtCore import QDateTime, QStandardPaths, QThread, QTimer, Signal
from PySide6.QtWidgets import (QDateTimeEdit, QDialog, QDialogButtonBox,
    QLabel, QMessageBox, QPushButton, QVBoxLayout)

WARNING = "Keep your computer on while updating. Internet access is required to download updates."
REMOTE = "git@github.com:HexandRoach/nimvex.git"


class GitJob(QThread):
    done = Signal(bool, str)

    def __init__(self, root, install, parent):
        super().__init__(parent)
        self.root, self.install = root, install

    def git(self, *args):
        env = dict(os.environ, GIT_TERMINAL_PROMPT="0",
                   GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=15")
        result = subprocess.run(["git", *args], cwd=self.root, env=env,
            capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Git command failed")
        return result.stdout.strip()

    def run(self):
        try:
            if Path(self.git("rev-parse", "--show-toplevel")).resolve() != self.root:
                raise RuntimeError("Not running from the Nimvex repository root.")
            if self.git("remote", "get-url", "origin") != REMOTE:
                raise RuntimeError("Unexpected update repository. Update refused.")
            if self.git("branch", "--show-current") != "main":
                raise RuntimeError("Updates require the main branch.")
            if self.git("status", "--porcelain"):
                raise RuntimeError("Local changes detected. Commit or save them before updating.")
            self.git("fetch", "--no-tags", "origin", "main")
            target = self.git("rev-parse", "FETCH_HEAD")
            current = self.git("rev-parse", "HEAD")
            if current == target:
                self.done.emit(True, "current")
                return
            self.git("merge-base", "--is-ancestor", current, target)
            if self.install:
                if self.git("status", "--porcelain") or self.git("rev-parse", "HEAD") != current:
                    raise RuntimeError("Local files changed during download. Update refused.")
                self.git("-c", "core.hooksPath=/dev/null", "merge", "--ff-only", target)
                self.done.emit(True, "installed")
            else:
                self.done.emit(True, "available")
        except Exception as error:
            self.done.emit(False, str(error))


class Updater:
    def __init__(self, browser, root):
        self.browser, self.root = browser, Path(root).resolve()
        directory = Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation))
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "update-schedule.json"
        try:
            self.state = json.loads(self.path.read_text())
            if not isinstance(self.state, dict):
                self.state = {}
            float(self.state.get("due", 0))
        except (OSError, ValueError, TypeError):
            self.state = {}
        self.job = None
        self.available = False
        self.installed = False
        self.retry_at = 0
        self.reminder = None
        self.button = browser.browser_menu.addAction(
            "Check for updates…", self.open
        )
        self.timer = QTimer(browser)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)
        QTimer.singleShot(2500, lambda: self.start(False))

    def save(self):
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.state), encoding="utf-8")
        temporary.replace(self.path)

    def label(self):
        if self.installed:
            text = "Update installed — restart to finish"
        elif self.state.get("due"):
            date = QDateTime.fromSecsSinceEpoch(int(self.state["due"]))
            text = "Update scheduled · " + date.toString("MMM d, HH:mm")
        else:
            text = "Update Available" if self.available else "Check for updates"
        self.button.setText(text)
        self.browser.menu_button.setText(
            "☰ 1" if self.available and not self.installed else "☰"
        )

    def start(self, install):
        if self.job and self.job.isRunning():
            return
        if self.installed:
            return
        self.button.setEnabled(False)
        self.button.setText("Updating…" if install else "Checking…")
        if install:
            self.browser.statusBar().showMessage(WARNING)
        self.job = GitJob(self.root, install, self.browser)
        self.job.done.connect(lambda ok, message: self.result(ok, message, install))
        self.job.start()

    def result(self, ok, message, install):
        self.button.setEnabled(True)
        if not ok:
            self.retry_at = time.time() + 300
            self.browser.statusBar().showMessage("Update pending or blocked: " + message)
            self.button.setToolTip(message)
            if install:
                QMessageBox.warning(self.browser, "Update did not complete",
                    message + "\n\nNo successful update was confirmed.\n" + WARNING)
        else:
            self.button.setToolTip("")
            self.available = message == "available"
            if message == "installed":
                self.installed = True
            if install and message in ("installed", "current"):
                self.state = {}
                self.save()
                self.hide_reminder()
                QMessageBox.information(self.browser, "Update complete",
                    "Update complete. You can now turn off your computer.\n"
                    "Restart Nimvex to use updated code. Open tabs will not be closed automatically."
                    if self.installed else "Nimvex is already up to date. No update is running.")
            elif message == "current":
                self.browser.statusBar().showMessage("Nimvex is up to date.")
        self.label()

    def open(self):
        if self.installed:
            QMessageBox.information(self.browser, "Update complete",
                "Restart Nimvex to finish. You can now turn off your computer.")
            return
        if not self.available and not self.state.get("due"):
            self.start(False)
            return
        box = QMessageBox(self.browser)
        box.setWindowTitle("Nimvex updates")
        box.setText("Choose when to update Nimvex.")
        box.setInformativeText(WARNING + "\nScheduled updates require Nimvex to remain open. "
            "If it is closed, the saved schedule resumes next time it opens.")
        now = box.addButton("Update Now", QMessageBox.ButtonRole.AcceptRole)
        later = box.addButton("Update Later", QMessageBox.ButtonRole.ActionRole)
        cancel = None
        if self.state.get("due"):
            cancel = box.addButton("Cancel Schedule", QMessageBox.ButtonRole.DestructiveRole)
        box.exec()
        if box.clickedButton() == now:
            self.start(True)
        elif box.clickedButton() == later:
            self.schedule()
        elif cancel is not None and box.clickedButton() == cancel:
            self.state = {}
            self.save()
            self.hide_reminder()
            self.label()

    def schedule(self):
        dialog = QDialog(self.browser)
        dialog.setWindowTitle("Schedule Nimvex update")
        layout = QVBoxLayout(dialog)
        label = QLabel("Choose a future date and time (your local time).\n" + WARNING +
            "\nNimvex must be open at the scheduled time.")
        label.setWordWrap(True)
        layout.addWidget(label)
        picker = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        picker.setDisplayFormat("yyyy-MM-dd HH:mm")
        picker.setCalendarPopup(True)
        layout.addWidget(picker)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        due = picker.dateTime().toSecsSinceEpoch()
        if due <= time.time():
            QMessageBox.warning(self.browser, "Invalid date", "Choose a future time.\n" + WARNING)
            return
        self.state = {"due": due, "reminded": False}
        self.save()
        self.retry_at = 0
        self.hide_reminder()
        self.label()
        self.tick()

    def hide_reminder(self):
        if self.reminder:
            self.reminder.close()
            self.reminder.deleteLater()
            self.reminder = None

    def tick(self):
        due = self.state.get("due")
        if not due or self.installed:
            return
        remaining = float(due) - time.time()
        if 0 < remaining <= 300 and not self.state.get("reminded"):
            self.state["reminded"] = True
            self.save()
            self.reminder = QDialog(self.browser)
            self.reminder.setWindowTitle("Nimvex update reminder")
            layout = QVBoxLayout(self.reminder)
            message = QPushButton("Update starts at " + QDateTime.fromSecsSinceEpoch(int(due)).toString("HH:mm") +
                "\n" + WARNING + "\nClick this message to dismiss (update stays scheduled).")
            message.clicked.connect(self.reminder.close)
            layout.addWidget(message)
            self.reminder.show()
        if remaining <= 0 and time.time() >= self.retry_at:
            if not self.job or not self.job.isRunning():
                self.hide_reminder()
                self.start(True)
