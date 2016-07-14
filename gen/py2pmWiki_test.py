#!/usr/bin/python
# coding=utf-8
from __future__ import print_function

import os
import sys
import py2pmWiki as pm

if __name__ == "__main__": 
    file_dir, file_name = os.path.split(sys.argv[0])
    group = pm.WikiFile.path_to_group(file_dir)
    title = pm.WikiFile.name_to_title(file_name)
    initial = os.path.join(file_dir, file_name)
    restored = os.path.join(
       pm.WikiFile.group_to_path(group),
       pm.WikiFile.title_to_name(title))
    print(os.path.normpath(initial))
    print(os.path.normpath(restored))
    print(group+"."+title)
