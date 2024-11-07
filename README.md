# RandoFetch

Randomize your fetcher config for fun and profit!


<!-- [![PyPI - Version](https://img.shields.io/pypi/v/randofetch.svg)](https://pypi.org/project/randofetch)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/randofetch.svg)](https://pypi.org/project/randofetch) -->

---

**Table of Contents**

- [RandoFetch](#randofetch)
  - [Overview](#overview)
  - [Installation](#installation)
  - [License](#license)

## Overview 

Tired of choosing between different `fetcher` programs and different terminal images? RandoFetch will generate different commands for various fetchers for you.


RandoFetch is a simple script that reads a configuration file and generates a random command based on the config. In the config file, you should specify the fetcher(s) available on you system, and desired flags for the fetchers. 

there are a few helper tools in the script; adding and deleting images to rotate through using `add_images` and `remove_image` commands; listing images using the `list_images` command, and regenerating the default configuration among others.


## Installation

```console
pip install randofetch
```


## License

`randofetch` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
