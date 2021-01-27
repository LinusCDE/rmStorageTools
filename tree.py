#!/usr/bin/env python3

import api
from sys import stderr, argv

# ------------------------------
# Config:
DEBUG = False
# ------------------------------


def printTree(rmFiles, prefix=(' '*4)):
    for index, rmFile in enumerate(rmFiles):
        if index == len(rmFiles) - 1 and not rmFile.isFolder:
            print('%s└── %s' % (prefix, rmFile.name))
        else:
            print('%s├── %s' % (prefix, rmFile.name))

        if rmFile.isFolder:
            printTree(rmFile.files, '%s│   ' % prefix)

    if len(rmFiles) == 0:
        print('%s└── <Empty>' % prefix)


if __name__ == '__main__':
    try:
        if len(argv) == 1:
            print(f'Usage: {argv[0]} <folder>', file=stderr)
            exit(1)

        print('Fetching file structure...\n', file=stderr)  # Prints to stderr to ignore this if piped into a text file
        storage = api.RmStorage(argv[1])
        root_files = list(storage.files_in_root())

        print('Remarkable file tree:')
        printTree(root_files)
    except Exception as ex:
        # Error handling:
        if DEBUG:
            raise ex
            exit(1)
        else:
            print('ERROR: %s' % ex, file=stderr)
            print(file=stderr)
            print('Please make sure your reMarkable is connected to this PC and you have enabled the USB Webinterface in "Settings -> Storage".', file=stderr)
            exit(1)
