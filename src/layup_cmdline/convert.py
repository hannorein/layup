#
# The `layup convert` subcommand implementation
#
import argparse
from layup_cmdline.layupargumentparser import LayupArgumentParser


def main():
    parser = LayupArgumentParser(
        prog="layup convert",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="This would convert orbits",
    )

    positionals = parser.add_argument_group("Positional arguments")
    positionals.add_argument(
        help="input orbit file",
        dest="input",
        type=str,
    )

    positionals.add_argument(
        help="orbit type to convert to [COM, BCOM, KEP, BKEP, CART, BCART]",
        dest="type",
        type=str,
    )

    optional = parser.add_argument_group("Optional arguments")
    optional.add_argument(
        "-c",
        "--chunksize",
        help="number of orbits to be processed at once",
        dest="c",
        type=int,
        default=10000,
        required=False,
    )
    optional.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite output file",
    )
    optional.add_argument(
        "--fo",
        "--format",
        help="format of input file",
        dest="fo",
        type=str,
        default="csv",
        required=False,
    )
    optional.add_argument(
        "-o",
        "--output",
        help="output file name. default path is current working directory",
        dest="o",
        type=str,
        default="converted_output",
        required=False,
    )

    args = parser.parse_args()

    return execute(args)


def execute(args):
    print("Hello world this would start convert")


if __name__ == "__main__":
    main()
