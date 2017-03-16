import collections
import abc
import json

class PartialDataAccessor:
    '''
    Manages a dynamic set of PartialDataObjects to easily handle
    data that can be accessed in many different ways.
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _getPdoAttr(self, pdo, name):
        '''Delegate method for PartialDataObject attribute access.'''
        return

    @abc.abstractmethod
    def _getPdoItem(self, pdo, key):
        '''Delegate method for PartialDataObject item access.'''
        return

    @abc.abstractmethod
    def _iterPdo(self, pdo):
        '''Delegate method for PartialDataObject attribute access.'''
        return

    def _initPdo(self, pdo):
        '''Called upon the creation of new PartialDataObjects. Can be overloaded.'''
        return pdo

    def __getattr__(self, name):
        '''Create a new partial data object and simulate a getattr call.'''
        pdo = self._initPdo(type(self).PartialDataObject.fromPda(self))
        return getattr(pdo, name)

    def __getitem__(self, key):
        '''Create a new partial data object and simulate a getitem call.'''
        pdo = self._initPdo(type(self).PartialDataObject.fromPda(self))
        return pdo[key]

    def __str__(self):
        return type(self).__name__

    class PartialDataObject():
        '''
        Emulates partial-function-like behavior with the fill()
        method, while overloading .attribute and [item] behavior.
        Depends on a contract with a PartialDataAccessor to
        delegate .attribute, [item], and iter calls, which may
        either return values or new PartialDataObjects.
        Note that it is *not* a mutable mapping.
        '''
        @classmethod
        def fromPda(cls, partialDataAccessor, *args, **kwargs):
            '''
            Constructs a new PartialDataObject and
            sets the _pda parameter.
            '''
            obj = cls()
            obj._pda = partialDataAccessor
            obj._args = []
            obj._kwargs = {}
            return obj

        @classmethod
        def fromPdo(cls, partialDataObject, *args, **kwargs):
            '''
            Constructs a new PartialDataObject from the given
            object by setting the _pda parameter and extending
            args and kwargs.
            '''
            obj = cls.fromPda(partialDataObject._pda)
            obj._mergeArgs(partialDataObject, *args)
            obj._mergeKwargs(partialDataObject, **kwargs)
            return obj

        def _mergeArgs(self, pdo, *args):
            self._args = pdo._args.copy()
            self._args.extend(args)

        def _mergeKwargs(self, pdo, **kwargs):
            self._kwargs = pdo._kwargs.copy()
            self._kwargs.update(kwargs)

        def args(self):
            return self._args

        def kwargs(self):
            return self._kwargs

        def get(self, val):
            if type(val) == int:
                return self._args[val]
            else:
                return self._kwargs[val]

        def getArg(self, i):
            return self._args[i]

        def getKwarg(self, key):
            return self._kwargs[key]

        def fill(self, *args, **kwargs):
            '''
            Call the fromPdo constructor from an instance.
            This is useful because PartialDataAccessor subclasses
            will not have direct access to the PartialDataObject
            constructors.
            '''
            return type(self).fromPdo(self, *args, **kwargs)

        def filled(self, *args, **kwargs):
            '''
            Merge new args and kwargs without creating a new instance.
            In general, this is useful for a PDA's _initPdo method.
            '''
            self._args.extend(args)
            self._kwargs.update(kwargs)
            return self

        def __getattr__(self, name):
            '''
            Delegates to the PartialDataAcessor.
            '''
            return self._pda._getPdoAttr(self, name)

        def __getitem__(self, key):
            '''
            Delegates to the PartialDataAcessor.
            '''
            return self._pda._getPdoItem(self, key)

        def __iter__(self):
            '''
            Delegates to the PartialDataAcessor.
            '''
            return self._pda._iterPdo(self)

        def __len__(self):
            '''
            Simply call the iterator and get the number
            of elements. Efficiency is not a huge issue here.
            '''
            return len([key for key in self])

        def __str__(self):
            trim = (lambda s, l: s if len(s) <= l else "{0}...".format(s[:l]))
            args = [trim(repr(arg), 100) for arg in self._args]
            kwargs = {key: trim(repr(self._kwargs[key]), 100) for key in self._kwargs}
            return "PartialDataObject(accessor={0}, args={1}, kwargs={2})".format(self._pda, args, kwargs)

        def __repr__(self):
            return str(self)