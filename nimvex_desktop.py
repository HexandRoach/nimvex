import os
import shutil
import subprocess
from pathlib import Path


def repair_desktop_icon(root):
    root = Path(root).resolve()
    source = root / "assets" / "nimvex.png"
    if not source.is_file():
        raise FileNotFoundError(source)

    data_home = Path(
        os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local/share")
    )
    target = data_home / "icons/hicolor/256x256/apps/nimvex.png"
    desktop = data_home / "applications/nimvex.desktop"
    changed = False

    if not target.exists() or target.read_bytes() != source.read_bytes():
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        shutil.copyfile(source, temporary)
        temporary.replace(target)
        changed = True

    if desktop.is_file():
        original = desktop.read_text()
        lines = original.splitlines()
        in_main_group = False
        found_icon = False
        updated = []

        for line in lines:
            if line.startswith("[") and line.endswith("]"):
                if in_main_group and not found_icon:
                    updated.append("Icon=nimvex")
                    found_icon = True
                in_main_group = line == "[Desktop Entry]"

            if in_main_group and line.startswith("Icon="):
                line = "Icon=nimvex"
                found_icon = True

            updated.append(line)

        if in_main_group and not found_icon:
            updated.append("Icon=nimvex")

        result = "\n".join(updated) + "\n"
        if result != original:
            backup = desktop.with_name("nimvex.desktop.before-icon-fix")
            if not backup.exists():
                shutil.copy2(desktop, backup)
            temporary = desktop.with_name(desktop.name + ".tmp")
            temporary.write_text(result)
            temporary.replace(desktop)
            changed = True

    if changed:
        for name in ("kbuildsycoca6", "kbuildsycoca5"):
            command = shutil.which(name)
            if command:
                subprocess.run(
                    [command, "--noincremental"],
                    check=True,
                    timeout=60,
                )
                break

    return changed


if __name__ == "__main__":
    changed = repair_desktop_icon(Path(__file__).resolve().parent)
    print("Desktop icon repaired." if changed else "Desktop icon is already current.")
