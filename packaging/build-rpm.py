#!/usr/bin/python3
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--release", default="1")
    args = parser.parse_args()

    if not re.fullmatch(r"[0-9]+(?:\.[A-Za-z0-9]+)*", args.release):
        raise SystemExit("Stopped: invalid RPM release.")

    root = Path(__file__).resolve().parents[1]
    for tool in ("git", "rpmbuild", "rpm", "desktop-file-validate"):
        if shutil.which(tool) is None:
            raise SystemExit(f"Stopped: missing tool: {tool}")

    commit = run(
        "git", "-C", str(root), "rev-parse",
        "--verify", args.ref + "^{commit}",
    )

    def source(name):
        return subprocess.check_output(
            ["git", "-C", str(root), "show", f"{commit}:{name}"]
        )

    browser = source("browser.py").decode("utf-8")
    old = "from nimvex_updater import Updater"
    if browser.count(old) != 1:
        raise SystemExit("Stopped: expected exactly one source updater import.")
    browser = browser.replace(
        old, "from nimvex_rpm_updater import Updater", 1
    )
    ast.parse(browser)

    updater = source("nimvex_rpm_updater.py")
    ast.parse(updater.decode("utf-8"))

    spec = source("packaging/nimvex.spec").decode("utf-8")
    versions = re.findall(r"(?m)^Version:\s+(\S+)\s*$", spec)
    if len(versions) != 1:
        raise SystemExit("Stopped: unexpected Version field.")
    version = versions[0]

    spec, count = re.subn(
        r"(?m)^Release:.*$",
        f"Release:        {args.release}%{{?dist}}",
        spec,
    )
    if count != 1:
        raise SystemExit("Stopped: unexpected Release field.")

    parent = Path.home() / "Projects/nimvex-builds"
    parent.mkdir(parents=True, exist_ok=True)
    build = Path(tempfile.mkdtemp(
        prefix=f"nimvex-{version}-{args.release}-{commit[:8]}-",
        dir=parent,
    ))
    for name in ("BUILD", "BUILDROOT", "RPMS", "SOURCES", "SPECS", "SRPMS"):
        (build / name).mkdir()

    stage = build / "staging" / f"nimvex-{version}"
    (stage / "assets").mkdir(parents=True)
    (stage / "browser.py").write_text(browser, encoding="utf-8")
    (stage / "nimvex_rpm_updater.py").write_bytes(updater)

    paths = {
        "License": "License",
        "nimvex.desktop": "packaging/nimvex.desktop",
        "nimvex.repo": "packaging/nimvex.repo",
        "RPM-GPG-KEY-nimvex": "packaging/keys/RPM-GPG-KEY-nimvex",
    }
    for destination, origin in paths.items():
        (stage / destination).write_bytes(source(origin))

    assets = run(
        "git", "-C", str(root), "ls-tree",
        "-r", "--name-only", commit, "--", "assets/",
    ).splitlines()
    if not assets:
        raise SystemExit("Stopped: no committed assets found.")
    for name in assets:
        path = stage / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(source(name))

    launcher = stage / "nimvex"
    launcher.write_text(
        '#!/bin/sh\n'
        'exec /usr/bin/python3 /usr/share/nimvex/browser.py "$@"\n'
    )
    launcher.chmod(0o755)

    subprocess.run(
        ["desktop-file-validate", str(stage / "nimvex.desktop")],
        check=True,
    )

    with tarfile.open(
        build / "SOURCES" / f"nimvex-{version}.tar.gz", "w:gz"
    ) as archive:
        archive.add(stage, arcname=stage.name)

    spec_path = build / "SPECS/nimvex.spec"
    spec_path.write_text(spec)

    subprocess.run(
        ["rpmbuild", "--define", f"_topdir {build}",
         "-ba", str(spec_path)],
        check=True,
    )

    rpms = list((build / "RPMS").rglob("*.rpm"))
    srpms = list((build / "SRPMS").glob("*.src.rpm"))
    if len(rpms) != 1 or len(srpms) != 1:
        raise SystemExit(f"Stopped: unexpected package count in {build}")

    output = build / "output"
    output.mkdir()
    copied = []
    for package in (rpms[0], srpms[0]):
        target = output / package.name
        shutil.copy2(package, target)
        copied.append(target)

    rpm = copied[0]
    zip_path = output / f"Nimvex-{version}-{args.release}-Nobara-44.zip"
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
        archive.write(rpm, rpm.name)
    with ZipFile(zip_path) as archive:
        if archive.testzip() is not None:
            raise SystemExit("Stopped: ZIP verification failed.")

    identity = run("rpm", "-qp", str(rpm))
    files = run("rpm", "-qpl", str(rpm))
    required_payload = (
        "/usr/share/nimvex/nimvex_rpm_updater.py",
        "/etc/yum.repos.d/nimvex.repo",
        "/etc/pki/rpm-gpg/RPM-GPG-KEY-nimvex",
    )
    for name in required_payload:
        if name not in files.splitlines():
            raise SystemExit(f"Stopped: package is missing {name}")

    manifest = {
        "source_commit": commit,
        "package": identity,
        "signed": False,
        "files": files.splitlines(),
        "sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (*copied, zip_path)
        },
    }
    (output / "build-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )

    print(f"\nSource commit: {commit}")
    print(f"Package: {identity}")
    print(f"Artifacts: {output}")
    print("Packaged updater, assets, launcher, repository config, and public key.")
    print("UNSIGNED: signing and publication are still required.")
    print("Nothing installed or published.")


if __name__ == "__main__":
    main()
