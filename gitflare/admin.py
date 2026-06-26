"""GitFlare admin CLI tool."""

import argparse
import sys
import httpx

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
    else:
        parser.print_help()


def create_repo(config, name: str, auth_mode: str):
    """Create a new repository."""
    from .git.repo import init_bare
    
    try:
        repo_path = init_bare(config.server.repos_path, name)
        print(f"✓ Repository '{name}' created at {repo_path}")
    except Exception as e:
        print(f"✗ Failed to create repository: {e}")
        sys.exit(1)


def list_repos(config):
    """List all repositories."""
    from .git.repo import list_repos
    
    repos = list_repos(config.server.repos_path)
    if repos:
        print("Repositories:")
        for repo in repos:
            print(f"  - {repo}")
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


if __name__ == "__main__":
    main()
