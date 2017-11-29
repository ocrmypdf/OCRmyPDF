#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83

import sys


def main():
    if sys.argv[-1] == '--version':
        print('qpdf version 7.0.0')
        sys.exit(0)
    print('qpdf dummy')
    sys.exit(2)


if __name__ == '__main__':
    main()
