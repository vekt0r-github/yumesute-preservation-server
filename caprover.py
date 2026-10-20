"""CapRover adapter. Keeps upstream setup explicit and uses an external database."""
import os
from pathlib import Path
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "vendor/server-of-dreams/config.yml"


def required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Set {name} in CapRover App Configs > Environmental Variables")
    return value


def configure_database():
    if not CONFIG.is_file():
        raise RuntimeError("Installation not prepared. Run: python caprover.py prepare")
    config = yaml.safe_load(CONFIG.read_text())
    database = config["database"]
    database.update(
        host=required("YUMESUTE_DB_HOST"),
        port=int(os.getenv("YUMESUTE_DB_PORT", "5432")),
        database=os.getenv("YUMESUTE_DB_NAME", "yumesute"),
        username=os.getenv("YUMESUTE_DB_USER", "yumesute"),
        password=required("YUMESUTE_DB_PASSWORD"),
    )
    # Only update the database connection; preserve accounts and other settings.
    temp = CONFIG.with_suffix(".yml.tmp")
    temp.write_text(yaml.safe_dump(config), encoding="utf-8")
    temp.chmod(0o600)
    temp.replace(CONFIG)


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("start", "prepare", "doctor"):
        raise RuntimeError("Usage: python caprover.py {start|prepare|doctor} [additional arguments]")
    action = sys.argv[1]
    args = sys.argv[2:]
    if action == "prepare":
        subprocess.run([sys.executable, "server.py", "prepare", "--data-dir", "/app/data", *args], check=True, cwd=ROOT)
        configure_database()
        print("Preparation complete. Start/restart the CapRover app.", flush=True)
        return
    configure_database()
    if action == "doctor":
        subprocess.run([sys.executable, "server.py", "doctor", *args], check=True, cwd=ROOT)
        return
    public = required("YUMESUTE_PUBLIC_HOST")
    cmd = [
        sys.executable, "server.py", "start", "--no-docker", "--no-browser",
        "--host", os.getenv("YUMESUTE_BIND_HOST", "0.0.0.0"),
        "--public-host", public, *args,
    ]
    os.execv(sys.executable, cmd)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"CapRover setup: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
