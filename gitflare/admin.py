"""GitFlare admin CLI tool."""

import argparse
import getpass
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx
import keyring

from .config import load_config

SERVICE_PREFIX = "gitflare"
CREDENTIAL_HELPER = "gitflare"


def main():
    """Main entry point for gitflare-admin."""
    parser = argparse.ArgumentParser(description="GitFlare admin CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Auth commands
    login_parser = subparsers.add_parser("login", help="Store credentials for a GitFlare host")
    login_parser.add_argument("url", help="GitFlare server URL (e.g. http://yourhost:3000)")

    logout_parser = subparsers.add_parser("logout", help="Remove credentials for a GitFlare host")
    logout_parser.add_argument("url", help="GitFlare server URL")

    # Repo commands
    repo_parser = subparsers.add_parser("repo", help="Repository management")
    repo_subparsers = repo_parser.add_subparsers(dest="repo_command")

    # repo create
    create_parser = repo_subparsers.add_parser("create", help="Create a new repository")
    create_parser.add_argument("name", help="Repository name")
    create_parser.add_argument("--auth", choices=["ssh", "token", "both"], default="ssh", help="Auth mode")

    # repo list
    repo_subparsers.add_parser("list", help="List all repositories")

    # repo delete
    delete_parser = repo_subparsers.add_parser("delete", help="Delete a repository")
    delete_parser.add_argument("name", help="Repository name")

    # Token commands
    token_parser = subparsers.add_parser("token", help="Token management")
    token_subparsers = token_parser.add_subparsers(dest="token_command")

    # token generate
    gen_parser = token_subparsers.add_parser("generate", help="Generate an access token")
    gen_parser.add_argument("repo", help="Repository name")

    # token revoke
    revoke_parser = token_subparsers.add_parser("revoke", help="Revoke all tokens for a repo")
    revoke_parser.add_argument("repo", help="Repository name")

    # SSH key commands
    ssh_parser = subparsers.add_parser("ssh-key", help="SSH key management")
    ssh_subparsers = ssh_parser.add_subparsers(dest="ssh_command")

    # ssh-key add
    add_key_parser = ssh_subparsers.add_parser("add", help="Add an SSH public key")
    add_key_parser.add_argument("key", help="SSH public key (e.g. ssh-ed25519 AAAA...)")

    # ssh-key list
    ssh_subparsers.add_parser("list", help="List all SSH keys")

    # ssh-key remove
    remove_key_parser = ssh_subparsers.add_parser("remove", help="Remove an SSH key by ID")
    remove_key_parser.add_argument("key_id", help="Key ID (from ssh-key list)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = load_config()

    if args.command == "login":
        login(args.url)
    elif args.command == "logout":
        logout(args.url)
    elif args.command == "repo":
        if args.repo_command == "create":
            create_repo(config, args.name, args.auth)
        elif args.repo_command == "list":
            list_repos(config)
        elif args.repo_command == "delete":
            delete_repo(config, args.name)
        else:
            repo_parser.print_help()
    elif args.command == "token":
        if args.token_command == "generate":
            generate_token(config, args.repo)
        elif args.token_command == "revoke":
            revoke_tokens(config, args.repo)
        else:
            token_parser.print_help()
    elif args.command == "ssh-key":
        if args.ssh_command == "add":
            add_ssh_key(args.key)
        elif args.ssh_command == "list":
            list_ssh_keys()
        elif args.ssh_command == "remove":
            remove_ssh_key(args.key_id)
        else:
            ssh_parser.print_help()
    else:
        parser.print_help()


def login(url: str):
    """Store credentials for a GitFlare host."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = parsed.port
    scheme = parsed.scheme or "http"

    if port:
        host_display = f"{host}:{port}"
    else:
        host_display = host

    service = f"{SERVICE_PREFIX}:{host_display}"

    # Prompt for token
    token = getpass.getpass("Token: ")
    if not token:
        print("✗ No token provided")
        sys.exit(1)

    # Validate against server
    verify_url = f"{scheme}://{host_display}/admin/auth/verify"
    try:
        resp = httpx.get(verify_url, params={"repo": "_", "token": token}, timeout=10)
        if resp.status_code == 404:
            pass
        elif resp.status_code == 200:
            pass
        elif resp.status_code == 401:
            print("✗ Invalid token")
            sys.exit(1)
        else:
            print(f"✗ Unexpected response from server: {resp.status_code}")
            sys.exit(1)
    except httpx.ConnectError:
        print(f"✗ Could not connect to {verify_url}")
        sys.exit(1)

    # Store in keyring
    keyring.set_password(service, "gitflare", token)
    print(f"✓ Token stored in system keychain for {host_display}")

    # Register credential helper in ~/.gitconfig
    gitconfig = Path.home() / ".gitconfig"
    credential_section = f'[credential "{scheme}://{host_display}"]'
    helper_line = f"\thelper = {CREDENTIAL_HELPER}"

    if gitconfig.exists():
        content = gitconfig.read_text()
    else:
        content = ""

    if credential_section in content:
        lines = content.split("\n")
        new_lines = []
        in_section = False
        helper_found = False
        for line in lines:
            if line.strip() == credential_section.strip():
                in_section = True
                new_lines.append(line)
            elif in_section and line.startswith("\thelper"):
                new_lines.append(helper_line)
                helper_found = True
                in_section = False
            elif in_section and (line.startswith("[") or line.strip() == ""):
                if not helper_found:
                    new_lines.append(helper_line)
                in_section = False
                new_lines.append(line)
            else:
                new_lines.append(line)
        if in_section and not helper_found:
            new_lines.append(helper_line)
        content = "\n".join(new_lines)
    else:
        content = content.rstrip() + f"\n\n{credential_section}\n{helper_line}\n"

    gitconfig.write_text(content)
    print(f"✓ Registered git-credential-gitflare for {scheme}://{host_display}")


def logout(url: str):
    """Remove credentials for a GitFlare host."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = parsed.port
    scheme = parsed.scheme or "http"

    if port:
        host_display = f"{host}:{port}"
    else:
        host_display = host

    service = f"{SERVICE_PREFIX}:{host_display}"

    # Erase from keyring
    try:
        keyring.delete_password(service, "gitflare")
    except keyring.errors.PasswordDeleteError:
        pass
    print(f"✓ Credentials removed from keychain for {host_display}")

    # Remove from ~/.gitconfig
    gitconfig = Path.home() / ".gitconfig"
    if gitconfig.exists():
        content = gitconfig.read_text()
        credential_section = f'[credential "{scheme}://{host_display}"]'

        if credential_section in content:
            lines = content.split("\n")
            new_lines = []
            skip = False
            for line in lines:
                if line.strip() == credential_section.strip():
                    skip = True
                    continue
                if skip and (line.startswith("[") or line.strip() == ""):
                    skip = False
                if not skip:
                    new_lines.append(line)
            gitconfig.write_text("\n".join(new_lines))

    print("✓ Removed credential helper entry from ~/.gitconfig")


def create_repo(config, name: str, auth_mode: str):
    """Create a new repository."""
    from .git.repo import init_bare

    try:
        repo_path = init_bare(config.server.repos_path, name, auth_mode=auth_mode)
        print(f"✓ Repository '{name}' created at {repo_path}")
        print(f"  Auth mode: {auth_mode}")
    except Exception as e:
        print(f"✗ Failed to create repository: {e}")
        sys.exit(1)


def list_repos(config):
    """List all repositories."""
    from .git.repo import get_metadata, list_repos

    repos = list_repos(config.server.repos_path)
    if repos:
        print("Repositories:")
        for repo in repos:
            meta = get_metadata(config.server.repos_path, repo)
            auth = meta.auth_mode if meta else "unknown"
            print(f"  - {repo} (auth: {auth})")
    else:
        print("No repositories found.")


def delete_repo(config, name: str):
    """Delete a repository."""
    from .git.repo import delete_repo

    if delete_repo(config.server.repos_path, name):
        print(f"✓ Repository '{name}' deleted")
    else:
        print(f"✗ Repository '{name}' not found")
        sys.exit(1)


def generate_token(config, repo_name: str):
    """Generate an access token for a repository."""
    from .auth.tokens import generate_token as gen
    from .auth.tokens import hash_token
    from .git.repo import get_metadata, save_metadata

    meta = get_metadata(config.server.repos_path, repo_name)
    if not meta:
        print(f"✗ Repository '{repo_name}' not found")
        sys.exit(1)

    token = gen()
    hashed = hash_token(token)
    meta.tokens.append(hashed)
    save_metadata(config.server.repos_path, repo_name, meta)

    print(f"✓ Token generated for '{repo_name}'")
    print(f"  Token: {token}")
    print("  Store this securely. It will not be shown again.")


def revoke_tokens(config, repo_name: str):
    """Revoke all tokens for a repository."""
    from .git.repo import get_metadata, save_metadata

    meta = get_metadata(config.server.repos_path, repo_name)
    if not meta:
        print(f"✗ Repository '{repo_name}' not found")
        sys.exit(1)

    count = len(meta.tokens)
    meta.tokens = []
    save_metadata(config.server.repos_path, repo_name, meta)

    print(f"✓ Revoked {count} token(s) for '{repo_name}'")


def add_ssh_key(key: str):
    """Add an SSH public key."""
    from .auth.ssh import add_key

    try:
        key_id = add_key(key)
        print(f"✓ SSH key added (ID: {key_id})")
    except ValueError as e:
        print(f"✗ {e}")
        sys.exit(1)


def list_ssh_keys():
    """List all SSH keys."""
    from .auth.ssh import list_keys

    keys = list_keys()
    if keys:
        print("SSH Keys:")
        for k in keys:
            comment = k["comment"] or "(no comment)"
            print(f"  [{k['id']}] {k['key_type']} {comment}")
    else:
        print("No SSH keys found.")


def remove_ssh_key(key_id: str):
    """Remove an SSH key by ID."""
    from .auth.ssh import remove_key

    if remove_key(key_id):
        print(f"✓ SSH key {key_id} removed")
    else:
        print(f"✗ Key {key_id} not found")
        sys.exit(1)


if __name__ == "__main__":
    main()
