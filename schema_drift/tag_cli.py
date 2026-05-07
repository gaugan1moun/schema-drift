"""CLI sub-commands for managing snapshot tags."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from schema_drift.tag_store import TagStore


def _get_store(args: argparse.Namespace) -> TagStore:
    return TagStore(Path(args.history_dir))


def cmd_list(args: argparse.Namespace) -> None:
    store = _get_store(args)
    if args.version:
        tags = store.get_tags(args.version)
        if tags:
            print(f"{args.version}: {', '.join(tags)}")
        else:
            print(f"{args.version}: (no tags)")
    else:
        for version in store.all_versions():
            tags = store.get_tags(version)
            print(f"{version}: {', '.join(tags)}")


def cmd_add(args: argparse.Namespace) -> None:
    store = _get_store(args)
    for tag in args.tags:
        store.add_tag(args.version, tag)
    print(f"Added tags {args.tags} to {args.version}")


def cmd_remove(args: argparse.Namespace) -> None:
    store = _get_store(args)
    for tag in args.tags:
        store.remove_tag(args.version, tag)
    print(f"Removed tags {args.tags} from {args.version}")


def cmd_search(args: argparse.Namespace) -> None:
    store = _get_store(args)
    versions = store.versions_with_tag(args.tag)
    if versions:
        for v in versions:
            print(v)
    else:
        print(f"No snapshots tagged '{args.tag}'")


def build_tag_parser(parent: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = parent.add_parser("tags", help="Manage snapshot tags")
    p.add_argument("--history-dir", default=".schema_history", metavar="DIR")
    sub = p.add_subparsers(dest="tag_cmd", required=True)

    ls = sub.add_parser("list", help="List tags")
    ls.add_argument("--version", default=None)
    ls.set_defaults(func=cmd_list)

    add = sub.add_parser("add", help="Add tags to a version")
    add.add_argument("version")
    add.add_argument("tags", nargs="+")
    add.set_defaults(func=cmd_add)

    rm = sub.add_parser("remove", help="Remove tags from a version")
    rm.add_argument("version")
    rm.add_argument("tags", nargs="+")
    rm.set_defaults(func=cmd_remove)

    search = sub.add_parser("search", help="Find versions by tag")
    search.add_argument("tag")
    search.set_defaults(func=cmd_search)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="schema-drift-tags")
    subs = parser.add_subparsers(dest="command")
    build_tag_parser(subs)
    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
