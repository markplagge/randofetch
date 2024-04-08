# SPDX-FileCopyrightText: 2024-present Mark Plagge <mplagge@sandia.gov>
#
# SPDX-License-Identifier: MIT
import sys

if __name__ == "__main__":
    from randofetch.cli import randofetch

    sys.exit(randofetch())
