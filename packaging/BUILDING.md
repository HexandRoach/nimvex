# Local RPM test build

Initial target: Nobara 44 KDE on x86_64.

The spec uses a source archive named nimvex-0.0.0.tar.gz.
The archive contains a top-level nimvex-0.0.0 directory with:

- browser.py
- assets/HexandRoach.png
- assets/nimvex-logo.svg
- assets/nimvex.png
- assets/nimvex-installer-art.svg
- License
- nimvex.desktop
- nimvex

The packaged browser.py replaces the source Git updater startup with
an About updates action explaining that updates require a newer RPM.

The nimvex launcher executes:
    /usr/bin/python3 /usr/share/nimvex/browser.py

Build tools include rpmbuild, python3-devel, and desktop-file-utils.
Runtime requirements are recorded in nimvex.spec.

The initial build used version 0.0.0 and release 0.1.test.
This is a local test version, not a stable release.

The spec is saved here, but automated source-archive generation still
needs to be added. Do not build directly from an unmodified source
browser.py: the Git updater must be disabled in the packaged copy.

Build success does not establish installability or browser correctness.
Test graphical installation, clean-system dependency resolution,
application-menu launch, icons, downloads, tray behavior, and updates
before claiming support.
