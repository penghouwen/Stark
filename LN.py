import os
import subprocess

root = os.path.abspath("/home/ln/A/Datasets/GOT-10K/")
dest = os.path.abspath("./data/got10k/train")


def isDir(x):
    p = os.path.join(root, x)
    return os.path.isdir(p)


dirs = list(filter(isDir, os.listdir(root)))
for d in dirs:
    split = os.path.join(root, d)
    items = os.listdir(split)
    for it in items:
        ind = os.path.join(split, it)
        outd = os.path.join(dest, it)
        subprocess.call(["ln", "-sf", ind, outd])

