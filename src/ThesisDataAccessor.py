from PartialDataAccessor import PartialDataAccessor
from DataSourceManager import DataSourceManager
import utils
import collections
import os
import jsonschema



class ThesisDataAccessor(PartialDataAccessor):
    '''
    A partial data accessor that implements lazy loading of data sources
    and generally encapsulates data access.
    '''

    def __init__(self, top, dataSourceLocationsFile):
        
        self.dataManager = DataSourceManager(top, dataSourceLocationsFile)

        # Set the transition behavior that governs attribute and item
        # access for a given PartialDataObject
        self._loadStateTransitions()    

    def _loadStateTransitions(self):
        '''
        The set of possible PartialDataObjects for this data set can be roughly described
        by a finite state automaton with .attribute and [item] edges. There are only six states
        in this FSA. This function, which should be called on initialization of an instance, defines
        the state transition functions for each state. States are numbered, so self._attrTransitionFunction[1],
        is executed on a PDO in state 1. It performs the proper operations with the given attribute and updates the state of the PDO.
        '''
        self._attrTransitionFunctions = [
            lambda pdo, name: self._updateStateFunc(self._fillType(pdo, name), (lambda pdo: 2 if pdo.getKwarg('type').isLeaf() else 1)),
            lambda pdo, name: self._updateState(self._fillType(pdo, name), 2),
            lambda pdo, name: self._updateState(self._fillAttrList(pdo, name), 2),
            lambda pdo, name: self._handleAttrLeaf(self._setDataSourceRef(self._fillType(pdo, name), pdo.getKwarg('id')), 4),
            lambda pdo, name: self._handleAttrLeaf(self._fillAttrDict(pdo, name), 4)
        ]

        self._itemTransitionFunctions = [
            None, # There are no valid [item] transitions for a PDO in state 0.
            lambda pdo, _id: self._updateState(self._fillId(pdo, _id), 3),
            lambda pdo, _id: self._handleAttrLeaf(self._convertAttrList(self._setDataSourceRef(pdo, _id)), 4),
            None, # There are no valid [item] transitions for a PDO in state 3.
            None # There are no valid [item] transitions for a PDO in state 4.
        ]

        # Really should be the same as the item transition functions, but those include unncessary
        # validations. E.g., when iterating, we know an id is in the given data type.
        self._iterTransitionFunctions = [
            None, # You cannot iterate over a PDO in state 0.
            lambda pdo, _id: self._updateState(self._fillIdUnsafe(pdo, _id), 3),
            lambda pdo, _id: self._handleAttrLeaf(self._convertAttrList(self._setDataSourceRef(pdo, _id)), 4),
            None, # You cannot iterate over a PDO in state 3.
            None # You cannot iterate over a PDO in state 4.
        ]

    def _fillType(self, pdo, name):
        '''
        Searches the type hierarchy from the PDO's current type to see if a subtype with 'name' exists.
        If not, raises an AttributeError.
        Returns a new PDO.
        '''
        try:
            return pdo.fill(**{'type': pdo.getKwarg('type').getSubtype(name)})            
        except KeyError:
            raise AttributeError("Type {0} not found in type {1}".format(name, pdo.getKwarg('type').name()))

    def _fillId(self, pdo, _id):
        '''
        Fills the id attribute in a PDO, or raises an error if the id does not exist for the PDO's type.
        Returns a new PDO.
        '''
        if _id in pdo.getKwarg('type').getIds():
            return pdo.fill(**{'id': _id})
        else:
            raise KeyError("Data for entity {0} not found in {1}".format(_id, pdo.getKwarg('type').name()))

    def _fillIdUnsafe(self, pdo, _id):
        '''
        Fills the id attribute in a PDO *without* checking for validity. Should be used in iteration only!
        Returns a new PDO.
        '''
        return pdo.fill(**{'id':_id})

    def _setDataSourceRef(self, pdo, _id):
        '''
        Given an id, sets the PDO's id argument and gives its data argument a reference to the data source
        of the PDO's current type (the data source is retrieved through the type node's data hook).
        Returns a new PDO.
        '''
        return pdo.fill(**{'id': _id, 'data': pdo.getKwarg('type').getData(_id)})

    def _fillAttrList(self, pdo, name):
        '''
        For a PDO with a data source but no idea, dumbly adds the given attribute to the PDO's 'data access path,'
        which is the PDO's args attribute.
        Returns a new PDO.
        '''
        return pdo.fill(*[name])

    def _fillAttrDict(self, pdo, name):
        '''
        Advances the PDO's data reference with the given attribute and returns a new PDO.
        '''
        return self._advanceAttrDict(pdo.fill(), name)

    def _advanceAttrDict(self, pdo, name):
        '''
        Attempts to advance the PDO's data reference using the given attribute. If no such
        attribute exists, raises a KeyError.
        Does *not* return a new PDO, since it is only called by other methods that do.
        '''
        try:
            return pdo.filled(**{'data': pdo.getKwarg('data')[name]})
        except KeyError:
            raise KeyError("Attribute {0} not found in data source {1}".format(name, pdo.getKwarg('type').name()))

    def _convertAttrList(self, pdo):
        '''
        Converts the PDOs blind 'data access path' into an actual data reference.
        '''
        for attr in pdo.args():
            self._advanceAttrDict(pdo, attr)
        return pdo

    def _handleAttrLeaf(self, pdo, state):
        '''
        Determines if the given PDO has reached an end state, in which no further attribute or item accesses
        are possible. If so, return the value in the PDO's data attribute.\
        Acts a wrapper around _updateState, since some states of the PDO access FSA have empty transitions.
        '''
        if isinstance(pdo.getKwarg('data'), str) or not isinstance(pdo.getKwarg('data'), collections.Container):
            # If we've reached the end, return a value
            return pdo.getKwarg('data')
        else:
            # Otherwise, update the state and return the PDO
            return self._updateState(pdo, state)

    def _updateStateFunc(self, pdo, f):
        '''
        Updates the state of a PDO given a function over that PDO. Only necessary because the attribute transition
        from state 0 is ambiguous depending on whether the attribute recieved is a data type or data source.
        '''
        return self._updateState(pdo, f(pdo))

    def _updateState(self, pdo, state):
        '''
        Updates the state of the given PDO.
        Does not create a new PDO.
        '''
        return pdo.filled(**{'state': state})

    def _getPdoAttr(self, pdo, name):
        '''
        Call the appropriate attribute transition function or, if none exists, raise an AttributeError.
        '''
        try:
            return self._attrTransitionFunctions[pdo.getKwarg('state')](pdo, name)
        except TypeError: # Raised by attempting to call None as a function
            raise AttributeError("{0} is not a valid attribute for {1}".format(name, pdo))

    def _getPdoItem(self, pdo, key):
        '''
        Call the appropriate item transition function or, if none exists, raise a KeyError.
        '''
        try:
            return self._itemTransitionFunctions[pdo.getKwarg('state')](pdo, key)
        except TypeError: # Raised by attempting to call None as a function
            raise KeyError("{0} is not a valid id for {1}".format(key, pdo))

    def _iterPdo(self, pdo):
        '''
        If the PDO is in an appropriate state (i.e. if it has outgoing [item] edges), return
        a generator over the ids for the PDO's current type.
        Or, if the current data type is a list, iterate over the items in the list
        '''
        try:
            for _id in pdo.getKwarg('type').getIds():
                yield self._iterTransitionFunctions[pdo.getKwarg('state')](pdo, _id)
        except TypeError: # Raised by attempting to call None as a function
            if isinstance(pdo.getKwarg('data'), collections.Sequence): # If data is pointing to a list, then iterate over it
                # This is hacky, but it will do. Really, the whole _iterPdo function should be redesigned to
                # handle this better.
                for i in range(len(pdo.getKwarg('data'))):
                    yield self._attrTransitionFunctions[4](pdo, i)
            else:
                raise KeyError("Cannot iterate over {0}".format(pdo))

    def _initPdo(self, pdo):
        '''
        Overridden from the base class. Initialize the PDO:
            type is the data source type of the PDO. It is initialized to the top-level data source type
            id is the PDO's current id. It is set to None to begin with, though it could be anything,
                since no one actually checks this value.
            data will hold a reference to a data source instance, once type is a data source and
                id is an actual id.
            state is 0. See the transition functions above.        
        '''
        return pdo.filled(**{'type':self.dataManager.root(), 'id': None, 'data': None, 'state': 0})

    def reset(self):
        print("Resetting...",end="")
        self.dataManager.reset()
        print("Done.")

# Usage: from ThesisDataAccessor import Accessor as data
Accessor = ThesisDataAccessor("../", "schema/locs.json")