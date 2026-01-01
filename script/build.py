import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"
BACKEND_DIST = BACKEND / "dist"
FRONTEND_DIST = FRONTEND / "dist"
ROOT_DIST = ROOT / "dist"
BACKEND_DEVELOPMENT_TARGET_STATIC = BACKEND / "static"
TARGET_STATIC = BACKEND / "src/pushikoo/frontend-static"


def safe_rmdir(path: Path):
    if path.exists():
        print(f"Removing: {path}")  # remove
        shutil.rmtree(path)


def safe_copy(src: Path, dst: Path):
    print(f"Copying {src} -> {dst}")  # move
    shutil.copytree(str(src), str(dst))


def run(cmd, cwd, env=None):
    print(f"Running: {cmd}")  # run
    subprocess.run(cmd, shell=True, check=True, cwd=cwd, env=env)


def get_version() -> str:
    """Get version using hatch version command."""
    result = subprocess.run(
        ["hatch", "version"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def main():
    # Get version
    version = get_version()
    print(f"Building version: {version}")

    # if not (ROOT / ".git").exists():
    #    raise SystemExit("Error: must run in project root")

    # frontend build with version env var
    safe_rmdir(FRONTEND_DIST)
    build_env = os.environ.copy()
    build_env["VITE_APP_VERSION"] = version
    run("pnpm build", cwd=FRONTEND, env=build_env)

    # backend prepare
    safe_rmdir(ROOT_DIST)
    safe_rmdir(BACKEND_DIST)
    safe_rmdir(TARGET_STATIC)
    safe_rmdir(BACKEND_DEVELOPMENT_TARGET_STATIC)
    safe_copy(FRONTEND_DIST, BACKEND_DEVELOPMENT_TARGET_STATIC)
    safe_copy(FRONTEND_DIST, TARGET_STATIC)
    safe_rmdir(FRONTEND_DIST)

    # backend build
    run("uv build", cwd=BACKEND)
    safe_copy(BACKEND_DIST, ROOT_DIST)
    safe_rmdir(BACKEND_DIST)

    print(f"Done. Aval at {ROOT_DIST}")  # done


if __name__ == "__main__":
    main()
