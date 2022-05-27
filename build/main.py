from src.build import build
from src.build_single import build_single
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", '-l', help="Use local mode", action="store_true")
    parser.add_argument("--single", '-s', help="For single content", action="store_true")
    parser.add_argument("--file", '-f', help="File to be rendered ", action="store")
    args = parser.parse_args()
    if args.single:
        build_single(args.file)
    else:
        build(args.local)

