from ThesisDataAccessor import Accessor as data
import re
import binascii
import utils
from datetime import datetime

def makeId(name):
    '''
    Generates a deterministic hexadecimal representation from the given name by getting the
    hex representation of the string's byte array and returning the corresponding decoded string
    '''
    return binascii.hexlify(bytes(name, encoding='ascii')).decode()

def strNameDict(d):
    return "{0} {1}{2}: {3}".format(d['first'], d['middle']+" " if 'middle' in d else "", d['last'], getDescriptor(d))

def getDescriptor(d):
    if 'descriptor' in d:
        if type(d['descriptor']) == dict:
            s = d['descriptor']['office']
            if d['descriptor']['state'] is not None:
                s += " " + d['descriptor']['state']
            return s
        else:
            return d['descriptor']
    else:
        return "EMPTY"

def parseName(nameStr):
    nameRegex = "((.*?) )?([A-Z]\w+) (([A-Z])\. )?([A-Z][\w']+)(,? Jr\.)?(,? (\((.+)\)|([DR]- ?[A-z\.]+)))?$"
    match = re.match(nameRegex, nameStr)
    if not match:
        print("Name did not match: {0}".format(nameStr))
        raise TypeError
    groups = match.groups()
    d = {'first': groups[2], 'last': groups[5]}
    if groups[4] is not None:
        d['middle'] = groups[4]
    if groups[1] is not None:
        d['descriptor'] = {
            'office': groups[1],
            'state': groups[8]
        }
    elif groups[8] is not None:
        d['descriptor'] = groups[8]
    return d

# The ones in here already were manually extracted because the format was so bizzare
participantsDict = {
    '75090': ["Gary Bauer", "Orrin Hatch", "Steve Forbes", "John McCain", "Alan Keyes"],
    '75118': ["Wesley Clark", "Joe Lieberman", "Dennis Kucinich", "Howard Dean", "John Kerry", "Al Sharpton", "John Edwards"],
    '74348': ["Sam Brownback", "Jim Gilmore", "Rudy Giuliani", "Duncan Hunter", "Mike Huckabee", "John McCain", "Ron Paul", "Mitt Romney", "Tom Tancredo", "Tommy Thompson"],
    '75140': ["Mike Gravel", "Christopher Dodd", "John Edwards", "Hillary Clinton", "Barack Obama", "Bill Richardson", "Joe Biden", "Dennis Kucinich"],
    '74351': ["John Kerry", "Howard Dean", "Joe Lieberman", "Wesley Clark", "Dennis Kucinich", "John Edwards", "Al Sharpton"],
    '75089': ["Gary Bauer", "George Bush", "Orrin Hatch", "John McCain", "Alan Keyes", "Steve Forbes"]
}

# These map some common name variations/misspellings (and one little bug) to standard forms
mappings = {
    'Christoper Dodd': 'Christopher Dodd',
    'Joseph Biden': 'Joe Biden',
    'Rudolph Giuliani': 'Rudy Giuliani',
    'James Gilmore': 'Jim Gilmore',
    'Rodham Clinton': 'Hillary Clinton' # This is the bug
}

participantsSection = "<(b|i)> (PARTICIPANTS|Participants|Candidates): (<br/> )?</(b|i)> (<br/> )?(.*?) </?p>"
suffix = "[;,\.]?( and;?)?\s*$"

for debate in data.debates:
    transcript = re.sub("\s+"," ", debate.transcriptsRaw)
    
    participants = re.search(participantsSection, transcript)

    if participants and participants.group(6) is not None and "<br/>" in participants.group(6):
        nameStrings = [re.sub(suffix, "", line).strip() for line in participants.group(6).split("<br/>") if not re.match("^\s*$", line)]
        names = [parseName(name) for name in nameStrings if "Moderator" not in name]
        participantsDict[debate.get('id')] = [(lambda full: mappings.get(full, full))("{0} {1}".format(d['first'], d['last'])) for d in names]

people = {}
for debateId in participantsDict:
    #print(debateId, participantsDict[debateId])
    for person in participantsDict[debateId]:
        if person not in people:
            people[person] = debateId

def makePersonMetadata(_id, firstname, lastname, personType, party):
    return {
        'id': _id,
        'firstName': firstname,
        'lastName': lastname,
        'personType': personType,
        'party': party
    }

peopleMetadata = {}
for person in people:
    _id = makeId(person)
    peopleMetadata[_id] = makePersonMetadata(_id, person.split()[0], person.split()[1], 'candidate', data.debates[people[person]].debateMetadata.party)


utils.writeJSON(peopleMetadata, "../data/people/metadata/metadata.json")

## UNSAFE!!! ##
debateMetadata = utils.getJSON("../data/debates/metadata/metadata.json")
utils.writeJSON(debateMetadata, "../data/debates/metadata/metadata_backup.json")
for debateId in debateMetadata:
    debateMetadata[debateId]['participants'] = [makeId(participant) for participant in participantsDict[debateId]]
utils.writeJSON(debateMetadata, "../data/debates/metadata/metadata.json")


# ------------------------------------- VALIDATE ------------------------------------- #

data.reset() # Reset the PDA, which resets the data manager, so the data sources that have changed get reloaded

for year in [2000, 2004, 2008, 2012, 2016]:
    metadatas = sorted([md for md in data.debates.debateMetadata if md.electionYear == year], key=lambda md: datetime.strptime(md.date, "%Y/%m/%d"))
    for md in metadatas:
        print("Participants in {0} on {1}:".format(md.friendlyName, md.date))
        for participantId in md.participants:
            person = data.people.peopleMetadata[participantId]
            print("{0} {1}".format(person.firstName, person.lastName))
        input()
        print()
