from pathlib import Path
from importlib import resources
from platformdirs import user_config_dir, user_data_dir
from randofetch import appname, appauthor
from ruamel.yaml import YAML


class BaseConfig:
    """Class that manages configuration for randofetch.
    Checks if XDG or defualt config file / path exists.
    If not, creates it, and copies the default config there.
    Manages XDG paths too.
    Finally, gathers images in IMAGE CONFIG.
    @TODO: Add the ability to overwrite image storage path."""

    _fetcher_config = None
    _config_path_ovr = None
    _data_path_ovr = None
    _base_config_file = None
    _config_dict = None

    fetch_max_latency = 2.1
    fetcher_save_name = "fetch.pkl"
    image_save_name = "image_cfg.pkl"
    image_list = []
    image_globs = ["*.jpg", "*.png", "*.bmp"]

    def __init__(
        self,
        config_path_ovr: Path | None = None,
        base_config_file_ovr: Path | None = None,
        reset_config: bool = False,
    ) -> None:
        """init. Creates a config folder and populates it with:
        1. A copy of the base_config (or base_config_file_ovr if specified)
        Args:
            config_path_ovr (Path | None, optional): _description_. Defaults to None.
            base_config_file_ovr (Path | None, optional): _description_. Defaults to None.
        """
        if config_path_ovr:
            self._config_path_ovr = config_path_ovr

        if base_config_file_ovr:
            self._base_config_file = base_config_file_ovr
        else:
            self._base_config_file = Path(
                str(resources.files("randofetch.config").joinpath("fetchers.yaml"))
            )
        if reset_config or not self.yaml_config_file.exists():
            self.yaml_config_file = self._base_config_file
        ils = []
        for glob in self.image_globs:
            for file in self.app_data_path().glob(glob):
                ils.append(str(file))
        ils = list(set(ils))
        self.image_list = [Path(i) for i in ils]

    # States:
    # 1. app_config has no yaml:
    # Create yaml in app_config
    # return yaml
    # 2. app_config has yaml:
    # return yaml
    # 3. reset config:
    # Do #1
    @property
    def fetcher_save_path(self) -> Path:
        return self.app_data_path() / self.fetcher_save_name

    @property
    def img_cfg_save_path(self) -> Path:
        return self.app_data_path() / self.image_save_name

    @staticmethod
    def _load_xdg(xdgp: Path | str) -> Path:
        """
        Loads the XDG directory for the application.

        This method retrieves the XDG directory for the application. The XDG directory is a standard directory for storing application-specific data.

        Args:
            xdgp (Path | str): The path to the XDG directory. If a string is provided, it will be converted to a Path object.

        Returns:
            Path: The loaded XDG directory as a Path object.
        """
        if isinstance(xdgp, str):
            xdgp = Path(xdgp)
        if not xdgp.exists():
            xdgp.mkdir()

        return xdgp

    @classmethod
    def app_config_path(cls) -> Path:
        """
        Returns the path to the XDG configuration directory for the application.

        This method retrieves the path to the XDG configuration directory for the application. The XDG configuration directory is a standard directory for storing application-specific configuration files.

        Args:
            cls (class): The class instance that calls this method.

        Returns:
            Path: The path to the XDG configuration directory for the application.
        """
        return cls._load_xdg(user_config_dir(appname, appauthor=appauthor))

    @classmethod
    def app_data_path(cls) -> Path:
        return cls._load_xdg(user_data_dir(appname, appauthor))

    @property
    def yaml_config_file(self) -> Path:
        """
        Returns the path to the YAML configuration file for the application.

        This method retrieves the path to the YAML configuration file for the application. If a custom configuration path has been specified, it will return that path. Otherwise, it will return the default configuration file path.

        Args:
            None

        Returns:
            Path: The path to the YAML configuration file for the application.
        """
        if self._fetcher_config:
            return self._fetcher_config
        fc = self.app_config_path() / "fetchers.yaml"
        return Path(fc)

    @yaml_config_file.setter
    def yaml_config_file(self, yaml_file: Path):
        """Sets the yaml configuration file for the app.
        Saves the config file to the `self.yaml_config_file` location."""
        yam_c = yaml_file.read_text()
        yam_dest = self.yaml_config_file
        yam_dest.write_text(yam_c)
        self._fetcher_config = yam_dest

    @property
    def config(self) -> dict:
        if self._config_dict:
            return self._config_dict
        yaml = YAML()
        cg: dict = yaml.load(self.yaml_config_file)

        self._config_dict = cg
        return cg

    @property
    def config_string(self) -> str:
        return self.yaml_config_file.read_text()

    @property
    def fetcher_configs(self):
        fetchers = self.config["fetchers"]
        return fetchers

    @property
    def image_configs(self):
        img_ms = self.config["image_methods"]
        return img_ms

    @property
    def fset_save_file(self) -> Path:
        return self.app_config_path() / self.fetcher_save_name


def clean_config(config_dict: dict) -> dict:
    """Cleans the configuration dictionary by splitting any cli flags that have spaces into seperate list entries.
    Goes through each entry in the config dict. If the value is a list, make sure the values of the list do not have spaces,
    since that breaks cli args. If the value is a dict, go into that dict and repeat."""

    for k, v in config_dict.items():
        if isinstance(v, list):
            new_list = []
            for list_entry in v:
                if " " in list_entry:
                    new_list.extend(list_entry.split())
                else:
                    new_list.append(list_entry)
            config_dict[k] = new_list
        elif isinstance(v, dict):
            config_dict[k] = clean_config(v)
    return config_dict


# def load_config(config_location: Path):
#    """Loads the configuration file for randofetch. This is a YAML file normally stored in"""
#
#
# def t_files():
#    print(resources.files("randofetch.config").joinpath("fetchers.yaml").read_text())
#
