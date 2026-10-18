import re
from pathlib import Path
from PySide6.QtCore import QUrl, QUrlQuery, QTimer
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings

EXTERNAL = {"mailto", "tel", "sms", "magnet", "steam", "discord"}
INTERNAL = {"http", "https", "file", "about", "data", "blob"}

def tell(browser, text):
    browser.statusBar().showMessage(text, 12000)
    print("Nimvex links:", text, flush=True)

def open_external(browser, url):
    if url.scheme().lower() not in EXTERNAL:
        tell(browser, "Unsupported external link type: " + url.scheme())
        return
    if getattr(browser, "_external_prompt_open", False):
        return
    browser._external_prompt_open = True
    try:
        box = QMessageBox(browser)
        box.setWindowTitle("Open another application?")
        box.setText("This link requests an external application. Only continue if you trust it.")
        box.setDetailedText(url.toString())
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        if box.exec() == QMessageBox.StandardButton.Yes:
            if not QDesktopServices.openUrl(url):
                tell(browser, "Desktop could not dispatch this link; check its application association.")
    finally:
        browser._external_prompt_open = False

def install_view(view):
    view.settings().setUnknownUrlSchemePolicy(
        QWebEngineSettings.UnknownUrlSchemePolicy.AllowUnknownUrlSchemesFromUserInteraction
    )
    def navigation(request):
        url = QUrl(request.url())
        scheme = url.scheme().lower()
        if scheme in INTERNAL:
            if scheme == "file" and view.url().scheme().lower() in {"http", "https"}:
                request.reject()
                tell(view.browser, "A website cannot open a local file. Use the address bar yourself.")
            return
        request.reject()
        clicked = request.navigationType() == QWebEnginePage.NavigationType.NavigationTypeLinkClicked
        if request.isMainFrame() and clicked and scheme in EXTERNAL:
            QTimer.singleShot(0, lambda u=url: open_external(view.browser, u))
        elif request.isMainFrame():
            tell(view.browser, "Blocked unsupported or non-click external navigation: " + scheme)
    view.page().navigationRequested.connect(navigation)

def parse_input(text):
    text = text.strip()
    if not text:
        return QUrl()
    if text.startswith(("/", "~/")):
        return QUrl.fromLocalFile(str(Path(text).expanduser()))
    host_port = re.match(r"^(localhost|[A-Za-z0-9.-]+):[0-9]+(?:[/?#]|$)", text)
    if host_port:
        return QUrl("http://" + text)
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", text):
        return QUrl(text)
    if not any(c.isspace() for c in text) and ("." in text or text == "localhost" or text.startswith("localhost/")):
        return QUrl.fromUserInput(("http://" if text.startswith("localhost") else "https://") + text)
    url = QUrl("https://www.google.com/search")
    query = QUrlQuery()
    query.addQueryItem("q", text)
    url.setQuery(query)
    return url

def open_input(browser, text, new_tab=False):
    url = parse_input(text)
    if url.isEmpty():
        return
    if not url.isValid():
        tell(browser, "Invalid URL.")
        return
    scheme = url.scheme().lower()
    if scheme in EXTERNAL:
        open_external(browser, url)
        return
    if scheme not in {"http", "https", "file", "about"}:
        tell(browser, "Unsupported or unsafe address-bar link type: " + scheme)
        return
    if scheme in {"http", "https"} and not url.host():
        tell(browser, "Website URL has no hostname.")
        return
    if scheme == "file" and (not url.isLocalFile() or url.host() or not Path(url.toLocalFile()).is_file()):
        tell(browser, "Choose an existing local file, not a directory or remote file URL.")
        return
    if scheme == "about" and url.toString() != "about:blank":
        tell(browser, "Only about:blank is supported here.")
        return
    if new_tab:
        browser.new_tab(url)
    else:
        view = browser.current_view()
        if view is None:
            browser.new_tab(url)
        else:
            view.load(url)
            view.setFocus()

def open_startup_links(browser, arguments):
    for argument in arguments:
        if argument.startswith("-"):
            continue
        # Startup accepts explicit URLs and absolute paths, not search text.
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", argument) or argument.startswith(("/", "~/")):
            open_input(browser, argument, new_tab=True)
        else:
            tell(browser, "Startup argument ignored: use an explicit URL or absolute file path.")
