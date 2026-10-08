# Nimvex

Nimvex is an experimental Linux web browser built with Python,
PySide6, and Qt WebEngine.

It combines a custom start page, tabbed browsing, local bookmarks,
system-tray integration, and an optional gaming mode.

## Project status

Nimvex is currently a prototype being prepared for public alpha testing.

[Download Nimvex](https://github.com/HexandRoach/nimvex/archive/refs/heads/main.zip)

The source version can be run locally. A standalone downloadable alpha
package is not yet documented as available.

Use Nimvex for testing and non-sensitive browsing while its functionality,
packaging, and update behavior are being validated.

## Features

### Browsing and navigation

- Tabbed browsing with a new-tab button.
- Address-bar navigation and search.
- Back, forward, reload, and Home controls.
- Local bookmarks and a bookmark toolbar.
- Website sessions and cache stored locally.
- GPU and media diagnostic pages.

### Custom start page

- Nimvex welcome page.
- Custom fish-and-roach wallpaper.
- Wallpaper loaded from the project assets directory.
- Welcome text positioned on the darker side of the artwork.

### Branding and desktop integration

- Custom SVG Nimvex logo.
- Application identity configured for the Nimvex desktop launcher.
- Window and system-tray icons.
- Launcher template categorized under Utilities.

The menu section may be named Utilities or Accessories depending on the
desktop environment.

### System-tray behavior

- Closing the browser window hides it in the tray when a tray is available.
- Open Nimvex restores the window.
- Quit Nimvex fully exits the application.
- The browser's Quit menu also exits the application.
- If no system tray is available, closing the window closes it normally.

Hiding the window does not automatically stop media or web activity.

### Gaming mode

- Optional background-tab sleeping.
- Eligible background tabs are considered for sleeping after 60 seconds.
- Active tabs, loading pages, protected tabs, and tabs detected as playing
  media are excluded from sleeping.
- Individual tabs can be protected from sleeping.
- Disabling gaming mode wakes tabs.

Not every background tab will sleep: eligibility also depends on Qt
WebEngine's lifecycle recommendations.

## Running from source

### Requirements

- Linux desktop environment.
- Python compatible with the selected PySide6 release.
- PySide6, including Qt WebEngine.
- Git to clone the repository.

System-tray behavior requires a desktop environment with tray support.

### Get the source

```bash
git clone [https://github.com/HexandRoach/nimvex.git](https://github.com/HexandRoach/nimvex.git)
cd nimvex
```

### Set up a Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install PySide6
```

If installation fails, check that the chosen PySide6 version supports
your Python version and system architecture.

### Launch

With the environment activated:

```bash
python browser.py
```

Keep the project assets in place:

```text
assets/
├── HexandRoach.png
└── nimvex-logo.svg
```

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+T | Open a new tab |
| Ctrl+W | Close the current tab |
| Ctrl+L | Focus the address bar |
| Ctrl+D | Bookmark the current page |
| Ctrl+R | Reload |
| Alt+Left | Go back |
| Alt+Right | Go forward |
| Alt+Home | Open the start page |
| Ctrl+Tab | Switch to the next tab |

## Application-menu launcher

The repository includes:

```text
packaging/nimvex.desktop
```

Its category is:

```ini
Categories=Utility;
```

This is a packaging template, not a complete installation script.

The template expects:

- A launch command named `nimvex`.
- An installed icon named `nimvex`.
- The desktop entry installed in an applications directory.

Copying the template alone does not install the browser or its launch
command. For a source checkout, a local launcher must use the actual
Python executable, project path, and icon path.

## Updates

The project includes `nimvex_updater.py`.

Update behavior for a standalone packaged release still needs to be
reviewed and tested. Do not assume the source updater will work unchanged
inside an AppImage or other package.

## Alpha-release plans

The next release work includes:

- Build a downloadable Linux package.
- Include Qt WebEngine components and project assets.
- Test on systems outside the development environment.
- Provide launch and installation instructions.
- Include working desktop integration.
- Publish a GitHub pre-release with known limitations.

No specific package format or supported distribution list is guaranteed
until the build has been tested.

## Known limitations

- Nimvex is experimental, not a production-ready browser.
- Browser downloads and extensions are not implemented in the current
  documented prototype.
- The current tray implementation does not prevent multiple instances.
- Tray behavior and menu placement depend on the desktop environment.
- Standalone packaging and packaged updates are not yet validated.
- Closing the window to the tray leaves the browser running.

## Reporting problems

Please report issues at:

https://github.com/HexandRoach/nimvex/issues

Include:

- Linux distribution and version.
- Desktop environment.
- Whether you use Wayland or X11.
- Python and PySide6 versions, if running from source.
- Steps to reproduce the problem.
- Expected behavior and actual behavior.
- Relevant terminal output or screenshots.

Remove passwords, session tokens, and other private information before
sharing logs.

## License

See the `License` file in this repository.
