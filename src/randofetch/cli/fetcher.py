from pathlib import Path
import os
import pickle
import copy
import yaml
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed


class Fetcher:
    """Fetcher
    Class that represents and maintains a combination of a Fetcher program's path, arguments, and image file.
    This class is created once, and stored in a PKL file in the XDG_CONFIG_HOME path.
    """

    name: str = "uwufetch"
    path: str = "uwufetch"
    args: str = "-c ~/.config/neofetch/config.conf"
    args_iterm: str | None = "-c ~/.config/neofetch/config.conf"
    extra_reqs: str | None = "s1083807"
    _cache = None

    def __init__(
        self,
        name,
        path,
        args,
        args_iterm: str | None = None,
        extra_reqs: str | None = None,
    ):
        self.name = name
        self.path = path

        self.args = args
        self.args_iterm = args_iterm
        self.extra_reqs = extra_reqs

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
        return self.run(silent=True)

    @property
    def cmd(self):
        return f"{self.path} {self.args}"


class FetcherSet:
    known_fetchers = [
        #       {
        #           "name": "uwufetch",
        #           "path": "uwufetch",
        #           "args": "-c ~/.config/neofect/config.confg",
        #           'extra_reqs': 'zsh'
        #       },
        {
            "name": "uwufetch_pic",
            "path": "uwufetch",
            "args": "-i {}",
        },
        # {"name": "hyfetch", "path": "hyfetch", "args": "-m rgb"},
        {
            "name": "hyfetch_f",
            "path": "hyfetch",
            "args": "-m rgb --c-overlay -b fastfetch",
            "extra_reqs": "fastfetch",
        },
        # {"name": "fastfetch", "path": "fastfetch", "args": ""},
        # {
        #    "name": "FF_chafa",
        #    "path": "fastfetch",
        #    "args": "--chafa  ~/.config/neofetch/i_1.jpg --chafa-color-space RGB --chafa-fg-only False",
        #    "extra_reqs": "chafa",
        # },
        {
            "name": "FF_chafa",
            "path": "fastfetch",
            "args": "--chafa {}  --chafa-color-space RGB --chafa-fg-only False --disable-linewrap false",
            "extra_reqs": "chafa",
        },
        # {
        #    "name": "FFiterm",
        #    "path": "fastfetch",
        #    "args": "--iterm {} --disable-linewrap true   --logo-width 80 --logo-preserve-aspect-ratio true",
        #    "extra_reqs": "iterm",
        # },
        {
            "name": "FF_SIX",
            "path": "fastfetch",
            "args": "--sixel {} --disable-linewrap false --logo-width 20  --logo-preserve-aspect-ratio true",
        },
        # {
        #    "name": "neofetch_c",
        #    "path": "neofetch",
        #    "args": "--source {} --iterm2 --crop_mode fit --size 400px  --loop",
        #    "extra_reqs": "iterm",
        # },
        # {
        #    "name": "neofetch_it",
        #    "path": "neofetch",
        #    "args": "--iterm2 --crop_mode fill --loop",
        #    "extra_reqs": "iterm",
        # },
        #        {
        #            "name": "neofetch",
        #            "path": "neofetch",
        #            "args": "",
        #        },
    ]
    fetchers = []
    images = []

    def __init__(self, reset: bool, save_path: Path | None = None):
        if save_path is None:
            save_path = Path(os.environ["XDG_CONFIG_HOME"]) / "neofetch"

        img_path = save_path / "imgs.pkl"
        save_path = save_path / "fetch.pkl"

        if save_path.exists() and not reset:
            with open(save_path, "rb") as pf:
                fetchers = pickle.load(pf)
                self.fetchers = fetchers
        if img_path and img_path.exists() and not reset:
            with open(img_path, "rb") as f:
                images = pickle.load(f)
                self.images = images

        else:
            if img_path is not None:
                self.init_fetchers(img_path, save_path)

    def init_fetchers(self, img_path, save_path: Path):
        self.fetchers = []
        self.images = []
        p_path = Path(os.environ["XDG_CONFIG_HOME"]) / "neofetch"
        pics = [p for p in p_path.glob("*.jpg")] + [p for p in p_path.glob("*.png")]
        print(f"Found {pics=}")
        pre_fetch = []

        for kf in self.known_fetchers:
            if "{}" in kf["args"]:
                print("Adding image to fetchers")
                for pic in pics:
                    self.images.append(str(pic.absolute()))
                    new_f = copy.deepcopy(kf)
                    new_f["args"] = new_f["args"].replace("{}", str(pic.absolute()))

                    pre_fetch.append(new_f)
            else:
                pre_fetch.append(kf)
        print("Image fetchers generated...")
        fs = [Fetcher(**d) for d in pre_fetch]
        workers = []

        def check_f(fetcher):
            if fetcher.exists() and fetcher.check_extras():
                return fetcher
            else:
                return False

        print(f"{len(fs)=}")
        os = "\n".join([f.name for f in fs])
        print(os)
        with ThreadPoolExecutor(20) as e:
            for fetcher in fs:
                fa = e.submit(check_f, fetcher)
                workers.append(fa)

            for fr in as_completed(workers):
                fetcher = fr.result()
                if isinstance(fetcher, Fetcher):
                    self.fetchers.append(fetcher)

                    # if fetcher.exists() and fetcher.check_extras():

                    # self.fetchers.append(fetcher)
                    # else:
                    #    print(f"{fetcher.name}{fetcher.path=} Not found!?")

        print(f"Found {len(self.fetchers)}")
        # Py 3.11 compatibility:
        fm = "\n".join([f.cmd for f in self.fetchers])
        print(fm)

        # print(f"{'\n'.join([f.cmd for f in self.fetchers])}")
        with open(save_path, "wb") as pf:
            pickle.dump(self.fetchers, pf)
        with open(img_path, "wb") as pf:
            pickle.dump(self.images, pf)

    @property
    def fetcher(self):
        f = self.fetchers[random.randint(0, len(self.fetchers) - 1)]
        if f is None:
            print("ERRROROROROROROROROR")
        return f

    @property
    def image(self):
        return self.images[random.randint(0, len(self.images) - 1)]

    def run_fetcher(self):
        self.fetcher.run

    def get_cmd(self):
        return self.fetcher.cmd

    def print_cmd(self):
        print(self.fetcher.cmd)
