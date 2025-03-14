#
# The `layup predict` subcommand implementation
#
import argparse
from layup_cmdline.layupargumentparser import LayupArgumentParser


def main():
    parser = LayupArgumentParser(
        prog="layup predict",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="This would start predict",
    )
    optional = parser.add_argument_group("Optional arguments")
    optional.add_argument(
        "-p",
        "--print",
        help="Prints statement to terminal.",
        dest="p",
        action="store_true",
        required=False,
    )

    args = parser.parse_args()

    return execute(args)


def execute(args):
    if args.p:
        print("print statement used for predict")
    else:
        print("Hello world this would start predict")


if __name__ == "__main__":
    main()
