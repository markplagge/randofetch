# SPDX-FileCopyrightText: 2024-present Mark Plagge <mplagge@sandia.gov>
#
# SPDX-License-Identifier: MIT
import os
from pathlib import Path
import click

from randofetch.__about__ import __version__
from randofetch.cli.config import BaseConfig, t_files
from randofetch.cli.fetcher import Fetcher, FetcherSet, init_fetcher_list

CONFIG_OBJ = BaseConfig()


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(version=__version__, prog_name="randofetch")
@click.option("--reset", "-r", is_flag=True, default=False)
@click.option("--disp", "-d", is_flag=True, default=False)
@click.pass_obj
def randofetch(ctx, reset: bool, disp):
    # t_files()
    config = BaseConfig(reset_config=reset)
    # tx = {}
    global CONFIG_OBJ
    CONFIG_OBJ = config
    CONFIG_OBJ.app_data_path.mkdir(exist_ok=True)
    CONFIG_OBJ.app_config_path.mkdir(exist_ok=True)
    if reset:
        print("GENERATED BASE CONFIG")
        reset_fn()
    fetcher_set = gen()
    if disp:
        click.secho("display")
        f: Fetcher = fetcher_set.fetcher
        r = f.run_silent()
        rs = r.stdout.decode()
        click.secho(rs)

    # print(config.yaml_config_file)
    # print(config._base_config_file)
    # print(config.app_config_path)


def reset_fn():
    fl = init_fetcher_list(CONFIG_OBJ)
    fetcher_set = FetcherSet(
        reset=True,
        save_file=CONFIG_OBJ.fset_save_file,
        fetcher_list=fl,
        max_time=CONFIG_OBJ.fetch_max_latency,
    )
    print("Found timing: \n" "cmd \t\t\t\t time \n" + "-" * 40)
    for ts in fetcher_set.timing:
        print(f"{ts[0]} \t\t\t\t {ts[1]}")


def gen():
    global CONFIG_OBJ
    fetcher_set = FetcherSet(reset=False, save_file=CONFIG_OBJ.fset_save_file)
    c = fetcher_set.get_cmd()
    click.echo(c)
    return fetcher_set


@randofetch.command
@click.argument(
    "images",
    nargs=-1,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        path_type=Path,
    ),
)
@click.option("--link", "-l", help="Link images instead of copy", default=False)
def add_images(images: list[Path], link: bool):
    global CONFIG_OBJ

    def check_img(i: Path):
        return i.match("*.jpg") or i.match("*.png")

    if not all([check_img(c) for c in images]):
        click.echo("Need jpg or png images")
        exit(1)

    for i in images:
        if check_img(i):
            dest_path = CONFIG_OBJ.app_data_path / i.name
            if click.confirm(
                f"{'Link' if link else 'Copy'} {i} to {dest_path}?", abort=False
            ):
                if link:
                    i.link_to(dest_path)
                else:
                    dest_path.write_bytes(i.read_bytes())


@randofetch.command
def list_images():

    for i in CONFIG_OBJ.image_list:
        print(i)


@randofetch.command
@click.argument("image_name")
def remove_image(image_name):
    im_path = Path(CONFIG_OBJ.app_data_path / image_name)
    click.confirm(f"Delete file {im_path}?", abort=True)
    im_path.unlink()


if __name__ == "__main__":
    randofetch()
