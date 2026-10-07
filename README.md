# Nimvex

A Linux-first browser prototype built with Python, PySide6, and Qt WebEngine.

## Current features

- Firefox-inspired layout: tabs, navigation, bookmarks, web page
- Address bar with DuckDuckGo search
- Movable and closable tabs
- Locally saved bookmarks
- Gaming mode that freezes eligible background tabs
- Keep-this-tab-awake option
- GPU and media diagnostic pages
- Persistent website-profile configuration

Website login compatibility varies. Google sign-in is not guaranteed.

## Development environment

Tested during development on Nobara Linux 44 KDE, x86_64,
with Python 3.14.7 and PySide6 / Qt 6.11.2.

Install dependencies:

```bash
sudo dnf install python3-pyside6.x86_64 python3-psutil
```

Run:

```bash
/usr/bin/python3 browser.py
```

Optional quieter website-console output:

```bash
QT_LOGGING_RULES='js.warning=false' /usr/bin/python3 browser.py
```

## Performance status

This is a prototype, not a proven performance improvement over Firefox.
Resource measurements must include the Qt WebEngine subprocesses.
See DEVELOPMENT.md for the current investigation.

## Privacy

Do not commit browser profiles, cookies, website storage, account tokens,
personal bookmarks, or diagnostic logs.
