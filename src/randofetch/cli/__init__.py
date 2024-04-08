# SPDX-FileCopyrightText: 2024-present Mark Plagge <mplagge@sandia.gov>
#
# SPDX-License-Identifier: MIT
import click

from randofetch.__about__ import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=True)
@click.version_option(version=__version__, prog_name="randofetch")
def randofetch():
    click.echo("Hello world!")
