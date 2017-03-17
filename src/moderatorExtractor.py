from ThesisDataAccessor import Accessor as data
import re
import binascii
import utils
from datetime import datetime
import unicodedata

def makeId(name):
    '''
    Generates a deterministic hexadecimal representation from the given name by getting the
    hex representation of the string's byte array and returning the corresponding decoded string
    '''
    return binascii.hexlify(bytes(name, encoding='ascii')).decode()

def parseName(nameStr):
    # Decompose and remove accents/diacritics
    nameStr = ''.join([c for c in unicodedata.normalize('NFD', nameStr) if not unicodedata.combining(c)])

    nameRegex = "([A-Z]\w+) (([A-Z]\w+) )?([A-Z][\w'\-]+)(,? Jr\.)?(, (.+)|:? \((.+)\))?$"
    match = re.match(nameRegex, nameStr, flags=re.UNICODE)
    if not match:
        print("Name did not match: '{0}'".format(nameStr))
        raise TypeError
    groups = match.groups()
    org = groups[6] if groups[6] else groups[7]
    return {'first': groups[0], 'last': groups[3], 'org': "EMPTY" if not org else org }
    

# The ones in here already were manually extracted because the format was so bizzare
debatesDict = {
    '76562': ['Jorge Ramos'],
    '75089': ['Judy Woodruff', 'Candy Crowley', 'John King'],
    '75171': ['Wolf Blitzer'],
    '74348': ['Brit Hume', 'Chris Wallace', 'Wendell Goler'],
    '75140': ['Wolf Blitzer', 'Tom Fahey', 'Scott Spradling'],
    '75664': ['George Stephanopoulos'],
    '96660': ['Jim DeMint', 'Steve King', 'Robert George'],
    '75118': ['Tom Brokaw'],
    '75090': ['Cokie Roberts'],
    '74351': ['Brit Hume', 'Peter Jennings', 'Tom Griffith', 'John Distaso']
}

moderatorsDict = {}

# These map some common name variations/misspellings (and one little bug) to standard forms
mappings = {
    'Charles Gibson': 'Charlie Gibson',
    'Brett Baier': 'Bret Baier'
}

moderatorsSection = "<(b|i)> (HOSTS?|Hosts?|MODERATORS?|Moderators?): (<br/> )?</(b|i)> (<br/> )?(.*?) </?p>"
suffix = "[;,\.]?( (and|with);?)?\s*$"
n = 0
uncovered = []
for debate in data.debates:
    #print(debate.get("id"))
    transcript = re.sub("\s+"," ", debate.transcriptsRaw)
    
    moderators = re.search(moderatorsSection, transcript)

    #if debate.get('id') == '29427':
    #    print(transcript[:1000])
    #    print(moderators.groups())
    #    input()

    if moderators and moderators.group(6) is not None:
        n += 1
        nameStrings = [re.sub(suffix, "", line).strip() for line in moderators.group(6).split("<br/>") if not re.match("^\s*$", line)]
        names = [parseName(name) for name in nameStrings if "PANELIST" not in name]
        debatesDict[debate.get('id')] = [(lambda full: mappings.get(full, full))("{0} {1}".format(d['first'], d['last'])) for d in names]
        for d in names:
            full = "{0} {1}".format(d['first'], d['last'])
            if full in moderatorsDict:
                moderatorsDict[full].append(d)
            else:
                moderatorsDict[full] = [d]
    elif debate.get('id') not in debatesDict:
        print("Uncovered: {0} ({1})".format(debate.get('id'), debate.debateMetadata.date))
print()

people = {}
for debateId in debatesDict:
    #print(debateId, participantsDict[debateId])
    for person in debatesDict[debateId]:
        if person not in people:
            people[person] = [debateId]
        else:
            people[person].append(debateId)

for person in sorted(people.keys()):
    print("{0}: {1}".format(person, people[person]))


def makePersonMetadata(_id, firstname, lastname, personType):
    return {
        'id': _id,
        'firstName': firstname,
        'lastName': lastname,
        'personType': personType
    }

peopleMetadata = {}
for person in people:
    _id = makeId(person)
    peopleMetadata[_id] = makePersonMetadata(_id, person.split()[0], person.split()[1], 'moderator')

current = utils.getJSON("../data/people/metadata/metadata.json")
utils.writeJSON(current, "../data/people/metadata/metadata_backup.json")

alone = set([_id for _id in current if current[_id]['personType'] == 'moderator']) - set(peopleMetadata.keys())
print(alone)

print(len(peopleMetadata))
print(len(current))
current.update(peopleMetadata)
print("-------")
print(len(current))
utils.writeJSON(current, "../data/people/metadata/metadata.json")

## UNSAFE!!! ##
debateMetadata = utils.getJSON("../data/debates/metadata/metadata.json")
utils.writeJSON(debateMetadata, "../data/debates/metadata/metadata_backup.json")
for debateId in debateMetadata:
    debateMetadata[debateId]['moderators'] = [makeId(moderator) for moderator in debatesDict[debateId]]
utils.writeJSON(debateMetadata, "../data/debates/metadata/metadata.json")


# ------------------------------------- VALIDATE ------------------------------------- #

data.reset() # Reset the PDA, which resets the data manager, so the data sources that have changed get reloaded

for year in [2000, 2004, 2008, 2012, 2016]:
    metadatas = sorted([md for md in data.debates.debateMetadata if md.electionYear == year], key=lambda md: datetime.strptime(md.date, "%Y/%m/%d"))
    for md in metadatas:
        print("Moderators for {0} on {1}:".format(md.friendlyName, md.date))
        for moderatorId in md.moderators:
            person = data.people.peopleMetadata[moderatorId]
            print("{0} {1}".format(person.firstName, person.lastName))
        input()
        print()