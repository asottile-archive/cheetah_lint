# -*- coding: utf-8 -*-
import io


def read_file(filename):
    with io.open(filename) as f:
        return f.read()
