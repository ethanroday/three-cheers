import os

import jsonschema

import utils
from TypeNode import TypeNode


class DataSourceManager():
    def __init__(self, top, dataSourceLocationsFile):
        self.top = top
        self.locsFile = os.path.join(top, dataSourceLocationsFile)
        self._loadTypes()

    ##############################################
    ############### INITIALIZATION ###############

    def _loadTypes(self):
        # Get the data source data (i.e. the meta-metadata)
        locs = utils.getJSON(self.locsFile)

        # Get the schema for the locs file
        locsSchemaFile = os.path.join(self.top, locs['schemaDir'], locs['schema'])
        locsSchema = utils.getJSON(locsSchemaFile)

        # Validate the schema and locs
        #jsonschema.Draft4Validator.check_schema(locsSchema)
        #jsonschema.Draft4Validator(locsSchema, format_checker=jsonschema.FormatChecker()).validate(locs)

        # If no errors, then set the locs, along with the schemaDir and dataDir
        self.schemaDir = locs['schemaDir']
        self.dataDir = locs['dataDir']
        self.locations = locs['dataSources']

        # Create the data source type hierarchy and set id and data hooks where appropriate
        self._root = TypeNode(None, "rootType")
        for dataSource in self.locations:
            dataTypeName = self.locations[dataSource]['dataType']
            try:
                dataTypeNode = self._root.child(dataTypeName)
            except KeyError:
                dataTypeNode = self._root.add(dataTypeName)
            dataSourceNode = TypeNode(dataTypeNode, dataSource, \
                _datahook=(lambda node, _id: self.getDataSourceInstance(node.name(), _id)), \
                _idshook=(lambda node: self.getDataSourceIds(node.name())))
            dataTypeNode.addNode(dataSourceNode)
            if 'hasIds' in self.locations[dataSource]:
                dataTypeNode.setIdsHook((lambda node, child=dataSourceNode: child.getIds()))

        # Ensure that all top-level data types have an id source
        noIds = [dataType for dataType in self._root.children() if dataType._idshook == None]
        if len(noIds) != 0:
            raise AttributeError("The following data types do not have id sources: {0}".format([dataType.name() for dataType in noIds]))

        # Create an empty dictionary which will store the actual data from the data sources
        self.data = {}

    def reset(self):
        self._loadTypes()

    ##############################################
    ################ LAZY LOADING ################

    def loadDataSourceIds(self, dataSourceType):
        '''
        Given a data source, load all of the ids for that data source.
        This should only be called if the data source is completely uninitialized.
        If it's a single data source, then load the entire data source.
        Otherwise, just get the list of ids from the filenames in the directory.
        '''
        if self.isSingle(dataSourceType):
            self.loadSingleDataSource(dataSourceType)
        else:
            directory = self.getDataSourceDirectory(dataSourceType)
            self.data[dataSourceType] = \
                    {utils.getBaseFilename(filename): None for filename in utils.getFilenames(directory, ext="json")}

    def loadSingleDataSource(self, dataSourceType):
        '''
        Load the file containing data for this data source into a dictionary and
        place it in the top-level data variable.
        '''
        dataSourceLocation = self.locations[dataSourceType]
        directory = self.getDataSourceDirectory(dataSourceType)

        filename = utils.makeJSONFilename(directory, os.path.basename(directory))
        self.data[dataSourceType] = utils.getJSON(filename)

    def loadMulitpleDataSource(self, dataSourceType, _id=None):
        '''
        Load data from a multiple-file data source. If _id is None, then load
        the entire data source. Otherwise, only load the specified _id.
        '''
        dataSourceLocation = self.locations[dataSourceType]
        directory = self.getDataSourceDirectory(dataSourceType)

        loader = utils.getJSON if dataSourceLocation['isJson'] else utils.getText
        if _id == None:
            # Get all of the ids for this data source
            ids = self.getDataSourceIds(dataSourceType)
        else:
            # Ask for the data source ids. If they are already loaded, then
            # this will do nothing. If not, it will initialize the data source.
            self.getDataSourceIds(dataSourceType)
            # But we only need to actually load this particular instance
            ids = [_id]

        for _id in ids:
            # Check to see if the instance has already been loaded
            if self.data[dataSourceType][_id] == None:
                # If not, then load it.
                self.data[dataSourceType][_id] = loader(utils.makeJSONFilename(directory, _id))

    def loadDataSourceInstance(self, dataSourceType, _id=None):
        '''
        Load the given instance of the given data source. If the data
        source is stored a single file, then load the entire data source.
        If it's not, then only load the specified _id.
        '''
        if self.isSingle(dataSourceType):
            self.loadSingleDataSource(dataSourceType)
        else:
            self.loadMulitpleDataSource(dataSourceType, _id)

    ##############################################
    ############### INTERNAL ACCESS ##############

    def isSingle(self, dataSourceType):
        '''
        Return true if the entire datasource is stored in a single file.
        '''
        return self.locations[dataSourceType]['single']

    def getDataSourceDirectory(self, dataSourceType):
        '''
        Return a path to the directory where the data for this data source is stored.
        '''
        return os.path.join(self.top, self.dataDir, self.locations[dataSourceType]['dir'])

    def getDataSource(self, dataSourceName):
        '''
        Return the direct reference to the data source dictionary in memory.
        If the data source has not been initialized, then load the ids and try again.
        '''
        try:
            return self.data[dataSourceName]
        except KeyError:
            try:
                self.loadDataSourceIds(dataSourceName)
                return self.getDataSource(dataSourceName)
            except KeyError:
                raise KeyError("{0} is not a valid data source name.".format(dataSourceName))

    ##############################################
    ############## EXTERNAL ACCESS ###############

    def root(self):
        '''
        Return a reference to the root of the type hierarchy.
        '''
        return self._root

    def getDataSourceIds(self, dataSource):
        '''
        Get an iterable of ids for the given data source. If the data source 
        has not been initialized, then load the ids and try again.
        '''
        try:
            return self.data[dataSource].keys()
        except KeyError:
            self.loadDataSourceIds(dataSource)
            return self.getDataSourceIds(dataSource)


    def getDataSourceInstance(self, dataSourceName, _id):
        '''
        Return the direct reference to the given data source instance.
        If it has not been loaded, then load it first.
        '''
        if self.getDataSource(dataSourceName)[_id] == None:
            self.loadDataSourceInstance(dataSourceName, _id)
        return self.getDataSource(dataSourceName)[_id]
