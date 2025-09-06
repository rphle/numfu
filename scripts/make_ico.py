import argparse
from pathlib import Path

from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("input")
parser.add_argument("-o", "--output")
parser.add_argument(
    "-s",
    "--sizes",
    nargs="+",
    default=[16, 32, 48, 64, 128, 256],
    type=int,
)
args = parser.parse_args()

infile = Path(args.input)
outfile = Path(args.output) if args.output else infile.with_suffix(".ico")

img = Image.open(infile)
sizes = [(s, s) for s in args.sizes]
img.save(outfile, sizes=sizes)
