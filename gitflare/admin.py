"""GitFlare admin CLI tool."""

import argparse
import sys

from .config import load_config


def main():
    """Main entry point for gitflare-admin."""
    parser = argparse.ArgumentParser(description="GitFlare admin CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = load_config()

    if args.command == "repo":
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
    else:
        parser.print_help()


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
    from .git.repo import list_repos, get_metadata

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
    from .git.repo import get_metadata, save_metadata
    from .auth.tokens import generate_token as gen, hash_token

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


if __name__ == "__main__":
    main()
