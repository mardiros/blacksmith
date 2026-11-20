import os
import sys
from pathlib import Path
from typing import TextIO

import blacksmith
from blacksmith.domain.registry import registry
from blacksmith.entrypoints.cli import SubParser, cli_command


def safe_open(output: str) -> TextIO:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError(f"Output file {output} already exists")
    if not output_path.parent.is_dir():
        raise NotADirectoryError(f"Parent directory of {output} does not exist")
    if not output_path.parent.is_dir() or not os.access(output_path.parent, os.W_OK):
        raise PermissionError(f"Parent directory of {output} is not writable")
    return output_path.open("w")


def handler(
    scan_mods: list[str],
    sync: bool = False,
    async_: bool = False,
    output: str | None = None,
) -> None:
    blacksmith.scan(*scan_mods)

    if not any([sync, async_]):
        sync = async_ = True

    if output:
        stream = safe_open(output)
    else:
        stream = sys.stdout

    for client_name, resources in registry.clients.items():
        print()
        print(client_name)
        for resource_name, resource in resources.items():
            print("\t", resource_name, resource)

    try:
        if sync:
            print(f"Generating synchronous stubs and saving to {output}")

        if async_:
            print(f"Generating asynchronous stubs and saving to {output}")
    finally:
        stream.close()


@cli_command
def stub(subparsers: SubParser) -> None:
    stub_parser = subparsers.add_parser("stub", help="Generate stubs")
    stub_parser.add_argument(
        "--sync", action="store_true", help="Generate synchronous stubs"
    )
    stub_parser.add_argument(
        "--async",
        action="store_true",
        dest="async_",
        help="Generate asynchronous stubs",
    )
    stub_parser.add_argument("--output", type=str, help="Output file path")
    stub_parser.add_argument(
        "--scan",
        dest="scan_mods",
        action="append",
        type=str,
        required=True,
        help="module to scan to fill the blacksmith registry",
    )
    stub_parser.set_defaults(handler=handler)
