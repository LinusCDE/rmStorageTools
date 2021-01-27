#!/usr/bin/env python3

import api
from sys import stderr, argv

# ------------------------------
# Config:
DEBUG = False
# ------------------------------

if __name__ == '__main__':
    try:
        if len(argv) == 1:
            print(f'Usage: {argv[0]} <folder>', file=stderr)
            exit(1)

        print('Fetching file structure...\n')  # Prints to stderr to ignore this if piped into a text file
        storage = api.RmStorage(argv[1])

        print('IDs:')
        for file_id, rmFile in storage.rmfiles.items():
            if rmFile.isInTrash:
                continue
            print('%s: %s' % (file_id, rmFile.path()))
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
