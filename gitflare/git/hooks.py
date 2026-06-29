"""Git hooks support for GitFlare.

Git hooks are executable scripts placed in a bare repo's hooks/ directory.
GitFlare installs a pre-receive hook that enforces server-side rules.

Supported hooks:
  pre-receive  — runs before a push is accepted (can reject by exit 1)
  post-receive — runs after a push is accepted (for notifications)
  update       — runs once per ref being updated
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("gitflare.hooks")

PRE_RECEIVE_HOOK = """\
#!/bin/sh
# GitFlare pre-receive hook
# Exit non-zero to reject the push.
# Add custom validation below.

while read oldrev newrev refname; do
    # Reject force pushes to main/master
    case "$refname" in
        refs/heads/main|refs/heads/master)
            if [ "$oldrev" != "0000000000000000000000000000000000000000" ]; then
                if [ "$newrev" = "0000000000000000000000000000000000000000" ]; then
                    echo "ERROR: Deleting main/master branch is not allowed" >&2
                    exit 1
                fi
            fi
            ;;
    esac
done

exit 0
"""

POST_RECEIVE_HOOK = """\
#!/bin/sh
# GitFlare post-receive hook
# This hook runs after a push is accepted.
# Add notifications, CI triggers, etc. below.
# Logging is handled by GitFlare's access log.
"""

UPDATE_HOOK = """\
#!/bin/sh
# GitFlare update hook
# Runs once per ref being updated (like pre-receive but per-ref).
# $1 = refname, $2 = oldrev, $3 = newrev
"""


def install_hooks(repo_path: Path) -> dict[str, bool]:
    """Install default GitFlare hooks into a bare repo.

    Returns dict of hook_name -> installed.
    """
    hooks_dir = repo_path / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    installed = {}

    for name, script in [
        ("pre-receive", PRE_RECEIVE_HOOK),
        ("post-receive", POST_RECEIVE_HOOK),
        ("update", UPDATE_HOOK),
    ]:
        hook_path = hooks_dir / name
        hook_path.write_text(script)
        hook_path.chmod(0o755)
        installed[name] = True
        logger.debug("Installed hook %s for %s", name, repo_path.name)

    return installed


def list_hooks(repo_path: Path) -> list[dict[str, str]]:
    """List installed hooks in a bare repo."""
    hooks_dir = repo_path / "hooks"
    if not hooks_dir.exists():
        return []

    hooks = []
    for hook_file in sorted(hooks_dir.iterdir()):
        if hook_file.is_file() and not hook_file.name.endswith(".sample"):
            hooks.append({
                "name": hook_file.name,
                "executable": "true" if hook_file.stat().st_mode & 0o111 else "false",
            })
    return hooks


def remove_hook(repo_path: Path, hook_name: str) -> bool:
    """Remove a specific hook from a bare repo."""
    hook_path = repo_path / "hooks" / hook_name
    if hook_path.exists() and hook_path.is_file():
        hook_path.unlink()
        logger.debug("Removed hook %s from %s", hook_name, repo_path.name)
        return True
    return False


def run_hook(repo_path: Path, hook_name: str, stdin_data: str = "") -> dict:
    """Run a hook script manually and return the result.

    This is useful for testing hooks or running them outside of git.
    """
    hook_path = repo_path / "hooks" / hook_name
    if not hook_path.exists():
        return {"returncode": -1, "stdout": "", "stderr": f"Hook {hook_name} not found"}

    result = subprocess.run(
        [str(hook_path)],
        input=stdin_data.encode() if stdin_data else None,
        capture_output=True,
        timeout=30,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout.decode("utf-8", errors="replace"),
        "stderr": result.stderr.decode("utf-8", errors="replace"),
    }
