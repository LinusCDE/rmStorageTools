'''
Utilities regarding the reMarkable files.
This files has most code from https://github.com/LinusCDE/rmWebUiTools,
but was changed to read the local .metadata files
(tested with rmfakecloud, but xochitl should work as well)

TODO: Also accept ssh instead of just a folder
TODO: Consistent casing of names
TODO: Cleanups and more/corrected docs
'''

from collections.abc import Iterable
from datetime import datetime
import os
import json


class RmStorage:
    def __init__(self, source):
        self.source = source
        self.rmfiles = dict()  # id (str): RmFile instance, ...
        self.fetch()
        pass

    def fetch(self):
        '''
        source: Currently only a path to the folder containing the flat file structure
        (Should support some kind of ssh info in the future.)
        '''
        self.rmfiles.clear()

        for filename in os.listdir(self.source):
            if not filename.endswith('.metadata'):
                continue
            metadata_path = os.path.join(self.source, filename)
            metadata_json = json.load(open(metadata_path, 'r'))
            rmfile = RmFile(metadata_json)
            self.rmfiles[rmfile.id] = rmfile

        for rmfile in self.rmfiles.values():
            rmfile.update_hierarchical_data(self)

    def find_by_id(self, file_id: str):
        return self.rmfiles.get(file_id, None)

    def files_in_root(self):
        for rmfile in self.rmfiles.values():
            if rmfile.isInRoot:
                yield rmfile

    def files_in_trash(self):
        for rmfile in self.rmfiles.values():
            if rmfile.isInTrash:
                yield rmfile

    def iterate_all(self):
        folders_to_visit = []

        # Find base files and folders
        for rmfile in self.files_in_root():
            if rmfile.isFolder:
                folders_to_visit.append(rmfile)
            else:
                yield rmfile

        # Process until there are no unvisited folders
        while len(folders_to_visit) > 0:
            rmfolder = folders_to_visit.pop()
            yield rmfile
            for rmfile in rmfolder.files:
                if rmfile.isFolder:
                    folders_to_visit.append(rmfile)
                else:
                    yield rmfile


class RmFile:
    '''
    Representation of a file or folder on the reMarkable device.
    '''

    def __init__(self, metadata):
        # Given parameters:
        self.metadata = metadata
        self.parent = None  # Determined later

        # Hierachial data:
        # otherwise "DocumentType"
        self.isFolder = 'Type' in metadata and metadata['Type'] == 'CollectionType'
        self.files = [] if self.isFolder else None  # Determined later if folder

        # Easy access of common metadata:
        # Typo still exists on cloud side?
        self.name = metadata['VissibleName'] if 'VissibleName' in metadata else metadata['VisibleName']

        # Parent is either:
        # - The id of the folder
        # - A empty string if in root
        # - The string "trash" if trashed
        self.isInRoot = metadata['Parent'] == ''
        self.isInTrash = metadata['Parent'] == 'trash'
        self.parentId = metadata['Parent'] if not self.isInRoot and not self.isInTrash else None

        self.id = metadata['ID']
        self.isBookmarked = metadata['Bookmarked']
        self.modifiedTimestamp = datetime.strptime(
            metadata['ModifiedClient'], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()

        # Prevent faulty structures:
        if '/' in self.name:
            self.name = self.name.replace('/', '')

    def update_hierarchical_data(self, storage: RmStorage):
        # Find parent
        if self.parentId is not None:
            parent = None
            for rmfile in storage.rmfiles.values():
                if rmfile.id == self.parentId:
                    self.parent = rmfile
                    break

        # Find children/files
        if self.isFolder:
            self.files.clear()
            for rmfile in storage.rmfiles.values():
                if rmfile.parentId == self.id:
                    self.files.append(rmfile)

    def path(self, basePath=''):
        '''
        Returns the complete path including this file/folder.
        basePath may be provided and prepended.
        '''
        if basePath and not basePath.endswith('/'):
            basePath += '/'

        path = self.name
        parent = self.parent
        while parent:
            path = parent.name + '/' + path
            parent = parent.parent

        return basePath + path

    def parent_folder_path(self, basePath=''):
        '''
        Returns the current folder path that a file is in.
        A basePath may be provided and prepended.

        If in root, the basePath (default '') will be returned.
        '''
        if self.parent:
            if basePath and not basePath.endswith('/'):
                basePath += '/'
            return basePath + self.parent.path()
        else:
            basePath

    def __str__(self):
        return 'RmFile{name=%s}' % self.name

    def __repr__(self):
        return self.__str__()
