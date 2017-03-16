'''
Iterate through transcript parses and identify the first utterance that is not part
of the introductions and the last utterance that is part of the debate.
Write to a csv with the following schema:
debateid,firstrealindex,lastrealindex
'''
import sys
from ThesisDataAccessor import Accessor as data

def printEvent(event):
    if event.eventType == 'utterance':
        try:
            print(event.text)
        except:
            print(event.text.encode('latin1'))
    else:
        print("[{}]".format(event.eventType))

def main():
    out = open(sys.argv[1], 'a')
    try:
        for debate in data.debates.transcripts:
            if debate.get('id') == '96660':
                continue

            print("------------------")
            print("Processing debate {}".format(debate.get('id')))
            out.write('{},'.format(debate.get('id'))) # Write the debate id

            events = list(debate.events) # Get a list of events

            print("------------------")
            # Go from the top to identify the first non-intro utterance
            i = 0
            while i < len(events):
                printEvent(events[i])
                sentinel = input(
                    "First non-intro utterance? "
                )
                if len(sentinel) != 0:
                    print("Writing index of first non-intro event.")
                    out.write('{},'.format(i))
                    break
                i += 1

            '''
            print("------------------")
            # Go from the bottom to identify the last non-outro utterance
            i = len(events)-1
            while i >= 0:
                printEvent(events[i])
                sentinel = input(
                    "Last non-outro utterance? "
                )
                if len(sentinel) != 0:
                    print("Writing index of last non-outro event.")
                    out.write('{}'.format(i))
                    break
                i -= 1
            '''

            out.write('\n')
        out.close()
    except:
        out.close()
        print("Crashed but closed. See output file for where to continue.")

if __name__ == "__main__":
    main()