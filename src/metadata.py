'''
A module for metadata access and manipulation code.
Could be reimplemented as a static class if desired.
'''

import json

# Path to the metadata file
METADATA_PATH = "../data/debates/metadata/metadata.json"

_metadata = None
calledLoad = False

def load():
    '''Attempts to load the metadata into the global variable metadata
    from the global METADATA_PATH.'''
    global _metadata
    global calledLoad
    try:
        with open(METADATA_PATH, 'r') as metadataFile:
            _metadata = json.load(metadataFile)
            calledLoad = True
    except FileNotFoundError:
        raise FileNotFoundError("Could not load metadata file at {0}. Has the file been moved?".format(METADATA_PATH))

def save():
    '''Saves the metadata object to the location at METADATA_PATH.
    Does not attempt to save if the file has not been previously loaded
    into memory.
    '''
    global _metadata
    if calledLoad:
        with open(METADATA_PATH, 'w') as metadataFile:
            json.dump(_metadata, metadataFile, indent=4)
        print("Metadata file saved to {0}.".format(METADATA_PATH))
    else:
        raise IOError("Cannot save; metadata has not been loaded.")

def getMetadata():
    if not calledLoad:
        load()
    return _metadata

def debateIds():
    '''Returns an iterable of debate ids.'''
    return getMetadata().keys()

def debates():
    '''Returns an iterable of debate metadata dicts.'''
    return getMetadata().values()

def metadata(debateId):
    '''Returns the metadata dict associated with debateId.'''
    try:
        return getMetadata()[debateId]
    except KeyError:
        raise KeyError("Could not find metadata for debateId {0}".format(debateId))

def isExcluded(debate):
    '''Returns true if the debate is marked excluded. Can pass a metadata dict or a debateId string.'''
    if type(debate) == str:
        debate = getMetadata()[debate]
    return 'exclude' in debate and debate['exclude'] == True

def exclusionReason(debate):
    '''Returns the exclusion reason for debate, or None if the debate is not excluded.
    Can pass a metadata dict or a debateId string.'''
    if type(debate) == str:
        debate = getMetadata()[debate]
    return debate['exclusionReason'] if isExcluded(debate) else None