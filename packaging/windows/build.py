import ast
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def main():
    if sys.platform != "win32":
        raise SystemExit("Run this build on Windows or the Windows GitHub Actions runner.")

    source = subprocess.check_output(
        ["git", "show", "HEAD:browser.py"], cwd=ROOT
    ).decode("utf-8")

    original = (
        "from nimvex_updater import Updater\n"
        "window.updater = Updater(window, Path(__file__).resolve().parent)"
    )
    replacement = (
        "from windows_updates import add_update_menu\n"
        "add_update_menu(window)"
    )
    if source.count(original) != 1:
        raise SystemExit("Browser startup changed. Review the Windows updater replacement.")

    source = source.replace(original, replacement)
    ast.parse(source)

    with tempfile.TemporaryDirectory(prefix="nimvex-windows-") as directory:
        work = Path(directory)
        entry = work / "browser.py"
        entry.write_text(source, encoding="utf-8")

        (work / "windows_updates.py").write_text(
            'from PySide6.QtCore import QUrl\n'
            'from PySide6.QtGui import QDesktopServices\n'
            'from PySide6.QtWidgets import QMessageBox\n'
            '\n'
            'def add_update_menu(browser):\n'
            '    def open_releases():\n'
            '        QMessageBox.information(browser, "Windows preview updates",\n'
            '            "This preview does not install updates automatically.\\n"\n'
            '            "Download a newer Windows package from GitHub when available.\\n"\n'
            '            "Close Nimvex before replacing its application folder.")\n'
            '        QDesktopServices.openUrl(QUrl(\n'
            '            "https://github.com/HexandRoach/nimvex/releases"))\n'
            '    browser.browser_menu.addAction(\n'
            '        "Windows downloads / manual updates...", open_releases)\n',
            encoding="utf-8",
        )

        assets = work / "assets"
        assets.mkdir()
        for name in ("HexandRoach.png", "nimvex.png", "nimvex-logo.svg"):
            data = subprocess.check_output(
                ["git", "show", f"HEAD:assets/{name}"], cwd=ROOT
            )
            (assets / name).write_bytes(data)

        license_data = subprocess.check_output(
            ["git", "show", "HEAD:License"], cwd=ROOT
        )

        subprocess.run(
            [
                sys.executable, "-m", "PyInstaller",
                "--noconfirm", "--clean", "--onedir", "--windowed",
                "--name", "Nimvex",
                "--paths", str(work),
                "--add-data", f"{assets}:assets",
                "--distpath", str(work / "dist"),
                "--workpath", str(work / "build"),
                "--specpath", str(work),
                str(entry),
            ],
            cwd=work,
            check=True,
        )

        bundle = work / "dist" / "Nimvex"
        if not (bundle / "Nimvex.exe").is_file():
            raise SystemExit("Expected Nimvex.exe was not produced.")

        (bundle / "License").write_bytes(license_data)
        (bundle / "WINDOWS-PREVIEW.txt").write_text(
            "Nimvex Windows Preview - experimental, unsigned build.\n"
            "Extract the entire ZIP before opening Nimvex.exe.\n"
            "Keep all supporting files with the executable.\n"
            "Automatic updates are not supported in this preview.\n"
            "Windows browsing and persistence require manual testing.\n",
            encoding="utf-8",
        )

        output = ROOT / "windows-output"
        output.mkdir(exist_ok=True)
        archive = shutil.make_archive(
            str(output / "Nimvex-Windows-x64-preview"),
            "zip", root_dir=work / "dist", base_dir="Nimvex",
        )
        print(f"Created: {archive}")

if __name__ == "__main__":
    main()
