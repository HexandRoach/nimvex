from PySide6.QtWidgets import QFileDialog
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QStyle
import base64
from time import monotonic
from PySide6.QtCore import QTimer
from PySide6.QtWebEngineCore import QWebEnginePage

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTabBar, QStackedWidget

import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QUrlQuery, QStandardPaths
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
    QMainWindow, QMenu, QMessageBox, QPushButton, QTabWidget,
    QToolButton, QVBoxLayout, QWidget
)
from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView


HOME = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>New tab</title>
<style>
body {
    margin: 0; background: #111820; color: #e7eef6;
    font-family: sans-serif; text-align: center;
}
main { margin: 16vh auto; padding: 24px; }
h1 { font-size: 58px; color: #68dbc3; margin-bottom: 12px; }
p { color: #9caebb; line-height: 1.8; }
.badge {
    display: inline-block; border: 1px solid #334552;
    border-radius: 20px; padding: 6px 16px; font-size: 13px;
}

/* NIMVEX_WALLPAPER */
html {
    min-height: 100%;
    background: #071827;
}
body {
    margin: 0;
    min-height: 100vh;
    box-sizing: border-box;
    background-color: #071827;
    background-image:
        linear-gradient(
            90deg,
            rgba(3, 15, 27, 0.65),
            rgba(3, 15, 27, 0.08)
        ),
        url("__NIMVEX_WALLPAPER_URL__");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
    color: #e7eef6;
    text-align: left;
}
main {
    box-sizing: border-box;
    width: min(520px, 90vw);
    margin: 0;
    padding: clamp(70px, 16vh, 160px) 28px 48px;
}
h1 {
    color: #8af3df;
    text-shadow: 0 3px 18px rgba(0, 0, 0, 0.65);
}
p {
    color: #e0edf5;
    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.9);
}
.badge {
    background: rgba(7, 24, 39, 0.75);
    border-color: rgba(180, 220, 235, 0.35);
    color: #e0edf5;
}
@media (max-width: 600px) {
    main {
        width: 100%;
        padding: 48px 24px;
    }
    h1 {
        font-size: 44px;
    }
}

</style>
</head>
<body>
<main>
<h1>Nimvex</h1>
<p>Your space on the web.</p>
<p>Type a website or search in the address bar above.</p>
<span class="badge">Prototype · Website sessions saved locally</span>
</main>
</body>
</html>
"""

# Load the wallpaper separately instead of embedding it in HOME.
NIMVEX_WALLPAPER = Path(__file__).resolve().parent / "assets" / "HexandRoach.png"
HOME = HOME.replace(
    "__NIMVEX_WALLPAPER_URL__",
    NIMVEX_WALLPAPER.as_uri()
)
HOME_BASE_URL = QUrl.fromLocalFile(
    str(Path(__file__).resolve().parent) + "/"
)


class WebView(QWebEngineView):
    def __init__(self, browser):
        super().__init__(browser.profile, browser)
        self.browser = browser

    def createWindow(self, window_type):
        return self.browser.new_tab()



class BrowserTabs(QWidget):
    currentChanged = Signal(int)
    tabCloseRequested = Signal(int)

    def __init__(self):
        super().__init__()
        self.header = QWidget()
        self.header.setObjectName("tabHeader")
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(8, 0, 8, 0)
        self.header_layout.setSpacing(4)

        self.bar = QTabBar()
        self.bar.setDocumentMode(True)
        self.bar.setUsesScrollButtons(True)
        self.header_layout.addWidget(self.bar, 1)

        self.stack = QStackedWidget(self)
        body = QVBoxLayout(self)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self.stack)

        self.bar.currentChanged.connect(self.activate)
        self.bar.tabCloseRequested.connect(self.tabCloseRequested.emit)
        self.bar.tabMoved.connect(lambda *_: self.activate(self.currentIndex()))

    def activate(self, index):
        view = self.widget(index)
        if view is not None:
            self.stack.setCurrentWidget(view)
        self.currentChanged.emit(index)

    def addTab(self, view, title):
        self.stack.addWidget(view)
        previous = self.bar.blockSignals(True)
        index = self.bar.addTab(title)
        self.bar.setTabData(index, view)
        self.bar.blockSignals(previous)
        return index

    def removeTab(self, index):
        view = self.widget(index)
        if view is None:
            return
        previous = self.bar.blockSignals(True)
        self.bar.removeTab(index)
        self.stack.removeWidget(view)
        self.bar.blockSignals(previous)
        self.activate(self.currentIndex())

    def widget(self, index):
        if 0 <= index < self.bar.count():
            return self.bar.tabData(index)
        return None

    def currentWidget(self):
        return self.widget(self.currentIndex())

    def currentIndex(self):
        return self.bar.currentIndex()

    def setCurrentIndex(self, index):
        self.bar.setCurrentIndex(index)
        self.activate(index)

    def count(self):
        return self.bar.count()

    def indexOf(self, view):
        for index in range(self.count()):
            if self.widget(index) is view:
                return index
        return -1

    def tabBar(self):
        return self.bar

    def setDocumentMode(self, enabled):
        self.bar.setDocumentMode(enabled)

    def setTabsClosable(self, enabled):
        self.bar.setTabsClosable(enabled)

    def setMovable(self, enabled):
        self.bar.setMovable(enabled)

    def setCornerWidget(self, widget, corner):
        self.header_layout.addWidget(widget)

    def setTabText(self, index, text):
        self.bar.setTabText(index, text)

    def setTabToolTip(self, index, text):
        self.bar.setTabToolTip(index, text)

    def setTabIcon(self, index, icon):
        self.bar.setTabIcon(index, icon)


class Browser(QMainWindow):

    def handle_download(self, download):
        directory = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        ) or str(Path.home())

        name = Path(download.downloadFileName()).name or "download"
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Save download",
            str(Path(directory) / name),
            "All files (*)",
        )

        if not destination:
            download.cancel()
            return

        target = Path(destination)
        download.setDownloadDirectory(str(target.parent))
        download.setDownloadFileName(target.name)

        self.active_downloads.append(download)
        download.isFinishedChanged.connect(
            lambda item=download: self.download_finished(item)
        )
        self.statusBar().showMessage("Downloading: " + target.name)
        download.accept()

    def download_finished(self, download):
        if not download.isFinished():
            return

        state = download.state()
        states = QWebEngineDownloadRequest.DownloadState
        target = Path(download.downloadDirectory()) / download.downloadFileName()

        if state == states.DownloadCompleted:
            self.statusBar().showMessage("Download complete: " + str(target))
        elif state == states.DownloadInterrupted:
            reason = download.interruptReasonString()
            self.statusBar().showMessage("Download failed: " + reason)
            QMessageBox.warning(self, "Download failed", reason)
        elif state == states.DownloadCancelled:
            self.statusBar().showMessage("Download cancelled.")

        if download in self.active_downloads:
            self.active_downloads.remove(download)

    def __init__(self):
        super().__init__()
        self.resize(1280, 820)
        self.setWindowTitle("Nimvex")

        profile_root = Path(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppDataLocation
            )
        ) / "web-profile"

        cache_root = Path(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.CacheLocation
            )
        ) / "web-cache"

        profile_root.mkdir(parents=True, exist_ok=True)
        cache_root.mkdir(parents=True, exist_ok=True)

        self.profile = QWebEngineProfile("NimvexDefault", self)
        self.active_downloads = []
        self.profile.downloadRequested.connect(self.handle_download)
        self.profile.setPersistentStoragePath(str(profile_root))
        self.profile.setCachePath(str(cache_root))
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        self.profile.setHttpCacheType(
            QWebEngineProfile.HttpCacheType.DiskHttpCache
        )
        self.profile.setHttpCacheMaximumSize(128 * 1024 * 1024)

        data_dir = Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        ))
        data_dir.mkdir(parents=True, exist_ok=True)
        self.bookmark_path = data_dir / "bookmarks.json"
        self.bookmarks = self.read_bookmarks()

        root = QWidget(self)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(root)

        navigation = QWidget()
        navigation.setObjectName("navigation")
        nav = QHBoxLayout(navigation)
        nav.setContentsMargins(12, 9, 12, 9)
        nav.setSpacing(6)

        self.back_button = self.button("←", "Back", self.go_back)
        self.forward_button = self.button("→", "Forward", self.go_forward)
        self.reload_button = self.button("↻", "Reload", self.reload)
        self.home_button = self.button("⌂", "Home", self.show_home)

        for button in (
            self.back_button, self.forward_button,
            self.reload_button, self.home_button
        ):
            nav.addWidget(button)

        address_shell = QWidget()
        address_shell.setObjectName("addressShell")
        address_layout = QHBoxLayout(address_shell)
        address_layout.setContentsMargins(10, 0, 4, 0)
        address_layout.setSpacing(4)

        self.connection_label = QLabel("WEB")
        self.connection_label.setObjectName("connection")
        self.connection_label.setToolTip(
            "URL scheme indicator only — not a security audit."
        )
        address_layout.addWidget(self.connection_label)

        self.address = QLineEdit()
        self.address.setPlaceholderText("Search or enter address")
        self.address.setClearButtonEnabled(True)
        self.address.returnPressed.connect(self.navigate)
        address_layout.addWidget(self.address, 1)

        self.star_button = self.button(
            "☆", "Bookmark this page (Ctrl+D)", self.toggle_bookmark
        )
        address_layout.addWidget(self.star_button)
        nav.addWidget(address_shell, 1)

        self.menu_button = self.button("☰", "Nimvex menu", lambda: None)
        self.menu_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        self.browser_menu = QMenu(self)
        self.menu_button.setMenu(self.browser_menu)
        nav.addWidget(self.menu_button)

        self.bookmark_bar = QWidget()
        self.bookmark_bar.setObjectName("bookmarkBar")
        self.bookmark_layout = QHBoxLayout(self.bookmark_bar)
        self.bookmark_layout.setContentsMargins(14, 4, 14, 6)
        self.bookmark_layout.setSpacing(6)

        self.tabs = BrowserTabs()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.sync_ui)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.tabBar().setElideMode(Qt.TextElideMode.ElideRight)

        new_button = self.button("+", "New tab (Ctrl+T)", self.new_tab)
        self.tabs.setCornerWidget(new_button, Qt.Corner.TopRightCorner)

        page_container = QWidget()
        page_layout = QVBoxLayout(page_container)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        page_layout.addWidget(navigation)
        page_layout.addWidget(self.bookmark_bar)

        layout.addWidget(self.tabs.header)
        layout.addWidget(page_container)
        layout.addWidget(self.tabs, 1)

        self.setup_menu()
        self.tools_closed_tabs = []
        tools = self.browser_menu.addMenu("Tools Hub")
        tools.addAction("Search open tabs…", self.tools_search_tabs)
        reopen = tools.addAction("Reopen closed tab", self.reopen_closed_tab)
        reopen.setShortcut(QKeySequence("Ctrl+Shift+T"))
        tools.addAction("Find duplicate tabs…", self.tools_find_duplicates)
        tools.addAction("Search bookmarks…", self.tools_search_bookmarks)
        self.setup_shortcuts()
        self.apply_theme()
        self.refresh_bookmarks()
        self.new_tab()

    def button(self, text, tooltip, callback):
        button = QToolButton()
        button.setText(text)
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda checked=False: callback())
        return button

    def current_view(self):
        return self.tabs.currentWidget()

    def new_tab(self, url=None):
        view = WebView(self)
        index = self.tabs.addTab(view, "New tab")
        self.tabs.setCurrentIndex(index)

        view.titleChanged.connect(
            lambda title, v=view: self.update_tab_title(v, title)
        )
        view.iconChanged.connect(
            lambda icon, v=view: self.update_tab_icon(v, icon)
        )
        view.urlChanged.connect(lambda url, v=view: self.view_changed(v))
        view.loadStarted.connect(
            lambda v=view: self.loading_changed(v, True)
        )
        view.loadFinished.connect(
            lambda ok, v=view: self.loading_changed(v, False, ok)
        )

        if isinstance(url, QUrl):
            view.load(url)
        else:
            view.setHtml(HOME, HOME_BASE_URL)
            self.address.setFocus()

        self.sync_ui()
        return view


    def reopen_closed_tab(self):
        if self.tools_closed_tabs:
            self.new_tab(QUrl(self.tools_closed_tabs.pop()))
        else:
            self.statusBar().showMessage("No closed website tabs to reopen.", 4000)

    def tools_search_tabs(self):
        from PySide6.QtWidgets import QDialog, QListWidget
        dialog = QDialog(self)
        dialog.setWindowTitle("Search open tabs")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)
        search = QLineEdit()
        search.setPlaceholderText("Filter by title or URL")
        listing = QListWidget()
        views = [self.tabs.widget(i) for i in range(self.tabs.count())]
        layout.addWidget(search)
        layout.addWidget(listing)
        for view in views:
            listing.addItem((view.title() or "New tab") + " — " + view.url().toString())
        def filter_items(text):
            for i in range(listing.count()):
                listing.item(i).setHidden(text.casefold() not in listing.item(i).text().casefold())
        def activate(item):
            view = views[listing.row(item)]
            index = self.tabs.indexOf(view)
            if index >= 0:
                self.tabs.setCurrentIndex(index)
            dialog.accept()
        search.textChanged.connect(filter_items)
        listing.itemActivated.connect(activate)
        dialog.exec()

    def tools_search_bookmarks(self):
        from PySide6.QtWidgets import QDialog, QListWidget
        dialog = QDialog(self)
        dialog.setWindowTitle("Search bookmarks")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)
        search = QLineEdit()
        search.setPlaceholderText("Filter by name or URL")
        listing = QListWidget()
        bookmarks = list(self.bookmarks)
        layout.addWidget(search)
        layout.addWidget(listing)
        for bookmark in bookmarks:
            listing.addItem(bookmark["title"] + " — " + bookmark["url"])
        def filter_items(text):
            for i in range(listing.count()):
                listing.item(i).setHidden(text.casefold() not in listing.item(i).text().casefold())
        def activate(item):
            url = QUrl(bookmarks[listing.row(item)]["url"])
            if url.scheme() in ("http", "https"):
                self.new_tab(url)
                dialog.accept()
        search.textChanged.connect(filter_items)
        listing.itemActivated.connect(activate)
        dialog.exec()

    def tools_find_duplicates(self):
        groups = {}
        for i in range(self.tabs.count()):
            view = self.tabs.widget(i)
            if view.url().scheme() in ("http", "https"):
                groups.setdefault(view.url().toString(), []).append(i + 1)
        duplicates = [(url, tabs) for url, tabs in groups.items() if len(tabs) > 1]
        text = "\n\n".join(
            "Tabs " + ", ".join(map(str, tabs)) + "\n" + url
            for url, tabs in duplicates
        ) or "No duplicate website URLs found."
        QMessageBox.information(self, "Duplicate tabs — exact URLs", text)

    def close_tab(self, index):
        view = self.tabs.widget(index)
        if view:
            if view.url().scheme() in ("http", "https"):
                self.tools_closed_tabs.append(view.url().toString())
                self.tools_closed_tabs = self.tools_closed_tabs[-30:]
            view.stop()
            self.tabs.removeTab(index)
            view.deleteLater()
        if self.tabs.count() == 0:
            self.new_tab()

    def update_tab_title(self, view, title):
        index = self.tabs.indexOf(view)
        if index >= 0:
            self.tabs.setTabText(index, title or "New tab")
            self.tabs.setTabToolTip(index, title or "New tab")
        if view == self.current_view():
            self.sync_ui()

    def update_tab_icon(self, view, icon):
        index = self.tabs.indexOf(view)
        if index >= 0:
            self.tabs.setTabIcon(index, icon)

    def view_changed(self, view):
        if view == self.current_view():
            self.sync_ui()

    def loading_changed(self, view, loading, success=True):
        view.setProperty("loading", loading)
        if view == self.current_view():
            self.sync_ui()
            self.statusBar().showMessage(
                "Loading…" if loading else
                "Ready — website sessions saved locally" if success else
                "Page failed to load"
            )

    def sync_ui(self, *args):
        view = self.current_view()
        if not view:
            return

        url = view.url()
        text = url.toString()
        self.address.setText("" if text == "about:blank" or url == HOME_BASE_URL else text)
        self.connection_label.setText(
            "HTTPS" if url.scheme() == "https" else
            "HTTP" if url.scheme() == "http" else "WEB"
        )
        self.back_button.setEnabled(view.history().canGoBack())
        self.forward_button.setEnabled(view.history().canGoForward())

        loading = bool(view.property("loading"))
        self.reload_button.setText("✕" if loading else "↻")
        self.reload_button.setToolTip("Stop loading" if loading else "Reload")

        bookmarked = any(b["url"] == text for b in self.bookmarks)
        self.star_button.setText("★" if bookmarked else "☆")
        self.setWindowTitle(f"{view.title() or 'New tab'} — Nimvex")

    def navigate(self):
        text = self.address.text().strip()
        if not text:
            return

        if " " in text or (
            "." not in text and "://" not in text
            and not text.startswith(("localhost", "about:"))
        ):
            url = QUrl("https://www.startpage.com/sp/search")
            query = QUrlQuery()
            query.addQueryItem("query", text)
            url.setQuery(query)
        else:
            if "://" not in text and not text.startswith("about:"):
                text = "https://" + text
            url = QUrl.fromUserInput(text)

        if url.scheme() not in ("https", "http", "about"):
            self.statusBar().showMessage("Unsupported URL scheme.")
            return

        self.current_view().load(url)
        self.current_view().setFocus()

    def go_back(self):
        if self.current_view():
            self.current_view().back()

    def go_forward(self):
        if self.current_view():
            self.current_view().forward()

    def reload(self):
        view = self.current_view()
        if view:
            if view.property("loading"):
                view.stop()
            else:
                view.reload()

    def show_home(self):
        if self.current_view():
            self.current_view().setHtml(HOME, HOME_BASE_URL)

    def focus_address(self):
        self.address.setFocus()
        self.address.selectAll()

    def read_bookmarks(self):
        try:
            data = json.loads(self.bookmark_path.read_text())
            if not isinstance(data, list):
                return []
            return [
                item for item in data
                if isinstance(item, dict)
                and isinstance(item.get("title"), str)
                and isinstance(item.get("url"), str)
            ]
        except (OSError, ValueError):
            return []

    def save_bookmarks(self):
        try:
            temporary = self.bookmark_path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(self.bookmarks, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            temporary.replace(self.bookmark_path)
        except OSError as error:
            QMessageBox.warning(self, "Bookmarks", str(error))

    def toggle_bookmark(self):
        view = self.current_view()
        if not view or view.url().scheme() not in ("http", "https"):
            self.statusBar().showMessage("Open a website to bookmark it.")
            return

        url = view.url().toString()
        existing = next(
            (b for b in self.bookmarks if b["url"] == url), None
        )
        if existing:
            self.bookmarks.remove(existing)
        else:
            title, accepted = QInputDialog.getText(
                self, "Add bookmark", "Bookmark name:",
                text=view.title() or url
            )
            if not accepted:
                return
            self.bookmarks.append({
                "title": title.strip() or url,
                "url": url
            })

        self.save_bookmarks()
        self.refresh_bookmarks()
        self.sync_ui()

    def refresh_bookmarks(self):
        while self.bookmark_layout.count():
            item = self.bookmark_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.bookmarks:
            label = QLabel("Press Ctrl+D to add a bookmark")
            label.setObjectName("bookmarkHint")
            self.bookmark_layout.addWidget(label)

        for bookmark in self.bookmarks:
            url = bookmark["url"]
            title = bookmark["title"]
            button = QPushButton(
                title if len(title) <= 24 else title[:21] + "…"
            )
            button.setToolTip(f"{title}\n{url}")
            button.clicked.connect(
                lambda checked=False, u=url: self.current_view().load(QUrl(u))
            )
            self.bookmark_layout.addWidget(button)

        self.bookmark_layout.addStretch()

    def setup_menu(self):
        self.browser_menu.addAction("New tab", lambda: self.new_tab())
        self.browser_menu.addAction("Bookmark this page", self.toggle_bookmark)

        show_bar = self.browser_menu.addAction("Show bookmarks toolbar")
        show_bar.setCheckable(True)
        show_bar.setChecked(True)
        show_bar.toggled.connect(self.bookmark_bar.setVisible)

        self.browser_menu.addSeparator()
        diagnostics = self.browser_menu.addMenu("Diagnostics")
        diagnostics.addAction(
            "GPU information",
            lambda: self.new_tab(QUrl("chrome://gpu"))
        )
        diagnostics.addAction(
            "Media information",
            lambda: self.new_tab(QUrl("chrome://media-internals"))
        )
        self.browser_menu.addAction("About Nimvex", self.about)
        self.browser_menu.addAction("Quit", self.quit_application)

    def setup_shortcuts(self):
        commands = [
            ("Ctrl+T", lambda: self.new_tab()),
            ("Ctrl+W", lambda: self.close_tab(self.tabs.currentIndex())),
            ("Ctrl+L", self.focus_address),
            ("Ctrl+D", self.toggle_bookmark),
            ("Ctrl+R", self.reload),
            ("Alt+Left", self.go_back),
            ("Alt+Right", self.go_forward),
            ("Alt+Home", self.show_home),
            ("Ctrl+Tab", lambda: self.cycle_tab(1)),
            ("Ctrl+Shift+Tab", lambda: self.cycle_tab(-1)),
        ]
        for key, callback in commands:
            action = QAction(self)
            action.setShortcut(QKeySequence(key))
            action.triggered.connect(callback)
            self.addAction(action)

    def cycle_tab(self, direction):
        count = self.tabs.count()
        if count:
            self.tabs.setCurrentIndex(
                (self.tabs.currentIndex() + direction) % count
            )

    def about(self):
        QMessageBox.information(
            self, "About Nimvex",
            "Nimvex — browser prototype\n\n"
            "Firefox-inspired interface, Qt WebEngine foundation.\n"
            "Bookmarks are saved locally.\n"
            "Website sessions and cache are saved locally.\n\n"
            "Tab sleeping, downloads, and extensions are not implemented."
        )

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #171e27; color: #e3ebf3;
                font-family: sans-serif; font-size: 13px;
            }
            QTabWidget::pane { border: none; }
            QWidget#tabHeader, QTabBar { background: #111820; }
            QTabBar::tab {
                background: #111820; color: #9eafbd;
                padding: 10px 16px; margin: 5px 3px 4px 3px;
                border-radius: 7px; min-width: 110px;
                max-width: 210px;
            }
            QTabBar::tab:selected {
                background: #293744; color: #ffffff;
            }
            QTabBar::tab:hover { background: #22303b; }
            QWidget#navigation { background: #1d2732; }
            QWidget#addressShell {
                background: #10171e; border: 1px solid #394c5b;
                border-radius: 9px;
            }
            QLineEdit {
                background: transparent; border: none;
                padding: 10px 4px; color: #edf5fb;
                selection-background-color: #287c70;
            }
            QLabel#connection {
                background: transparent; color: #9fb2c0;
                font-size: 10px;
            }
            QToolButton {
                background: transparent; border: none;
                border-radius: 6px; padding: 7px;
                min-width: 22px; font-size: 19px;
            }
            QToolButton:hover { background: #344553; }
            QToolButton:disabled { color: #5a6875; }
            QWidget#bookmarkBar { background: #1d2732; }
            QLabel#bookmarkHint { color: #9eafbd; background: transparent; }
            QPushButton {
                background: transparent; border: none;
                border-radius: 5px; padding: 5px 9px;
            }
            QPushButton:hover { background: #344553; }
            QMenu {
                background: #25313e; border: 1px solid #425667;
                padding: 6px;
            }
            QMenu::item { padding: 8px 24px; }
            QMenu::item:selected { background: #36675f; }
            QStatusBar { background: #111820; color: #9eafbd; }
        """)



class GamingBrowser(Browser):
    def __init__(self):
        super().__init__()
        self.gaming_enabled = False

        self.browser_menu.insertSeparator(self.browser_menu.actions()[0])

        self.gaming_action = QAction("Gaming mode", self)
        self.gaming_action.setCheckable(True)
        self.gaming_action.toggled.connect(self.set_gaming_mode)
        self.browser_menu.insertAction(
            self.browser_menu.actions()[0], self.gaming_action
        )

        self.keep_awake_action = QAction("Keep this tab awake", self)
        self.keep_awake_action.setCheckable(True)
        self.keep_awake_action.toggled.connect(self.set_keep_awake)
        self.browser_menu.insertAction(
            self.browser_menu.actions()[1], self.keep_awake_action
        )
        self.browser_menu.aboutToShow.connect(self.update_keep_awake_action)

        self.sleep_timer = QTimer(self)
        self.sleep_timer.setInterval(5000)
        self.sleep_timer.timeout.connect(self.check_sleeping_tabs)
        self.sleep_timer.start()

        self.sync_ui()

    def new_tab(self, url=None):
        view = super().new_tab(url)
        view.last_active = monotonic()
        view.keep_awake = False
        view.media_check_pending = False
        view.page().lifecycleStateChanged.connect(
            lambda state, v=view: self.refresh_sleep_label(v)
        )
        return view

    def sync_ui(self, *args):
        view = self.current_view()
        if view:
            view.last_active = monotonic()
            if view.page().lifecycleState() != QWebEnginePage.LifecycleState.Active:
                view.page().setLifecycleState(
                    QWebEnginePage.LifecycleState.Active
                )
        super().sync_ui(*args)

    def update_tab_title(self, view, title):
        super().update_tab_title(view, title)
        self.refresh_sleep_label(view)

    def refresh_sleep_label(self, view):
        index = self.tabs.indexOf(view)
        if index < 0:
            return
        asleep = (
            view.page().lifecycleState()
            == QWebEnginePage.LifecycleState.Frozen
        )
        title = view.title() or "New tab"
        self.tabs.setTabText(index, ("[sleep] " if asleep else "") + title)
        self.tabs.setTabToolTip(
            index, title + (" — sleeping" if asleep else "")
        )

    def set_gaming_mode(self, enabled):
        self.gaming_enabled = enabled
        for index in range(self.tabs.count()):
            view = self.tabs.widget(index)
            view.last_active = monotonic()
            if not enabled:
                view.page().setLifecycleState(
                    QWebEnginePage.LifecycleState.Active
                )
        self.statusBar().showMessage(
            "Gaming mode on — eligible background tabs sleep after 60 seconds."
            if enabled else
            "Gaming mode off — all tabs awake."
        )

    def update_keep_awake_action(self):
        view = self.current_view()
        self.keep_awake_action.blockSignals(True)
        self.keep_awake_action.setChecked(
            bool(view and getattr(view, "keep_awake", False))
        )
        self.keep_awake_action.blockSignals(False)

    def set_keep_awake(self, enabled):
        view = self.current_view()
        if view:
            view.keep_awake = enabled
            view.page().setLifecycleState(
                QWebEnginePage.LifecycleState.Active
            )
            self.statusBar().showMessage(
                "This tab is protected from sleeping."
                if enabled else "This tab can sleep in Gaming mode."
            )

    def check_sleeping_tabs(self):
        if not self.gaming_enabled:
            return

        active = QWebEnginePage.LifecycleState.Active
        frozen = QWebEnginePage.LifecycleState.Frozen

        for index in range(self.tabs.count()):
            view = self.tabs.widget(index)
            page = view.page()

            protected = (
                view == self.current_view()
                or getattr(view, "keep_awake", False)
                or bool(view.property("loading"))
                or page.isVisible()
                or page.recentlyAudible()
                or page.recommendedState() == active
            )

            if protected:
                if page.lifecycleState() != active:
                    page.setLifecycleState(active)
                continue

            if page.lifecycleState() == frozen:
                continue

            if monotonic() - getattr(view, "last_active", monotonic()) < 60:
                continue

            if getattr(view, "media_check_pending", False):
                continue

            view.media_check_pending = True
            page.runJavaScript(
                """(() => Array.from(
                    document.querySelectorAll('video, audio')
                ).some(media => !media.paused && !media.ended))()""",
                lambda playing, v=view: self.finish_media_check(v, playing)
            )

    def finish_media_check(self, view, playing):
        if self.tabs.indexOf(view) < 0:
            return

        view.media_check_pending = False
        page = view.page()
        active = QWebEnginePage.LifecycleState.Active

        if (
            not self.gaming_enabled
            or view == self.current_view()
            or getattr(view, "keep_awake", False)
            or bool(view.property("loading"))
            or page.isVisible()
            or page.recentlyAudible()
            or page.recommendedState() == active
            or monotonic() - view.last_active < 60
            or playing is not False
        ):
            return

        page.setLifecycleState(QWebEnginePage.LifecycleState.Frozen)



class TrayBrowser(GamingBrowser):
    def __init__(self):
        super().__init__()

        icon = QIcon(str(Path(__file__).resolve().parent / "assets" / "nimvex-logo.svg"))
        if icon.isNull():
            icon = self.style().standardIcon(
                QStyle.StandardPixmap.SP_ComputerIcon
            )
        self.setWindowIcon(icon)

    def updater_is_busy(self):
        updater = getattr(self, "updater", None)
        if updater is None:
            return False

        # Packaged RPM updater.
        if getattr(updater, "process", None) is not None:
            return True

        # Development Git updater.
        job = getattr(updater, "job", None)
        return job is not None and job.isRunning()

    def quit_application(self):
        self.close()

    def closeEvent(self, event):
        if self.updater_is_busy():
            event.ignore()
            QMessageBox.information(
                self,
                "Update operation running",
                "Wait for the update operation to finish before closing Nimvex."
            )
            return

        super().closeEvent(event)
        if event.isAccepted():
            QApplication.instance().quit()


app = QApplication(["nimvex", *sys.argv[1:]])
app.setDesktopFileName("nimvex")
app.setApplicationDisplayName("Nimvex")
app.setWindowIcon(QIcon(str(
    Path(__file__).resolve().parent / "assets" / "nimvex-logo.svg"
)))
app.setApplicationName("Nimvex")
app.setOrganizationName("Nimvex")
window = TrayBrowser()
from nimvex_updater import Updater
window.updater = Updater(window, Path(__file__).resolve().parent)
window.show()
sys.exit(app.exec())
