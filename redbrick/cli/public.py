"""Main file for CLI."""

import sys
import argparse
from typing import List, Optional, Any

import shtab

import redbrick
from redbrick.cli.command import (
    CLIConfigController,
    CLIInitController,
    CLICloneController,
    CLIInfoController,
    CLIExportController,
    CLIUploadController,
    CLIIReportController,
)
from redbrick.cli.cli_base import CLIInterface
from redbrick.utils.logging import logger


class CLIController(CLIInterface):
    """Main CLI Controller."""

    def __init__(self, command: argparse._SubParsersAction) -> None:
        """Initialize CLI command parsers."""
        self.config = CLIConfigController(
            command.add_parser(
                self.CONFIG,
                help="Setup the credentials for your CLI.",
                description="Setup the credentials for your CLI.",
            )
        )
        self.init = CLIInitController(
            command.add_parser(
                self.INIT,
                help="Create a new project",
                description="""
Create a new project. We recommend creating a new directory and naming it after your project,
initializing your project within the new directory.

```bash
$ mkdir new-project
$ cd new-project
$ redbrick init
```
            """,
            )
        )
        self.clone = CLICloneController(
            command.add_parser(
                self.CLONE,
                help="Clone an existing remote project to local",
                description="""
The project will be cloned to a local directory named after your `project name`.
                """,
            )
        )
        self.info = CLIInfoController(
            command.add_parser(
                self.INFO,
                help="Get a project's information",
                description="Get a project's information",
            )
        )
        self.export = CLIExportController(
            command.add_parser(
                self.EXPORT,
                help="Export data for a project",
                description="Export data for a project",
            )
        )
        self.upload = CLIUploadController(
            command.add_parser(
                self.UPLOAD,
                help="Upload files to a project",
                description="Upload files to a project",
            )
        )
        self.report = CLIIReportController(
            command.add_parser(
                self.REPORT,
                help="Generate an audit report for a project",
                description="""
Generate an audit report for a project. Exports a JSON file containing all actions & events
associated with every task, including:

- Who annotated the task
- Who uploaded the data
- Who reviewed the task
- and more.
""",
            )
        )

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
        elif args.command == self.UPLOAD:
            self.upload.handler(args)
        elif args.command == self.REPORT:
            self.report.handler(args)
        else:
            raise argparse.ArgumentError(None, "")


def cli_parser(
    only_parser: bool = True,
) -> Any:
    """Initialize argument parser."""
    parser = argparse.ArgumentParser(
        description="The RedBrick CLI offers a simple interface to quickly import and "
        + "export your images & annotations, and perform other high-level actions."
    )
    parser.add_argument("-v", "--version", action="version", version=redbrick.version())
    cli = CLIController(parser.add_subparsers(title="Commands", dest="command"))

    shtab.add_argument_to(parser, "--completion")

    if only_parser:
        return parser

    return parser, cli


def cli_main(argv: Optional[List[str]] = None) -> None:
    """CLI main handler."""
    parser: argparse.ArgumentParser
    cli: CLIController

    parser, cli = cli_parser(False)

    try:
        args = parser.parse_args(argv if argv is not None else sys.argv[1:])
        logger.debug(args)
    except KeyboardInterrupt:
        logger.warning("User interrupted")
    except argparse.ArgumentError as error:
        logger.warning(str(error))
        parser.print_help()
    else:
        try:
            cli.handle_command(args)
        except KeyboardInterrupt:
            logger.warning("User interrupted")
        except argparse.ArgumentError as error:
            message = str(error)
            if message:
                logger.warning(message)

            if args.command:
                actions = (
                    parser._get_positional_actions()  # pylint: disable=protected-access
                )
                if actions:
                    choices = actions[0].choices
                    if choices:
                        subparser = dict(choices).get(args.command)
                        if subparser:
                            subparser.print_usage()
                            sys.exit(1)

            parser.print_usage()
            sys.exit(1)


if __name__ == "__main__":
    cli_main()
