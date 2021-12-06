"""Main file for CLI."""
import os
import sys
import argparse
from typing import List, Optional

from redbrick.common.cli import CLIInterface
from redbrick.cli.command import (
    CLIConfigController,
    CLIInitController,
    CLICloneController,
    CLIInfoController,
    CLIExportController,
)
from redbrick.utils.logging import print_error, print_warning


class CLIController(CLIInterface):
    """Main CLI Controller."""

    def __init__(self, command: argparse._SubParsersAction) -> None:
        """Initialize CLI command parsers."""
        self.config = CLIConfigController(command.add_parser(self.CONFIG))
        self.init = CLIInitController(command.add_parser(self.INIT))
        self.clone = CLICloneController(command.add_parser(self.CLONE))
        self.info = CLIInfoController(command.add_parser(self.INFO))
        self.export = CLIExportController(command.add_parser(self.EXPORT))

    def handle_command(self, args: argparse.Namespace) -> None:
        """CLI command main handler."""
        if args.command == self.CONFIG:
            self.config.handler(args)
        elif args.command == self.INIT:
            self.init.handler(args)
        elif args.command == self.CLONE:
            self.clone.handler(args)
        elif args.command == self.INFO:
            self.info.handler(args)
        elif args.command == self.EXPORT:
            self.export.handler(args)
        else:
            raise argparse.ArgumentError(None, "")


def cli_main(argv: Optional[List[str]] = None) -> None:
    """CLI main handler."""
    parser = argparse.ArgumentParser(description="RedBrick AI")
    command = parser.add_subparsers(title="Commands", dest="command")

    cli = CLIController(command)

    try:
        args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    except argparse.ArgumentError as error:
        print_warning(str(error))
        parser.print_help()
    else:
        try:
            cli.handle_command(args)
        except argparse.ArgumentError:
            parser.print_usage()
        except Exception as error:  # pylint: disable=broad-except
            if os.environ.get("REDBRICK_DEBUG"):
                raise error
            print_error(error)
            sys.exit(1)