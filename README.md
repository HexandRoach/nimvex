# Nimvex

A desktop web browser with Google search, tabs, bookmarks, downloads,
and in-app update checking.

Nimvex is developed for Nobara 44 KDE on x86_64.

## Desktop download

The latest locally built and signed desktop package is
`nimvex-0.1.0-5.fc44.noarch.rpm`, intended for Nobara 44 KDE on x86_64.

[Download Nimvex 0.1.0-5 for Nobara 44 KDE](https://hexandroach.github.io/nimvex/rpm/nobara/44/x86_64/nimvex-0.1.0-5.fc44.noarch.rpm)

This link targets the release-5 package in the official RPM repository.
Public availability and fresh-system installation are not confirmed by
this documentation update.

After downloading the RPM, install it from its containing directory:

```bash
sudo dnf5 --setopt=localpkg_gpgcheck=True install ./nimvex-0.1.0-5.fc44.noarch.rpm
```

Review the transaction and signing-key identity before accepting any
key import. Do not disable signature verification to bypass an error.

### Release 0.1.0-5

- Opens explicit website URLs supplied when Nimvex starts.
- Improves address-bar handling for localhost addresses with ports.
- Supports directly entered existing local-file paths and `file://` URLs.
- Adds confirmation before dispatching supported external-app links.
- Updates desktop integration to accept HTTP and HTTPS URLs.
- Includes the link-support module in the RPM.

Drag-to-detach is not included. The experimental implementation caused
desktop freezes and was not promoted into the release source.

## Current development version

The development source includes additions beyond the original desktop
release:

- Tools Hub.
- Tab search.
- Reopen closed tabs.
- Duplicate-tab detection.
- Bookmark search.
- Sidebar notes.
- Saved workspaces.

These features are recorded in the project's development commits.
Do not assume they are included in the downloadable RPM above.

System tray integration has been removed.



## Links and external applications

### Websites and startup URLs

Nimvex handles HTTP and HTTPS addresses. Links requesting a new window
use the existing new-tab handler.

Launch Nimvex with an explicit URL:

```bash
nimvex 'https://example.com'
```

Multiple URL arguments open in separate tabs. This does not add
single-instance routing into an already-running window.

For a local development server, enter `http://localhost:8000` or
`localhost:8000`. The server must already be running.

### Local files

Enter an existing absolute file path, a path beginning with `~/`, or a
`file:///` URL directly in the address bar. Not every file format can be
displayed. Website navigation to local files remains restricted.

### External applications

Recognized external schemes are `mailto:`, `tel:`, `sms:`, `magnet:`,
`steam:`, and `discord:`.

Nimvex asks for confirmation before dispatching these links to the
desktop. A compatible application and desktop association are required.
Dispatch does not guarantee the destination application completes the
action. Unsupported schemes and non-click external navigation are not
automatically launched. Scripted redirects and popup flows still need
broader testing.

### AI bots and automation

Opening a URL and allowing a bot to read or control the page are separate
capabilities. This release does not add a dedicated automation API or
guarantee compatibility with Playwright, Selenium, or a particular bot.
End-to-end testing with the reported third-party bot is pending.

## Bookmark import and management

The development source includes experimental bookmark migration and
bookmark management.

### Import from another browser

Open the Nimvex menu and select “Import browser data…”.

The searchable browser selector groups browsers alphabetically and
attempts to detect local profiles for:

- Brave
- Chromium
- Firefox
- Google Chrome
- LibreWolf
- Microsoft Edge
- Opera
- Opera GX
- Vivaldi
- Waterfox
- Zen Browser

Detection checks configured standard Linux and Windows locations,
including selected Flatpak and Snap installations. Custom profile
locations may require manual folder selection.

Choose a profile, review the import preview, and confirm before saving.
Existing Nimvex bookmarks are retained, exact duplicate URLs are
skipped, and a backup is saved before the bookmark file is changed.

An exported bookmark HTML file can also be selected as a fallback.

### Manage and delete bookmarks

Open the Nimvex menu and select “Manage bookmarks…”.

Search by title or URL, select one or more bookmarks, and choose
“Delete selected…”. Deletion requires confirmation and creates a
backup before saving. It changes Nimvex bookmarks only, not the
source browser's bookmarks.

### Current limitations and testing status

- Bookmarks only; passwords, history, cookies, extensions, and signed-in
  sessions are not imported.
- Only HTTP and HTTPS bookmark URLs are accepted.
- Folder hierarchy is flattened into Nimvex's bookmark list.
- Duplicate matching uses exact URL strings.
- The importer caps the resulting list at 2,000 bookmarks.
- HTML exports must be UTF-8 and no larger than 5 MiB.
- Browser-specific detection and readers are experimental.
- Syntax checks have passed; end-to-end testing across all listed
  browsers and operating systems is pending.

These are development-source features. Existing RPM packages and older
Windows preview artifacts are not updated by this documentation change.
The Windows build configuration includes the importer for subsequent
builds; each new build still requires verification.

## Mobile Preview — iPhone, iPad & Android — Work in Progress

[Open Nimvex Mobile Preview](https://hexandroach.github.io/nimvex/mobile/)

Nimvex Mobile Preview is a mobile-friendly web companion with:

- Web search and website navigation.
- Saved website shortcuts.
- Local notes.

Open the link in your phone's browser. Shortcuts and notes are stored
locally in that browser and do not sync with the desktop version.

The mobile preview source has been pushed to the repository. Public
deployment is pending verification.

### Current limitations

This preview is not a dedicated iOS or Android browser app.
It uses your existing browser to open websites and does not include
Nimvex's desktop tools or extensions.

Clearing website data may delete saved shortcuts and notes.
Do not store passwords or sensitive information in notes.

## Updates

Select “Check for updates…” in the browser menu. Restart after a
confirmed update.

Signed installation and repository access are verified on the
developer's system. Fresh-system installation and in-app update
installation are still pending verification.

## Feedback

[Report a problem](https://github.com/HexandRoach/nimvex/issues)

When reporting a problem, include your operating system, Nimvex version,
the steps to reproduce it, and any relevant error messages.

## License

Official releases are free to use under [License](License). Modification
and redistribution require permission, subject to the license and
applicable law.

## Windows Preview — Work in Progress

[Download Nimvex Windows x64 Preview — GitHub Actions](https://github.com/HexandRoach/nimvex/actions/runs/37881693797)

On the build summary page, select `Nimvex-Windows-x64-preview` under
Artifacts. You must be signed into GitHub with access to this repository.

This is a temporary build-artifact download, not a published release.
The workflow is configured to retain its artifact for 14 days.
A release download link will replace this link after publication.

### Build and testing status

The Windows package built successfully on GitHub Actions.
Windows startup, browsing, downloads, and saved-data persistence
have not yet been verified.

### Running the preview

1. Download and extract the GitHub artifact archive.
2. Extract the `Nimvex-Windows-x64-preview.zip` inside it.
3. Open `Nimvex.exe` from the extracted `Nimvex` folder.
4. Keep all supporting files with the executable.

### Current limitations

- Experimental, unsigned Windows x64 build.
- Windows runtime testing is pending.
- No automatic update installation.
- Updates require downloading a newer Windows package.
- The preview uses the committed desktop source, not unfinished
  local development changes.
