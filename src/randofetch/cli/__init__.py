# SPDX-FileCopyrightText: 2024-present Mark Plagge <mplagge@sandia.gov>
#
# SPDX-License-Identifier: MIT
from pathlib import Path
import click
import io
from randofetch.__about__ import __version__
from randofetch.cli.config import BaseConfig
from randofetch.cli.fetcher import Fetcher, FetcherSet, init_fetcher_list

_config_obj = BaseConfig()


class RichGroup(click.Group):
    def format_help(self, ctx, formatter):
        super().format_help(ctx, formatter)
        global _config_obj
        sio = io.StringIO()
        # console = rich.Console(file=sio, force_terminal=True)
        # console.print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:")
        caps = "Cache Path:\t"
        cops = "Config Path:\t"
        data_locs = click.style(
            f"{click.style(cops,fg=(15,200,90),bg='black',bold=True)}{click.style(_config_obj.app_config_path(),underline=True,bold=True)}\n",
            underline=True,
        )

        cache_locs = f"{click.style(caps,fg=(128,10,208),bg='black',bold=True,underline=True)}{click.style(_config_obj.app_data_path(),underline=True,bold=True)}\n"
        help_epi = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            + click.style(
                "On this platform, data is saved to:", fg="bright_blue", bold=True
            )
            + f"\n{data_locs}{cache_locs} ͍⃗⃡͜"
        )

        sio.write(help_epi)
        formatter.write(sio.getvalue())


@click.group(
    cls=RichGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(version=__version__, prog_name="randofetch")
@click.option(
    "--reset",
    "-r",
    is_flag=True,
    default=False,
    help="Reset config file with defaults. Implies --scan",
)
@click.option(
    "--scan",
    "-s",
    is_flag=True,
    default=False,
    help="Re-Scan images and fetchers using config file.",
)
@click.option("--disp", "-d", is_flag=True, default=False)
@click.option(
    "--timeout",
    "-t",
    default=2.0,
    help="When generating fetcher list, fetchers which take longer than this will not be used.",
)
def randofetch(reset: bool, scan: bool, disp: bool, timeout: float):
    """
    RandoFetch - Randomly run a fetcher program with a randomly selected image.

    RandoFetch stores data / cached information in the standard XDG
    This function is the main entry point for the randofetch command-line interface.



    If the reset flag is True, the function will regenerate the list of fetchers and images,
    and notify the user. If the scan flag is True, the function will re-scan and
    regenerate the list of fetchers.

    If the disp flag is True, the function will display the output of the fetcher program.
    The output is obtained by running the fetcher program silently and printing the result.

    The function also prints the paths to the YAML configuration file,
    the base configuration file, and the application configuration path.
    \f

    :param reset: A boolean flag indicating whether to reset the configuration to defaults.
    If this flag is True, the function will also set the scan flag to True.
    :type reset: bool

    :param scan: A boolean flag indicating whether to re-scan images and fetchers using the
    configuration file.
    :type scan: bool

    :param disp: A boolean flag indicating whether to display the output of the fetcher program.
    :type disp: bool

    """

    # Reset configuration to defaults. This is done in the BaseConfig object
    config = BaseConfig(
        reset_config=reset,
    )

    global _config_obj
    _config_obj = config
    _config_obj.app_data_path().mkdir(exist_ok=True)
    _config_obj.app_config_path().mkdir(exist_ok=True)
    if timeout != 2.0:
        _config_obj.fetch_max_latency = timeout
    if reset:
        # When config is reset, we need to regenerate the list of fetchers + images. Also, notifiy user
        click.secho("Regenerating config", fg="blue")
        scan = True
    if scan:
        # Only re-scan and regenerate list of fetchers
        click.secho("Scaning images", fg="green")
        reset_fn()

    fetcher_set = gen()
    if disp:
        click.secho("display")
        f: Fetcher = fetcher_set.fetcher
        r = f.run_silent()
        # rs = r.stdout.decode()
        click.secho(r)

    # print(config.yaml_config_file)
    # print(config._base_config_file)
    # print(config.app_config_path)


def reset_fn():
    fl = init_fetcher_list(_config_obj)

    fetcher_set = FetcherSet(
        reset=True,
        save_file=_config_obj.fset_save_file,
        fetcher_list=fl,
        max_time=_config_obj.fetch_max_latency,
    )
    print("Found timing: \n" "cmd \t\t\t\t time \n" + "-" * 40)
    for ts in fetcher_set.timing:
        print(f"{ts[0]} \t\t\t\t {ts[1]}")


def gen():
    fetcher_set = FetcherSet(reset=False, save_file=_config_obj.fset_save_file)
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
    """add_images Adds images to the configuration folder and configuration file.


    :param images: One or more image files - they need to be compatible with your fetcher.
    :type images: list[Path]
    :param link: Do we link the images or copy them to the folder?
    :type link: bool
    """

    def check_img(i: Path):
        return i.match("*.jpg", case_sensitive=False) or i.match(
            "*.png", case_sensitive=False
        )

    for i, imc in enumerate([check_img(im) for im in images]):
        if not imc:
            click.secho("Found non JPG or PNG image: ", fg="red", underline=True)
            click.secho(f"{images[i]}")
            click.confirm(
                "Continue anyway?", default=False, abort=True
            )  # @TODO  maybe support other image formats?

    for i in images:
        dest_path = Path(_config_obj.app_data_path()) / i.name
        if click.confirm(
            f"{'Link' if link else 'Copy'} {i} to {dest_path}?", abort=False
        ):
            if link:
                i.symlink_to(dest_path)
            else:
                dest_path.write_bytes(i.read_bytes())


@randofetch.command
def list_images():
    """
    List all images currently in the application data directory.

    This function is a Click command that lists all images currently in the application data directory. It does not take any arguments and does not return anything.

    The function iterates over the `image_list` attribute of the `CONFIG_OBJ` object, which is expected to be a list of image paths. It then prints each image path to the console.
    """
    for i in _config_obj.image_list:
        print(i)


@randofetch.command
@click.argument("image_name")
def remove_image(image_name):
    """remove_image Removes an image from the application data directory.

    :param image_name: Image name - check `list_images` to see a list of image names.
    :type image_name: str
    """
    im_path = Path(_config_obj.app_data_path / image_name)
    click.confirm(f"Delete file {im_path}?", abort=True)
    im_path.unlink()


if __name__ == "__main__":
    randofetch()  # pylint: disable=no-value-for-parameter
