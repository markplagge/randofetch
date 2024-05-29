import logging
import os
import pickle
import random
import shlex
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

import ruamel.yaml
import tqdm

from randofetch.cli.config import BaseConfig

logger = logging.getLogger(__name__)
Fetchtp = TypeVar("Fetchtp", bound="Fetcher")


class Fetcher:
    """Fetcher
    Class that represents and maintains a combination of a Fetcher program's path, arguments, and image file.
    This class is created once, and stored in a PKL file in the XDG_CONFIG_HOME path.
    """

    # name: str = "uwufetch"
    # path: str = "uwufetch"
    # args: str = "-c ~/.config/neofetch/config.conf"
    _args: str | None = None
    # extra_reqs: str | None = "s1083807"
    _extra_reqs: str | None = None
    needs_image: bool = False
    _cache = None
    #    needs_image: bool = False
    image_args = ""

    def __init__(
        self,
        name: str,
        path: str,
        args: str,
        extra_reqs: str | None = None,
        needs_image: bool = False,
    ):
        self.name = name
        self.path = path
        self.args = args
        self.extra_reqs = extra_reqs
        self.needs_image = needs_image

    @property
    def extra_reqs(self):
        return self._extra_reqs

    @extra_reqs.setter
    def extra_reqs(self, reqs: str | None):
        self._extra_reqs = reqs

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
            case _:
                pass

        r = subprocess.run(
            f"which {self.extra_reqs}", capture_output=True, shell=True
        ).returncode

        if r == 0:
            logger.info(
                f"Fetcher {self.name} ran `which {self.extra_reqs}` and got return code of {r}"
            )
        return r != 127

    def run(self, silent: bool = False):
        return subprocess.run(self.cmd, capture_output=silent, shell=True)

    def run_silent(self):
        if not self._cache:
            self._cache = self.run(True).stdout
        return self._cache

    @property
    def cmd(self):
        st = f"{self.image_args if self.image_args else ''} {self.main_args}"

        # need to validate more shellx quote / paths.. I was trying this out too:
        # s1 = f"{self.path}  " + shlex.quote(st)
        return f"{self.path}  " + st

    @staticmethod
    def clone(other: Fetchtp):
        f = Fetcher(
            name=other.name,
            path=other.path,
            args=other.args,
            extra_reqs=other.extra_reqs,
            needs_image=other.needs_image,
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
    _fetchers: list[Fetcher] = []
    _timing: list[float] = []
    _max_latency: float = 2.2

    def __init__(
        self,
        reset: bool,
        save_file: Path,
        fetcher_list: list[Fetcher] | None = None,
        max_time: float = 1.1,
    ):
        super().__init__()  # Why does my linter complain if I don't call this?
        self._mutable_fetchers: list[Fetcher] = []
        self.max_latency: float = max_time
        self.timing: list[tuple[str, float | bool]] = []
        reset = reset or not (save_file.exists())
        if not reset:
            with open(save_file, "rb") as pf:
                fetchers: list[Fetcher] = pickle.load(pf)
                self.fetchers = fetchers
        else:
            if fetcher_list is not None:
                self.init_fetchers(fetcher_list)
                with open(save_file, "wb") as f:
                    pickle.dump(self.fetchers, f)
            else:
                raise ValueError("If reset need a list of fetchers")

    @classmethod
    def _fetcher_list(cls, fl: list[Fetcher]):
        cls._fetchers = fl

    @property
    def fetchers(self):
        return self._fetchers

    @fetchers.setter
    def fetchers(self, fl: list[Fetcher]):
        FetcherSet._fetcher_list(fl)
        self._mutable_fetchers = fl

    def init_fetchers(self, fetchers: list[Fetcher]):
        def check_f(fetcher: Fetcher):
            start = time.perf_counter()
            if fetcher.exists():
                end = time.perf_counter()
                if fetcher.check_extras():
                    return fetcher, end - start
                else:
                    return False, end - start
            else:
                return False, False

        times: list[tuple[str, float | bool]] = []
        for f in tqdm.tqdm(fetchers):
            res, t = check_f(f)
            print(f)
            c: str = ""
            if isinstance(res, Fetcher):
                if t <= self.max_latency:
                    self.fetchers.append(res)
                else:
                    _, t = check_f(f)  # Run twice?
                    if t <= self.max_latency:
                        self.fetchers.append(res)
                c = res.cmd
            timing: float | bool = t if isinstance(t, float) else False
            times.append((c, timing))

        self.timing = times
        # Old threaded mode here.... not really needed...
        #        workers = []

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
            # Fail silently since this is a startup / shell program
            # @TODO: Raise an exception, and have the CLI manage error conditions
            exit(0)
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
                        mags = ""
                        for m in im.args:
                            if " " in m:
                                m = shlex.quote(m)
                            mags = f"{mags} {m}"
                            print(mags)

                        # mags = " ".join(im.args)
                        fx.image_args = mags.replace(
                            "{}", shlex.quote(str(image.absolute()))
                        )

                        fetchers.append(fx)
        else:
            fetchers.append(fetcher)
    return fetchers


if __name__ == "__main__":
    c = BaseConfig(reset_config=True)
    l = init_fetcher_list(c)
    [print(ll) for ll in l]
