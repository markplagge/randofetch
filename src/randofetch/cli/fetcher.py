from dataclasses import dataclass
import logging
from pathlib import Path
import os
import pickle
import copy
import tqdm
import ruamel.yaml
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from randofetch.cli.config import BaseConfig
import time

logger = logging.getLogger(__name__)


class Fetcher:
    """Fetcher
    Class that represents and maintains a combination of a Fetcher program's path, arguments, and image file.
    This class is created once, and stored in a PKL file in the XDG_CONFIG_HOME path.
    """

    name: str = "uwufetch"
    path: str = "uwufetch"
    args: str = "-c ~/.config/neofetch/config.conf"
    _args: str | None = None
    args_iterm: str | None = "-c ~/.config/neofetch/config.conf"
    extra_reqs: str | None = "s1083807"
    _cache = None
    needs_image: bool = False
    image_args = ""

    def __init__(
        self,
        name,
        path,
        args,
        extra_reqs: str | None = None,
    ):
        self.name = name
        self.path = path
        self.args = args
        self.extra_reqs = extra_reqs

    @property
    def main_args(self):

        if self._args is None:
            if self.args is not None:
                self._args = ""
                if isinstance(self.args, list):
                    self._args = " ".join(self.args)
                else:
                    self._args = self.args
            else:
                self.args = ""
                self._args = ""

        return self._args

    def exists(self) -> bool:
        r = subprocess.run(self.path, shell=True, capture_output=True).returncode
        print(f"Result for {self.name} / {self.path}: {r}")
        if self.path == "chafa":
            return r != 127
        else:
            return r == 0

    def check_extras(self):
        match self.extra_reqs:
            case "iterm":
                return "ITERM" in "\n ".join(list(os.environ.keys()))
        r = subprocess.run(
            f"which {self.extra_reqs}", capture_output=True, shell=True
        ).returncode

        return r != 127 or r == 0

    def run(self, silent=False):
        return subprocess.run(self.cmd, capture_output=silent, shell=True)

    def run_silent(self):
        if not self._cache:
            self._cache = self.run(True).stdout
        return self._cache

        return self.run(silent=True)

    @property
    def cmd(self):
        st = (
            f"{self.path} {self.image_args if self.image_args else ''} {self.main_args}"
        )
        return st

    @classmethod
    def clone(cls, other):
        f = Fetcher(
            name=other.name,
            path=other.path,
            args=other.args,
            extra_reqs=other.extra_reqs,
        )
        return f

    def __str__(self):
        return self.cmd


@dataclass()
class ImageMethod:
    name: str = "chafa"
    caller: str = "fastfetch"

    args: str = " --chafa-color-space RGB --chafa-fg-only False"

    def check_caller(self, other: Fetcher):
        return other.name == self.caller


class FetcherSet:
    fetchers = []
    timing: list = []

    def __init__(
        self,
        reset: bool,
        save_file: Path,
        fetcher_list: list | None = None,
        max_time: float = 1.1,
    ):
        self.max_latency = max_time
        reset = reset or not (save_file.exists())
        if not reset:
            with open(save_file, "rb") as pf:
                fetchers = pickle.load(pf)
                self.fetchers = fetchers
        else:
            if fetcher_list is not None:
                self.init_fetchers(fetcher_list)
                with open(save_file, "wb") as f:
                    pickle.dump(self.fetchers, f)
            else:
                raise ValueError(f"If reset need a list of fetchers")

    def init_fetchers(self, fetchers: list[Fetcher]):

        workers = []

        def check_f(fetcher):
            start = time.perf_counter()
            if fetcher.exists():
                end = time.perf_counter()
                if fetcher.check_extras():
                    return fetcher, end - start
                else:
                    return False, end - start
            else:
                return False, False

        times = []
        for f in tqdm.tqdm(fetchers):
            res, t = check_f(f)
            print(f)
            if isinstance(res, Fetcher):
                if t <= self.max_latency:
                    self.fetchers.append(res)
                else:
                    _, t = check_f(f)  # Run twice?
                    if t <= self.max_latency:
                        self.fetchers.append(res)
                c = res.cmd
            else:
                c = ""

            times.append((c, t))  # type: ignore

        self.timing = times

        # with ThreadPoolExecutor(20) as e:
        #     for fetcher in fetchers:
        #         fa = e.submit(check_f, fetcher)
        #         workers.append(fa)

        #     for fr in tqdm.tqdm(as_completed(workers)):
        #         results = fr.result()
        #         fetch_ok = results[0]
        #         fetch_time = results[1]

        #         if isinstance(fetch_ok, Fetcher):
        #             if fetch_time <= self.max_latency:
        #                 self.fetchers.append(fetcher)

        # if fetcher.exists() and fetcher.check_extras():

        # self.fetchers.append(fetcher)
        # else:
        #    print(f"{fetcher.name}{fetcher.path=} Not found!?")

        print(f"Found {len(self.fetchers)}")
        # Py 3.11 compatibility:
        fm = "\n".join([f.cmd for f in self.fetchers])
        print(fm)

    @property
    def fetcher(self):
        f = self.fetchers[random.randint(0, len(self.fetchers) - 1)]
        if f is None:
            print("ERRROROROROROROROROR")
        return f

    def run_fetcher(self):
        self.fetcher.run

    def get_cmd(self):
        return self.fetcher.cmd

    def print_cmd(self):
        print(self.fetcher.cmd)


def init_imagem_list(base_config: BaseConfig) -> list[ImageMethod]:
    im_dict = base_config.image_configs
    im_list: list[ImageMethod] = []
    for im_name, params in im_dict.items():
        method = ImageMethod(name=im_name, caller=params["caller"], args=params["args"])
        im_list.append(method)
    return im_list


def init_fetcher_list(base_config: BaseConfig):
    fetchers = []

    yaml = ruamel.yaml.YAML()
    yaml.register_class(Fetcher)
    ycfg = yaml.load(base_config.yaml_config_file)
    fetcher_configs = ycfg["fetchers"]

    image_methods = init_imagem_list(base_config)

    def check_fim(fetcher: Fetcher):
        t = time.perf_counter()
        for im in image_methods:
            if im.check_caller(fetcher):
                return True
        return False

    for fetcher in fetcher_configs:
        if fetcher.needs_image and check_fim(fetcher):
            for im in image_methods:
                if im.check_caller(fetcher):
                    for image in base_config.image_list:
                        fx = Fetcher.clone(fetcher)
                        mags = " ".join(im.args)
                        fx.image_args = mags.replace("{}", str(image.absolute()))
                        fetchers.append(fx)
        else:
            fetchers.append(fetcher)
    return fetchers


if __name__ == "__main__":
    c = BaseConfig(reset_config=True)
    l = init_fetcher_list(c)
    [print(ll) for ll in l]
