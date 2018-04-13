#!/usr/bin/env python

from __future__ import print_function
import os

aws_region = 'us-west-2'


def main():
    os.environ['SHALLOW_DIR'] = os.environ['PWD']
    os.environ['PROJECT'] = os.environ['LAMBCI_REPO'].split('/')[-1].lower()


if __name__ == '__main__':
    main()
