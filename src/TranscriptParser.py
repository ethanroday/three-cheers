'''
This module contains the TranscriptParser class, a
class for parsing raw transcripts into generators of
utterance and non-utterance events.
'''

import re
from itertools import chain, filterfalse

from bs4 import BeautifulSoup, NavigableString
from nltk.tokenize import sent_tokenize, word_tokenize

import utils
from ThesisDataAccessor import Accessor as data


class TranscriptParser:
    '''
    A class for parsing raw transcripts into generators of utterance and non-utterance events.
    This class uses a debate's parsing metadata, which identifies patterns in transcript formats
    (viz. length of the transcript header, format of non-utterance events, and format of speaker
    names). Some debate-specific idiosynchracies are also hardcoded.
    '''

    ###############################################################
    # These class constants are used in mapping event regex matches
    # to actual non-utterance events. See documentation throughout.

    eventTypes = {
        "applause": "applause",
        "applaud": "applause",
        "laugh": "laughter",
        "chuckle": "laughter",
        "cross talk": "crosstalk",
        "crosstalk": "crosstalk",
        "cheer": "cheering",
        "boo": "booing",
        "jeer": "booing",
        "buzz": "timer",
        "timer": "timer",
        "bell": "timer",
        "spangled": "national anthem",
        "anthem": "national anthem",
        "video": "video clip",
        "clip": "video clip",
        "unk": "unknown"
    }

    excludeExact = [
        "sic",
        "ph",
        "sp"
    ]

    excludeContains = [
        "thousand",
        "illion",
        "0"
    ]

    keepInTranscriptContains = [
        "unidentified",
        "unintelligible",
        "inau"
    ]

    keepInTranscriptExact = [
        "k",
        "j"
    ]

    # End of class constants
    ###############################################################

    @staticmethod
    def separateSingleStrings(soup):
        '''
        This method is necessary because 76561 and 76562 don't have separate tags for speakers.
        It iterates over all of the p tags and inserts a b tag for each speaker.
        '''
        for p in soup.find_all(lambda tag: tag.name == 'p' and tag.string):
            if re.match("[^a-z:]+:", p.string):
                i = p.string.find(": ")
                speaker = soup.new_tag('b')
                speaker.string = p.string[:i + 1].strip()
                p.string = p.string[i + 2:].strip()
                p.string.insert_before(speaker)
            else:
                p.string = p.string.strip()

    # See applySpecialFixes() for documentation
    specialFixes = {
        '90513':
            (lambda soup: \
                soup.find(lambda tag: \
                    tag.name == 'b' and tag.find('b') is not None \
                ).find('b').unwrap()
            ),
        '76561': separateSingleStrings.__func__,
        '76562': separateSingleStrings.__func__,
        '111178':
            (lambda soup: \
                (lambda tag: tag.replace_with(''.join([tag, '[']))) \
                (soup.find(string=re.compile(r']This is')).parent.contents[2])
            ),
        '110758':
            (lambda soup: \
                soup.find(string=re.compile(r'Governor -- \[')).find_next_sibling('b').unwrap()
            ),
        '74349':
            (lambda soup: \
               [tag.extract() for tag in soup.find_all('b') if \
                tag.string != None and tag.string.strip() == ':']
            )
    }

    # This event regex detects strings that look like
    # non-utterance events within a span of text.
    eventRegex = r"\[\s*?(.+?)\s*?\]|\(\s*?(.+?)\.?\s*?\)"

    # This regex splits an event string into potentially
    # multiple different events, as some events are
    # often transcribed together.
    eventSplitter = r"(?:, ?)|(?: a[nm]d )|(?:/)"

    @classmethod
    def eventGetter(cls, eventMatch):
        '''
        Retrieve the non-utterance event string from a given full event match object.
        '''
        return next(item for item in eventMatch.groups() if item is not None).lower()

    speakerDetectors = [
        (lambda tag: tag.name == 'b' and tag.string)
    ]

    speakerIdentifiers = [
        # By default, the speaker is identified by last name; if
        # unidentifiable, return None
        (lambda parserObject, speakerString: \
            parserObject.lastNames.get( \
                speakerString.strip(":").split()[-1].lower(), \
                None)
        ),

        # Some transcripts identify the moderator with 'MODERATOR' rather than by name.
        # The best we can do here is just choose the first moderator from the list
        # of known moderators.
        (lambda parserObject, speakerString: \
            parserObject.lastNames.get(speakerString.strip(":").split()[-1].lower(), None) \
            if speakerString.strip() != "MODERATOR:" else \
            list(iter(parserObject.debate.debateMetadata.moderators))[0]
        ),

        # When speakers are identified by first utterance, the last name is right
        # before the comma (after excluding anything in parentheses)
        # Ex: 'GOV. GEORGE W. BUSH (R-TX), PRESIDENTIAL CANDIDATE:'
        (lambda parserObject, speakerString: \
            parserObject.lastNames.get( \
                re.sub(r"\(.+?\)", "", speakerString) \
                .split(',')[0].split()[-1].strip(':').lower(), \
            None)
        )
    ]

    @classmethod
    def makeUtterances(cls, speaker, text):
        '''
        Given a speaker and the text of an utterance, split the utterance
        into sentences (it may be multiple sentences) and yield an utterance
        event, including a list of tokens.
        '''
        for sentence in sent_tokenize(text.strip()):
            yield {
                'eventType': 'utterance',
                'speaker': speaker,
                'text': sentence,
                'tokens': word_tokenize(sentence)
            }

    @classmethod
    def makeNonUtterances(cls, match):
        '''
        Given a string representing a non-utterance event, split
        the string into potentially multiple event string, then yield
        an event for each one.
        '''

        # Sometimes, a string that looks like a non-utterance event should
        # actually be dropped entirely. See method documentation for more.
        if not cls.dropMatch(match):

            matchString = match.group()
            eventString = cls.eventGetter(match)

            # Sometimes, multiple non-utterance events come in the same string.
            # This method will, for example, split '[ applause and laughter ]'
            # into two separate applause and laughter events.
            eventStringLower = eventString.lower()
            eventStrings = [s.strip() for s in \
                re.split(TranscriptParser.eventSplitter, eventStringLower)]

            for e in eventStrings:
                yield {
                    'eventType': next((cls.eventTypes[t] for t in \
                        cls.eventTypes if t in e), 'other'),
                    'text': matchString
                }

    @classmethod
    def keepInTranscript(cls, eventMatch):
        '''
        Given a span of text that matches the event regex, see if we actually
        want to keep it in the transcript. This is sometimes the case for
        things like '(inaudible)'.
        '''
        eventString = cls.eventGetter(eventMatch)
        return any(ex in eventString for ex in TranscriptParser.keepInTranscriptContains) or \
            any(ex == eventString.strip() for ex in TranscriptParser.keepInTranscriptExact)

    @classmethod
    def filteredEventMatches(cls, extentString):
        '''
        Return a list of regex match objects for all of the non-utterance
        events in the extent (i.e. excluding strings that look like non-utterance
        events but which should actually remain in the transcript).
        '''
        return (match for match in re.finditer(cls.eventRegex, extentString) if \
            not cls.keepInTranscript(match))

    @classmethod
    def dropMatch(cls, eventMatch):
        '''
        Some transcript annotations that look like non-utterance events should
        simply be dropped entirely from the parsed transcript. These include
        '(sp)', '(ph)', etc.
        '''
        eventString = cls.eventGetter(eventMatch)
        return any(ex in eventString for ex in cls.excludeContains) or \
            any(ex == eventString.strip() for ex in cls.excludeExact) or \
            re.search(r"\?\s*[\)\]]", eventMatch.group())

    def __init__(self, debateToParse):
        self.debate = debateToParse
        self.soup = BeautifulSoup(
            re.sub(r"\s+", " ", debateToParse.transcriptsRaw), "html.parser"
        )
        self.lastNames = {data.people.peopleMetadata[_id].lastName.lower(): _id for _id in chain(
            debateToParse.debateMetadata.participants, debateToParse.debateMetadata.moderators)}
        self.isSpeakerTag = TranscriptParser.speakerDetectors[
            debateToParse.parsingMetadata.speakerDetector]
        self.speakerIdentifier = TranscriptParser.speakerIdentifiers[
            debateToParse.parsingMetadata.speakerIdentifier]

    def applySpecialFixes(self):
        '''
        If this raw transcript has any special fixes defined, apply them.
        '''
        if self.debate.get('id') in TranscriptParser.specialFixes:
            TranscriptParser.specialFixes[self.debate.get('id')](self.soup)

    def skipHeader(self, descendants):
        '''
        Skip the raw transcript header by iterating past the appropriate
        numer of outer <p> tags.
        '''
        pCount = 0

        skip = self.debate.parsingMetadata.utteranceIterator

        # Skip the header that most debates have.
        while True:
            e = next(descendants)
            if e.name == 'p' and e.parent.name == 'span':
                if pCount == skip:
                    break
                pCount += 1

    def eventsFromExtent(self, speakerString, extentString):
        '''
        Given a speaker string and an extent string, attempt to identify the speaker
        and parse the extent into utterance and non-utterance events.
        '''

        # Identify the speaker
        speaker = self.speakerIdentifier(self, speakerString.strip())

        # Find all of the matches for potential non-utterance events.
        # Iterate through the matches, yielding utterances in the space between
        # each match and non-utterances within each match.
        lastEnd = 0
        for match in TranscriptParser.filteredEventMatches(extentString):
            yield from TranscriptParser.makeUtterances(speaker, extentString[lastEnd:match.start()])
            yield from TranscriptParser.makeNonUtterances(match)
            lastEnd = match.end()
        rest = extentString[lastEnd:]
        if rest:
            yield from TranscriptParser.makeUtterances(speaker, rest)

    def parse(self):
        '''
        Parse the given raw transcript into a list of utterance and non-utterance events.
        '''

        # The parser keeps track of speaker strings and extents.
        # The current extent is just a string containing all of the text since
        # the last speaker tag.
        curSpeaker = ""
        curExtent = ""

        # Some raw transcripts have odd issues. They get their own special fixes.
        self.applySpecialFixes()

        descendants = self.soup.descendants

        # Most transcripts have a header which is one, two, or three <p> tags.
        # Skip the header.
        self.skipHeader(descendants)

        # Get to the first utterance and identify the speaker.
        while True:
            e = next(descendants)
            if self.isSpeakerTag(e):
                curSpeaker = e.string
                next(descendants)
                break

        # Continue through the rest of the debate.
        for e in descendants:
            if self.isSpeakerTag(e):
                # If we encounter a speaker tag, then 'finish' the current
                # extent. This involves identifying the speaker, parsing
                # the entire extent into utterances and other events, and
                # yielding all of those events.
                yield from self.eventsFromExtent(curSpeaker, curExtent)

                # Sometimes the speaker tag is empty. If it is, assume the
                # previously identified speaker is still talking
                # Otherwise, set the new speaker string.
                if e.string.strip():
                    curSpeaker = e.string

                # Reset the current extent
                curExtent = ""
                # Skip the NavigableString that is a child of this tag (and
                # the next element in the descendants iterator
                next(descendants)

            elif isinstance(e, NavigableString):
                # It it's not a speaker tag, just add to the current extent
                curExtent += e
            
        if curExtent:
            yield from self.eventsFromExtent(curSpeaker, curExtent)

if __name__ == '__main__':

    def eventToStr(event):
        '''
        A utility function for printing individual events when debugging parsing code.
        '''
        if event['eventType'] == 'utterance':
            if event['speaker'] is not None:
                speaker = data.people.peopleMetadata[event['speaker']]
                speakerString = ' '.join([speaker.firstName, speaker.lastName])
            else:
                speakerString = "Unknown"
            return ''.join([speakerString, ': ', '\'', event['text'], '\''])
        else:
            return ''.join([event['eventType'], ': ', '\'', event['text'], '\''])

    for debate in data.debates:
        if debate.get('id') != '96660':
            print("Parsing debate with id {0}...".format(debate.get('id')), end="")
            try:
                filename = "../data/debates/parsedTranscripts/{0}.json".format(debate.get('id'))
                utils.writeJSON({
                    'id': debate.get('id'),
                    'events':list(TranscriptParser(debate).parse())
                }, filename)
                print("Done!")
            except Exception as err:
                print("Error while parsing debate with id {0}".format(debate.get('id')))
                raise err
