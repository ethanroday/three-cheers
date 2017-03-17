class TypeNode():
    '''
    An object representing a node in a type hierarchy.
    _datahook and _idshook are optional callables that can be
    passed to get the instance data (or just an iterable of ids)
    for this data type.
    '''

    def __init__(self, parent, name, _datahook=None, _idshook=None):
        self._parent = parent
        self._name = name
        self._children = {}
        self._datahook = _datahook
        self._idshook = _idshook

    def name(self):
        '''Return this node's name.'''
        return self._name

    def parent(self):
        '''Return this node's parent node.'''
        return self._parent

    def child(self, name):
        '''Attempt to return a child node named name.'''
        return self._children[name]

    def children(self):
        '''Return an iterable of this node's children.'''
        return self._children.values()

    def add(self, name, datahook=None, idshook=None):
        '''Add a child node with the given parameters.'''
        node = TypeNode(self, name, datahook, idshook)
        return self.addNode(node)

    def addNode(self, node):
        '''Add a pre-initialized child node.'''
        self._children[node.name()] = node
        node._parent = self
        return node

    def isTop(self):
        '''Return true if this node has no parent.'''
        return self._parent is None

    def isLeaf(self):
        '''Return true if this node has no children.'''
        return len(self._children) == 0

    def getSubtype(self, name):
        '''
        Search for a type with the given name in this subtree of the
        hierarchy. If none is found, raise a KeyError.
        '''
        node = self._search(name)
        if node is None:
            raise KeyError("Node with name {0} not found".format(name))
        else:
            return node

    def _search(self, name):
        '''
        Perform a depth-first search for a type with the given name.
        If none if found, return None.
        '''
        for child in self._children.values():
            if child.name() == name:
                return child
            else:
                n = child._search(name)
                if n != None:
                    return n

    def setDataHook(self, datahook):
        '''
        Sets this type's datahook, which is a function that takes a node and an id
        and returns this data type's data for the given id.
        '''
        self._datahook = datahook

    def setIdsHook(self, idshook):
        '''
        Sets this type's idshook, which is a function that takes a node and
        returns an iterable of the ids that are defined for this data type.
        '''
        self._idshook = idshook

    def getData(self, dataId):
        '''
        Call this type's data hook with the given id to get this data type's data
        for the given id. Or, if no data hook has been set, raise an AttributeError.
        '''
        if self._datahook is None:
            raise AttributeError("TypeNode {0} has no data.".format(self.name()))
        else:
            return self._datahook(self, dataId)

    def getIds(self):
        '''
        Call this type's id hook to get an iterable of ids that are defined for
        this data type. Or, if no id hook has been set, raise an AttributeError.
        '''
        if self._idshook is None:
            raise AttributeError("TypeNode {0} has no ids.".format(self.name()))
        else:
            return self._idshook(self)

    def __str__(self):
        if self.isTop():
            s = ""
        else:
            s = str(self.parent()) + " -> "
        return s + self.name()

    def __repr__(self):
        return "TypeNode({0})".format(self)
