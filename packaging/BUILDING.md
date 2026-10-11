# Local RPM builds

Target: Nobara 44 KDE on x86_64.

Build from a committed Git reference:

    /usr/bin/python3 packaging/build-rpm.py --ref HEAD --release 3

The script reads package sources from the selected commit, not from
uncommitted browser changes. Commit packaging changes before building.

The source archive contains the committed browser, RPM updater,
bookmark importer, project assets, license, desktop entry, launcher,
repository configuration, and public signing key.

The packaged browser uses nimvex_rpm_updater instead of the development
Git updater. The launcher executes:

    /usr/bin/python3 /usr/share/nimvex/browser.py

Artifacts are created in a separate directory under
~/Projects/nimvex-builds. The script prints the exact output directory.

The build produces an unsigned binary RPM, source RPM, ZIP, and manifest.
It installs nothing and publishes nothing.

Before release:
1. Verify package identity and payload.
2. Sign the RPM with the official release key.
3. Verify the signature.
4. Test installation, launch, bookmark import, deletion, and persistence.
5. Publish the signed RPM and regenerate and sign repository metadata.
6. Update download documentation after deployment is verified.

Signing changes RPM bytes. ZIPs and SHA-256 manifests produced before
signing must be regenerated if they will be distributed with signed RPMs.

A successful build is not proof of runtime correctness or clean-system
dependency resolution. Existing downloads remain unchanged until
publication.
