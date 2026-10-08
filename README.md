# Nimvex

Nimvex is an experimental Linux web browser built with Python,
PySide6, and Qt WebEngine.

It combines a custom start page, tabbed browsing, local bookmarks,
system-tray integration, and an optional gaming mode.

## Project status

Nimvex is currently a prototype being prepared for public alpha testing.

[Download Nimvex](https://github.com/HexandRoach/nimvex/releases)

A Nobara-targeted RPM test build has been prepared. Installable test
packages are published as pre-release assets on the Releases page.
If no RPM asset is listed, the app download has not been published yet.

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

## Install and launch the test app

### Initial test target

- Nobara Linux 44, KDE Plasma Desktop Edition.
- Initial hardware target: x86_64.
- Other distributions and architectures are not yet validated.

This is an experimental test build. Use it for non-sensitive browsing.

### Download and install

1. Click Download Nimvex near the top of this README.
2. On the Releases page, open the latest Nimvex test pre-release.
3. Under Assets, download the attached nimvex RPM file.
4. Do not choose Source code (zip) or Source code (tar.gz) if you want
   the installable app.
5. Fully quit any existing Nimvex instance, including its tray instance.
6. Open the downloaded RPM with Nobara's graphical RPM installer.
7. Review the installation prompt and approve it if you want to install.
8. After installation, open the application menu, search for Nimvex,
   and launch it.

Users do not need to create a Python environment or run browser.py.
The RPM declares Python and PySide6 as system dependencies. Internet
access may be needed to install missing dependencies.

Graphical installation and dependency resolution are still being tested.
If double-clicking the RPM opens an archive viewer, try Open With and
select the Nobara RPM installer. If no installer is offered, report that
rather than assuming the package is broken.

The RPM is not a universal Linux package or a self-contained portable app.

### Later launches

Launch Nimvex from the application menu. You can pin that menu entry
to the taskbar.

If closing the window hides Nimvex in the tray, use Open Nimvex from
the tray to restore it. Use Quit Nimvex or the browser's Quit menu to
exit completely.

Avoid starting multiple instances: single-instance protection is not
implemented.

### Existing source users

An existing user-level nimvex.desktop entry may override the launcher
installed by the RPM and continue opening the source copy.

Back up that old launcher outside your user applications directory before
testing the packaged launcher. Do not delete your browser profile or
application data. Re-pin the installed application-menu entry if needed.

The packaged build has an About updates menu item instead of the
Git-based source updater. This helps identify which copy is running.

### Build and test status

The local RPM build and desktop-entry validation succeeded.
Graphical installation, dependency resolution on a fresh system,
application-menu launch, and end-to-end browser behavior still need
tester verification.

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

The RPM installs:

- The nimvex launch command.
- The browser and assets under /usr/share/nimvex.
- The desktop entry under /usr/share/applications.
- The PNG icon in the hicolor application-icon directory.

The launcher is categorized under Utilities. The menu section may be
named differently depending on the desktop environment.

The source-code ZIP does not install these files or create a shortcut.

## Updates

### Installed RPM

The Git-based in-browser updater is disabled in this test package.

To update, fully quit Nimvex, download a newer published RPM, and install
it through the package installer. An automatic package-update channel
has not yet been configured or tested.

Do not delete your browser profile or application data when updating.

### Source checkout

The source version includes a Git-based updater. It requires a clean
main-branch checkout, GitHub SSH access, and the exact SSH origin URL
expected by nimvex_updater.py.

It does not support source ZIP installations or the installed RPM.

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
- Basic downloads have been added and locally tested; broader testing
  is still needed. A full download manager is not implemented.
- Browser extensions are not implemented.
- The current tray implementation does not prevent multiple instances.
- Tray behavior and menu placement depend on the desktop environment.
- RPM installation and package updates need end-to-end validation.
- Other Linux distributions and architectures are not validated.
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
