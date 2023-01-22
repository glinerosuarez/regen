#!/usr/local/bin/python

import argparse

from inject import injector


def train():

    context = injector.execution_context
    context.train()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--train",
        default=False,
        action="store_const",
        const=True,
        help="Train an agent while collecting new observations.",
    )

    args = parser.parse_args()

    if args.train:
        train()
