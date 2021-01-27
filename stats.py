#!/usr/bin/env python3

import api
from collections.abc import Iterable
from statistics import mean, median
from sys import stderr, argv

# ------------------------------
# Config:
DEBUG = False
# ------------------------------


def printStats(storage):
    '''
    Collect some interesting stats to show off in console.
    '''
    # Data to collect:
    filesPerFolder = []

    # Collect data:
    for rmFile in storage.iterate_all():
        if rmFile.isFolder:
            filesPerFolder.append(len(rmFile.files))


    # Print collected data:

    # Folders:
    print('Files in folders:')
    folderFormat = '  ' + 4*'{:<14}'
    print(folderFormat.format(
        'TOTAL',
        'MEAN (AVG)',
        'MEDIAN',
        'TOTAL'
    ))
    print(folderFormat.format(
        '%d folders' % len(filesPerFolder),  # "TOTAL"
        '%.1f files' % mean(filesPerFolder),  # "MEAN (AVG)"
        '%.0f files' % median(filesPerFolder), # "MEDIAN"
        '%d files' % sum(filesPerFolder)  # "TOTAL"
    ))


if __name__ == '__main__':
    try:
        if len(argv) == 1:
            print(f'Usage: {argv[0]} <folder>', file=stderr)
            exit(1)

        print('Fetching file structure...\n')  # Prints to stderr to ignore this if piped into a text file
        storage = api.RmStorage(argv[1])
        print()
        printStats(storage)
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
