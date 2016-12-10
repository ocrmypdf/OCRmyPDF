#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83
import os


def get_program(name):
    envvar = 'OCRMYPDF_' + name.upper()
    return os.environ.get(envvar, name)
