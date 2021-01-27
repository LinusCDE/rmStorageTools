#!/usr/bin/env python3
'''
Export - Exports all files of the remarkable onto your PC as pdfs.

Info: If a file is already exported, it will get skipped by default.
'''


import api

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from os import makedirs, utime, unlink
from os.path import exists, getmtime, join, dirname
from sys import stderr

import rmrl

# ------------------------------
# Config:
DEBUG = False
# ------------------------------


def exportTo(storage, targetFolderPath, onlyNotebooks, onlyBookmarked, updateFiles, ignoreErrors, onlyPathPrefix=None):
    if not exists(targetFolderPath):
        makedirs(targetFolderPath)
        print('INFO: Created target folder')

    # Preprocessing filterPath:
    if onlyPathPrefix is not None:
        if onlyPathPrefix.startswith('/'):
            onlyPathPrefix = onlyPathPrefix[1:]
        onlyPathPrefix = onlyPathPrefix.lower()
        if onlyPathPrefix == '':
            onlyPathPrefix = None

    exportableFiles = list(
        filter(lambda rmFile: rmFile.isFolder is False, storage.iterate_all()))

    # Apply filter:
    if onlyPathPrefix is not None:
        exportableFiles = list(filter(lambda rmFile: rmFile.path(
        ).lower().startswith(onlyPathPrefix), exportableFiles))

    # Filter for only notebooks if requested:
    if onlyNotebooks:
        exportableFiles = list(
            filter(lambda rmFile: rmFile.isNotebook, exportableFiles))

    # Filter for only bookmared if requested:
    if onlyBookmarked:
        exportableFiles = list(
            filter(lambda rmFile: rmFile.isBookmarked, exportableFiles))

    totalExportableFiles = len(exportableFiles)

    lastDirectory = None
    for i, exportableFile in enumerate(exportableFiles):

        # Announce directory change:
        directory = exportableFile.parent_folder_path()
        if(directory != lastDirectory):
            print('INFO: Current folder: %s' %
                  ('<reMarkable Document Root>' if not directory else directory))
            lastDirectory = directory

        # Get full path:
        path = exportableFile.path(targetFolderPath)
        if not path.endswith('.pdf'):
            path += '.pdf'

        # Create necessary directories:
        parentDir = exportableFile.parent_folder_path(targetFolderPath)
        if parentDir:  # May be None in the root
            makedirs(parentDir, exist_ok=True)

        # Check if file needs to be downloaded and output appropriate messages:
        skipFile = False
        if exists(path):
            # Existing exported file:
            if updateFiles:
                if int(getmtime(path)) < int(exportableFile.modifiedTimestamp):
                    # Update outdated export:
                    print('INFO: [%d/%d] Updating file \'%s\'...' %
                          (i+1, totalExportableFiles, exportableFile.name))
                else:
                    # Skip file that is up-to-date:
                    skipFile = True
                    print('WARN: [%d/%d] Skipping unchanged file \'%s\'...' %
                          (i+1, totalExportableFiles, exportableFile.name))
            else:
                # Don't override files. Regardless of date:
                skipFile = True
                print('INFO: [%d/%d] Skipping file \'%s\' (already exists in your target folder)...' %
                      (i+1, totalExportableFiles, exportableFile.name))

        if not exists(path):
            print('INFO: [%d/%d] Exporting \'%s\'...' %
                  (i+1, totalExportableFiles, exportableFile.name))

        # Export file if necessary:
        if not skipFile:
            try:
                zip_path = join(storage.source, f'{exportableFile.id}.zip')
                with rmrl.render(zip_path) as pdf_stream:
                    with open(path, 'wb') as file_stream:
                        while len(buffer := pdf_stream.read(8*1024)) > 0:
                            file_stream.write(buffer)
                # Use timestamp from the reMarkable device
                utime(path, (exportableFile.modifiedTimestamp,
                             exportableFile.modifiedTimestamp))
            except Exception as e:
                print('ERROR: Failed to export \'%s\'' % exportableFile.name)
                if exists(path):
                    unlink(path)
                if not ignoreErrors:
                    raise e


if __name__ == '__main__':
    # Disclaimer:
    print('DISCLAIMER: Please be aware that this puts the STRAIN of creating exported pdf files on YOUR REMARKABLE DEVICE rather than this computer.\n'
          'This can lead to UNEXPECTED BEHAVIOUR when many and/or big files are being exported.\n'
          'I WON\'T TAKE ANY RESPONSIBILITY for potential damage this may induce!\n', file=stderr)

    # Argument parsing:
    ap = ArgumentParser(
        description=__doc__,
        formatter_class=RawDescriptionHelpFormatter)

    ap.add_argument(
        'source_folder', help='Folder that contains remarkables flat file structure')
    ap.add_argument('target_folder',
                    help='Base folder to put the exported files in')

    ap.add_argument(
        '-n', '--only-notebooks',
        action='store_true', default=False, help='Skips all files except notebooks')

    ap.add_argument(
        '-b', '--only-bookmarked',
        action='store_true', default=False, help='Skips all files except bookmarked')

    ap.add_argument(
        '-f', '--only-path-prefix', metavar='path',
        default='', help='Skips all files that DON\'T starts with the given path (case-insensitive)')

    ap.add_argument(
        '-u', '--update',
        action='store_true', default=False, help='Overrides/Updates all updated files. Does not remove deleted files!')

    ap.add_argument(
        '-i', '--ignore-errors',
        action='store_true', default=False, help='Continues the export even when a file failed to export!')

    args = ap.parse_args()
    targetFolder, onlyNotebooks, onlyBookmarked, updateFiles, ignoreErrors, onlyPathPrefix = args.target_folder, args.only_notebooks, args.only_bookmarked, args.update, args.ignore_errors, args.only_path_prefix

    # Print info regarding arguments:
    if updateFiles:
        print('INFO: Updating files that have been changed recently. (Does not delete old files.)')
    if onlyNotebooks:
        print('INFO: Export only notebooks.')
    if onlyBookmarked:
        print('INFO: Export only bookmarked files.')
    if onlyPathPrefix:
        print('INFO: Only exporting files whose path begins with given filter (case insensitive).')

    try:
        # Actual process:
        # Prints to stderr to ignore this if piped into a text file
        print('INFO: Fetching file structure...')
        storage = api.RmStorage(args.source_folder)

        exportTo(storage, targetFolder, onlyNotebooks, onlyBookmarked,
                 updateFiles, ignoreErrors, onlyPathPrefix)
        print('Done!')
    except KeyboardInterrupt:
        print('Cancelled.')
        exit(0)
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
