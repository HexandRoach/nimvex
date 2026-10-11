import json
import os
import tempfile
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QFileDialog, QMessageBox


class BookmarkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.entries = []
        self.href = None
        self.title = []

    def finish_link(self):
        if self.href is not None:
            self.entries.append({
                "url": self.href.strip(),
                "title": " ".join("".join(self.title).split()),
            })
        self.href = None
        self.title = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.finish_link()
            self.href = dict(attrs).get("href")
            self.title = []

    def handle_data(self, data):
        if self.href is not None:
            self.title.append(data)

    def handle_endtag(self, tag):
        if tag == "a":
            self.finish_link()


def parse_bookmarks(text, existing):
    parser = BookmarkParser()
    parser.feed(text)
    parser.close()
    parser.finish_link()

    seen = {item["url"] for item in existing}
    additions = []
    duplicates = 0
    unsupported = 0

    for item in parser.entries:
        url = item["url"]
        parsed = QUrl(url)
        if (
            not parsed.isValid()
            or parsed.scheme().lower() not in ("http", "https")
            or not parsed.host()
            or any(ord(character) < 32 for character in url)
        ):
            unsupported += 1
            continue
        if url in seen:
            duplicates += 1
            continue
        seen.add(url)
        additions.append({"title": item["title"] or url, "url": url})

    return additions, duplicates, unsupported


def import_bookmarks(browser):
    try:
        filename, source_kind = choose_source(browser)
    except (OSError, ValueError, configparser.Error) as error:
        QMessageBox.warning(browser, "Cannot locate browser data", str(error))
        return
    if not filename:
        return

    try:
        text = read_source(filename, source_kind)
        additions, duplicates, unsupported = parse_bookmarks(
            text, browser.bookmarks
        )
        if len(browser.bookmarks) + len(additions) > 2000:
            raise ValueError(
                "This preview supports up to 2,000 total bookmarks "
                "because the current toolbar displays every bookmark."
            )
    except (OSError, UnicodeError, ValueError) as error:
        QMessageBox.warning(browser, "Import not completed", str(error))
        return

    summary = (
        f"New bookmarks: {len(additions)}\n"
        f"Duplicate URLs skipped: {duplicates}\n"
        f"Unsupported URLs skipped: {unsupported}\n\n"
        "Only HTTP/HTTPS bookmarks are imported. Folder structure is not "
        "preserved. Passwords, history, cookies, and sessions are not imported."
    )
    if not additions:
        QMessageBox.information(browser, "Nothing to import", summary)
        return

    box = QMessageBox(browser)
    box.setWindowTitle("Preview bookmark import")
    box.setText(summary)
    box.setInformativeText(
        "Add these bookmarks to Nimvex? Existing bookmarks will be retained."
    )
    box.setDetailedText("\n".join(
        f'{item["title"]} — {item["url"]}' for item in additions[:100]
    ) + ("\nOnly the first 100 entries are shown." if len(additions) > 100 else ""))
    box.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
    )
    box.setDefaultButton(QMessageBox.StandardButton.Cancel)
    if box.exec() != QMessageBox.StandardButton.Yes:
        return

    target = Path(browser.bookmark_path)
    merged = list(browser.bookmarks) + additions
    backup = None
    temporary = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = target.with_name(f"bookmarks.before-import-{stamp}.json")
        previous = (
            target.read_bytes() if target.exists()
            else json.dumps(browser.bookmarks, ensure_ascii=False).encode("utf-8")
        )
        with backup.open("xb") as output:
            output.write(previous)

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent,
            prefix="bookmarks-import-", suffix=".tmp", delete=False,
        ) as output:
            temporary = Path(output.name)
            json.dump(merged, output, indent=2, ensure_ascii=False)
            output.flush()
            os.fsync(output.fileno())
        temporary.replace(target)
    except OSError as error:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        QMessageBox.warning(
            browser, "Import not saved",
            f"No imported bookmarks were added to the running browser.\n{error}",
        )
        return

    browser.bookmarks = merged
    browser.refresh_bookmarks()
    browser.sync_ui()
    QMessageBox.information(
        browser, "Bookmarks imported",
        f"Added {len(additions)} bookmarks.\n"
        f"Skipped {duplicates} duplicates and {unsupported} unsupported URLs.\n\n"
        f"Previous bookmarks backed up to:\n{backup}",
    )


import configparser
import sqlite3
import sys
from html import escape
from PySide6.QtWidgets import QInputDialog


def original_locate_profiles(kind):
    home = Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    results = []
    if kind == "firefox":
        if sys.platform == "win32":
            roots = [Path(os.environ.get("APPDATA") or home / "AppData/Roaming")
                     / "Mozilla/Firefox"]
        else:
            roots = [
                home / ".mozilla/firefox",
                config / "mozilla/firefox",
                home / ".var/app/org.mozilla.firefox/.mozilla/firefox",
                home / ".var/app/org.mozilla.firefox/config/mozilla/firefox",
                home / "snap/firefox/common/.mozilla/firefox",
            ]
        for root in roots:
            ini = root / "profiles.ini"
            if ini.is_file():
                settings = configparser.ConfigParser(interpolation=None)
                settings.read(ini, encoding="utf-8")
                for section in settings.sections():
                    if not section.startswith("Profile"):
                        continue
                    value = settings.get(section, "Path", fallback="")
                    if not value:
                        continue
                    folder = Path(value)
                    if settings.get(section, "IsRelative", fallback="1") == "1":
                        folder = root / folder
                    target = folder / "places.sqlite"
                    if target.is_file():
                        name = settings.get(section, "Name", fallback=folder.name)
                        results.append((name, target))
            for pattern in ("*/places.sqlite", "Profiles/*/places.sqlite"):
                for target in root.glob(pattern):
                    results.append((target.parent.name, target))
    else:
        if sys.platform == "win32":
            roots = [Path(os.environ.get("LOCALAPPDATA") or home / "AppData/Local")
                     / "Google/Chrome/User Data"]
        else:
            roots = [
                config / "google-chrome",
                home / ".var/app/com.google.Chrome/config/google-chrome",
            ]
        for root in roots:
            for target in root.glob("*/Bookmarks"):
                if target.is_file():
                    results.append((target.parent.name, target))

    unique = {}
    for name, target in results:
        unique.setdefault(str(target.resolve()), (name, target))
    return list(unique.values())



from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

# name: (reader, Linux config path, Windows base, Windows relative path)
BROWSER_CATALOG = {
    "Brave": ("chrome", "BraveSoftware/Brave-Browser",
              "local", "BraveSoftware/Brave-Browser/User Data"),
    "Chromium": ("chrome", "chromium", "local", "Chromium/User Data"),
    "Firefox": ("firefox", None, None, None),
    "Google Chrome": ("chrome", None, None, None),
    "LibreWolf": ("firefox", None, None, None),
    "Microsoft Edge": ("chrome", "microsoft-edge",
                       "local", "Microsoft/Edge/User Data"),
    "Opera": ("chrome", "opera", "roaming", "Opera Software/Opera Stable"),
    "Opera GX": ("chrome", None, "roaming", "Opera Software/Opera GX Stable"),
    "Vivaldi": ("chrome", "vivaldi", "local", "Vivaldi/User Data"),
    "Waterfox": ("firefox", None, None, None),
    "Zen Browser": ("firefox", None, None, None),
}



# NIMVEX_ALL_BROWSER_DETECTION
def locate_profiles(name):
    if name not in BROWSER_CATALOG:
        raise ValueError("Unknown source browser.")

    home = Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    local = Path(os.environ.get("LOCALAPPDATA") or home / "AppData/Local")
    roaming = Path(os.environ.get("APPDATA") or home / "AppData/Roaming")
    reader, linux_path, win_base, win_path = BROWSER_CATALOG[name]
    roots = []

    if sys.platform == "win32":
        firefox_roots = {
            "Firefox": [roaming / "Mozilla/Firefox"],
            "LibreWolf": [
                home / ".librewolf",
                roaming / "librewolf",
                local / "librewolf",
            ],
            "Waterfox": [
                roaming / "Waterfox",
                roaming / "Waterfox/Waterfox",
            ],
            "Zen Browser": [roaming / "zen"],
        }
        if reader == "firefox":
            roots.extend(firefox_roots.get(name, []))
        elif name == "Google Chrome":
            roots.append(local / "Google/Chrome/User Data")
        elif win_path:
            roots.append((local if win_base == "local" else roaming) / win_path)

    elif sys.platform.startswith("linux"):
        firefox_roots = {
            "Firefox": [
                home / ".mozilla/firefox",
                config / "mozilla/firefox",
            ],
            "LibreWolf": [
                home / ".librewolf",
                config / "librewolf",
                config / "librewolf/librewolf",
            ],
            "Waterfox": [
                home / ".waterfox",
                config / "waterfox",
            ],
            "Zen Browser": [
                home / ".zen",
                config / "zen",
            ],
        }
        if reader == "firefox":
            roots.extend(firefox_roots.get(name, []))
        elif name == "Google Chrome":
            roots.append(config / "google-chrome")
        elif linux_path:
            roots.append(config / linux_path)

        flatpak = home / ".var/app"
        extra_roots = {
            "Firefox": [
                flatpak / "org.mozilla.firefox/.mozilla/firefox",
                flatpak / "org.mozilla.firefox/config/mozilla/firefox",
                home / "snap/firefox/common/.mozilla/firefox",
            ],
            "LibreWolf": [
                flatpak / "io.gitlab.librewolf-community/.librewolf",
                flatpak / "io.gitlab.librewolf-community/config/librewolf",
                flatpak / "io.gitlab.librewolf-community/config/librewolf/librewolf",
            ],
            "Zen Browser": [
                flatpak / "app.zen_browser.zen/zen",
                flatpak / "app.zen_browser.zen/.zen",
                flatpak / "app.zen_browser.zen/config/zen",
            ],
            "Google Chrome": [
                flatpak / "com.google.Chrome/config/google-chrome",
            ],
            "Brave": [
                flatpak / "com.brave.Browser/config/BraveSoftware/Brave-Browser",
            ],
            "Chromium": [
                flatpak / "org.chromium.Chromium/config/chromium",
                home / "snap/chromium/common/chromium",
            ],
            "Microsoft Edge": [
                flatpak / "com.microsoft.Edge/config/microsoft-edge",
            ],
            "Vivaldi": [
                flatpak / "com.vivaldi.Vivaldi/config/vivaldi",
            ],
        }
        roots.extend(extra_roots.get(name, []))

    results = {}
    seen_roots = set()

    def add_profile(label, target):
        if target.is_file():
            results.setdefault(str(target.resolve()), (label, target))

    for root in roots:
        key = str(root)
        if key in seen_roots or not root.is_dir():
            continue
        seen_roots.add(key)

        if reader == "firefox":
            ini = root / "profiles.ini"
            if ini.is_file():
                settings = configparser.ConfigParser(interpolation=None)
                try:
                    with ini.open(encoding="utf-8-sig") as file:
                        settings.read_file(file)
                    for section in settings.sections():
                        if not section.startswith("Profile"):
                            continue
                        value = settings.get(section, "Path", fallback="")
                        if not value:
                            continue
                        folder = Path(value)
                        if settings.get(section, "IsRelative", fallback="1") == "1":
                            folder = root / folder
                        label = settings.get(
                            section, "Name", fallback=folder.name
                        )
                        add_profile(label, folder / "places.sqlite")
                except (OSError, UnicodeError, configparser.Error):
                    pass

            for pattern in (
                "places.sqlite",
                "*/places.sqlite",
                "Profiles/*/places.sqlite",
            ):
                for target in root.glob(pattern):
                    add_profile(target.parent.name, target)
        else:
            for pattern in (
                "Bookmarks",
                "*/Bookmarks",
                "Profiles/*/Bookmarks",
            ):
                for target in root.glob(pattern):
                    add_profile(target.parent.name, target)

    return sorted(
        results.values(),
        key=lambda item: (item[0].casefold(), str(item[1])),
    )


def choose_source(browser):
    dialog = QDialog(browser)
    dialog.setWindowTitle("Import browser data")
    dialog.resize(700, 500)
    layout = QVBoxLayout(dialog)
    description = QLabel(
        "Import bookmarks only. Close the source browser first.\n"
        "Direct readers are experimental. Passwords, cookies, history, "
        "and folder hierarchy are not imported."
    )
    description.setWordWrap(True)
    layout.addWidget(description)

    search = QLineEdit()
    search.setPlaceholderText("Search browsers…")
    layout.addWidget(search)

    tree = QTreeWidget()
    tree.setHeaderLabels(["Browser", "Local profile detection"])
    layout.addWidget(tree)

    groups = {}
    items = []
    for name in sorted(BROWSER_CATALOG, key=str.casefold):
        initial = name[0].upper()
        group = (
            "A–C" if initial <= "C" else
            "D–F" if initial <= "F" else
            "G–L" if initial <= "L" else
            "M–O" if initial <= "O" else "P–Z"
        )
        if group not in groups:
            parent = QTreeWidgetItem(tree, [group])
            parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            groups[group] = parent
        manual_only = False
        item = QTreeWidgetItem(groups[group], [
            name, "Manual profile selection" if manual_only
            else "Detect profiles after selection",
        ])
        item.setData(0, Qt.ItemDataRole.UserRole, name)
        items.append(item)

    other = QTreeWidgetItem(tree, ["Other"])
    other.setFlags(other.flags() & ~Qt.ItemFlag.ItemIsSelectable)
    fallback = QTreeWidgetItem(other, [
        "Exported bookmark HTML file", "Choose an export file",
    ])
    fallback.setData(0, Qt.ItemDataRole.UserRole, "html")
    items.append(fallback)
    tree.expandAll()
    tree.setColumnWidth(0, 250)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok |
        QDialogButtonBox.StandardButton.Cancel
    )
    buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Continue")
    buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
    layout.addWidget(buttons)

    def update_selection():
        item = tree.currentItem()
        valid = bool(item and not item.isHidden() and
                     item.data(0, Qt.ItemDataRole.UserRole))
        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(valid)

    def filter_items(text):
        for item in items:
            item.setHidden(text.casefold() not in item.text(0).casefold())
        for parent in list(groups.values()) + [other]:
            parent.setHidden(all(
                parent.child(i).isHidden() for i in range(parent.childCount())
            ))
        update_selection()

    search.textChanged.connect(filter_items)
    tree.itemSelectionChanged.connect(update_selection)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return "", ""

    name = tree.currentItem().data(0, Qt.ItemDataRole.UserRole)
    if name == "html":
        filename, _ = QFileDialog.getOpenFileName(
            browser, "Choose bookmark export", "",
            "Bookmark HTML (*.html *.htm);;All files (*)",
        )
        return filename, "html"

    reader = BROWSER_CATALOG[name][0]
    profiles = locate_profiles(name)
    manual = "Choose profile folder manually..."
    labels = [f"{label} — {target.parent}" for label, target in profiles]
    selected, accepted = QInputDialog.getItem(
        browser, f"Choose {name} profile",
        "Select a profile. Bookmarks will be read without changing the source.\n"
        "If no profile is detected, choose its folder manually.",
        labels + [manual], 0, False,
    )
    if not accepted:
        return "", ""
    if selected == manual:
        folder = QFileDialog.getExistingDirectory(
            browser, f"Choose {name} profile folder"
        )
        if not folder:
            return "", ""
        target = Path(folder) / (
            "places.sqlite" if reader == "firefox" else "Bookmarks"
        )
        if not target.is_file():
            raise ValueError(
                f"No {'places.sqlite' if reader == 'firefox' else 'Bookmarks'} "
                "file exists in that folder."
            )
    else:
        target = profiles[labels.index(selected)][1]
    return str(target), reader


def read_source(filename, kind):
    path = Path(filename)
    if kind == "html":
        with path.open("rb") as source:
            raw = source.read(5 * 1024 * 1024 + 1)
        if len(raw) > 5 * 1024 * 1024:
            raise ValueError("HTML exports are limited to 5 MiB.")
        return raw.decode("utf-8-sig")

    entries = []
    if kind == "firefox":
        try:
            connection = sqlite3.connect(
                path.resolve().as_uri() + "?mode=ro",
                uri=True, timeout=2,
            )
            try:
                rows = connection.execute(
                    "SELECT COALESCE(b.title, p.title, p.url), p.url "
                    "FROM moz_bookmarks AS b "
                    "JOIN moz_places AS p ON p.id = b.fk "
                    "WHERE b.type = 1 ORDER BY b.id LIMIT 10001"
                ).fetchall()
            finally:
                connection.close()
            entries = [(title or url, url) for title, url in rows if url]
        except sqlite3.Error as error:
            raise ValueError(
                "Could not read Firefox bookmarks. Close Firefox and retry.\n"
                + str(error)
            ) from error
    else:
        with path.open("rb") as source:
            raw = source.read(20 * 1024 * 1024 + 1)
        if len(raw) > 20 * 1024 * 1024:
            raise ValueError("Chrome bookmark files are limited to 20 MiB.")
        data = json.loads(raw.decode("utf-8-sig"))
        roots = data.get("roots") if isinstance(data, dict) else None
        if not isinstance(roots, dict):
            raise ValueError("Unrecognized Chrome bookmark format.")
        stack = list(roots.values())
        visited = 0
        while stack:
            node = stack.pop()
            visited += 1
            if visited > 50000:
                raise ValueError("Bookmark structure exceeds the preview limit.")
            if not isinstance(node, dict):
                continue
            if node.get("type") == "url" and isinstance(node.get("url"), str):
                url = node["url"]
                title = node.get("name")
                entries.append((title if isinstance(title, str) else url, url))
            children = node.get("children", [])
            if isinstance(children, list):
                stack.extend(reversed(children))

    if len(entries) > 10000:
        raise ValueError("This preview reads at most 10,000 source bookmarks.")
    return "\n".join(
        f'<a href="{escape(url, quote=True)}">{escape(title)}</a>'
        for title, url in entries
    )


def librewolf_profiles():
    home = Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    flatpak = home / ".var/app/io.gitlab.librewolf-community"
    roots = [
        home / ".librewolf",
        config / "librewolf",
        config / "librewolf/librewolf",
        flatpak / ".librewolf",
        flatpak / "config/librewolf",
        flatpak / "config/librewolf/librewolf",
    ]
    results = {}
    for root in roots:
        ini = root / "profiles.ini"
        if ini.is_file():
            settings = configparser.ConfigParser(interpolation=None)
            settings.read(ini, encoding="utf-8")
            for section in settings.sections():
                if not section.startswith("Profile"):
                    continue
                value = settings.get(section, "Path", fallback="")
                if not value:
                    continue
                folder = Path(value)
                if settings.get(section, "IsRelative", fallback="1") == "1":
                    folder = root / folder
                target = folder / "places.sqlite"
                if target.is_file():
                    name = settings.get(section, "Name", fallback=folder.name)
                    results[str(target.resolve())] = (name, target)
        for pattern in ("*/places.sqlite", "Profiles/*/places.sqlite"):
            for target in root.glob(pattern):
                if target.is_file():
                    results.setdefault(
                        str(target.resolve()), (target.parent.name, target)
                    )
    return list(results.values())


def manage_bookmarks(browser):
    from PySide6.QtWidgets import (
        QAbstractItemView, QListWidget, QListWidgetItem, QPushButton,
    )

    dialog = QDialog(browser)
    dialog.setWindowTitle("Manage bookmarks")
    dialog.resize(760, 520)
    layout = QVBoxLayout(dialog)
    hint = QLabel(
        "Search by title or URL. Select multiple bookmarks with Ctrl or Shift.\n"
        "Deletion affects Nimvex only, not the browser they came from."
    )
    hint.setWordWrap(True)
    layout.addWidget(hint)
    search = QLineEdit()
    search.setPlaceholderText("Search bookmarks…")
    layout.addWidget(search)

    listing = QListWidget()
    listing.setSelectionMode(
        QAbstractItemView.SelectionMode.ExtendedSelection
    )
    layout.addWidget(listing)
    delete = QPushButton("Delete selected…")
    delete.setEnabled(False)
    layout.addWidget(delete)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    def update_button():
        delete.setEnabled(bool(listing.selectedItems()))

    def filter_list(text):
        for index in range(listing.count()):
            item = listing.item(index)
            hidden = text.casefold() not in item.text().casefold()
            if hidden:
                item.setSelected(False)
            item.setHidden(hidden)
        update_button()

    def populate():
        listing.clear()
        for index, bookmark in enumerate(browser.bookmarks):
            item = QListWidgetItem(
                bookmark["title"] + " — " + bookmark["url"]
            )
            item.setData(Qt.ItemDataRole.UserRole, index)
            item.setToolTip(bookmark["url"])
            listing.addItem(item)
        filter_list(search.text())

    def delete_selected():
        selected = {
            item.data(Qt.ItemDataRole.UserRole)
            for item in listing.selectedItems() if not item.isHidden()
        }
        if not selected:
            return
        answer = QMessageBox.question(
            dialog, "Delete bookmarks?",
            f"Delete {len(selected)} selected bookmark(s) from Nimvex?\n\n"
            "A backup will be saved before changing the bookmark file.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        remaining = [
            bookmark for index, bookmark in enumerate(browser.bookmarks)
            if index not in selected
        ]
        target = Path(browser.bookmark_path)
        temporary = None
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            backup = target.with_name(f"bookmarks.before-delete-{stamp}.json")
            previous = (
                target.read_bytes() if target.exists()
                else json.dumps(
                    browser.bookmarks, ensure_ascii=False
                ).encode("utf-8")
            )
            with backup.open("xb") as output:
                output.write(previous)

            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=target.parent,
                prefix="bookmarks-delete-", suffix=".tmp", delete=False,
            ) as output:
                temporary = Path(output.name)
                json.dump(remaining, output, indent=2, ensure_ascii=False)
                output.flush()
                os.fsync(output.fileno())
            temporary.replace(target)
        except OSError as error:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
            QMessageBox.warning(
                dialog, "Deletion not saved",
                "The running bookmark list was not changed.\n" + str(error),
            )
            return

        browser.bookmarks = remaining
        browser.refresh_bookmarks()
        browser.sync_ui()
        populate()
        QMessageBox.information(
            dialog, "Bookmarks deleted",
            f"Deleted {len(selected)} bookmark(s).\n\nBackup saved to:\n{backup}",
        )

    search.textChanged.connect(filter_list)
    listing.itemSelectionChanged.connect(update_button)
    delete.clicked.connect(delete_selected)
    populate()
    dialog.exec()
