#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83
import sys

def main():
    if sys.argv[1] == '--version':
        print('0.5')
        sys.exit(0)

    print("Only supports --version")
    sys.exit(1)


if __name__ == '__main__':
    main()
