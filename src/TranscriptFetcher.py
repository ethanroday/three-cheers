'''
Contains one method, fetch_transcripts(), to
retrieve raw debate transcripts from their APP urls,
then output them to the raw transcripts folder.
'''

import requests
from bs4 import BeautifulSoup

from ThesisDataAccessor import Accessor as data

def fetch_transcripts():
    '''
    Retrieve the raw debate transcripts from their APP urls,
    then output them to the raw transcripts folder.
    '''
    for debate in data.debates.debateMetadata:
        print("Fetching debate {}.".format(debate.get('id')))
        url = debate.transcriptUrl # Get the transcript's url
        req = requests.get(url) # Fetch the HTML
        soup = BeautifulSoup(req.text) # Parse it using BeautifulSoup
        transcript = soup.find("span", class_="displaytext") # Get the transcript element
        transcript_file_path = '../data/debates/rawTranscripts/{}.json'.format(debate.get('id'))
        with open(transcript_file_path, 'wb') as transcript_file:
            transcript_file.write(transcript.prettify('latin1')) # Write the transcript to a file

if __name__ == "__main__":
    fetch_transcripts()
