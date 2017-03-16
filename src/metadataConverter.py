import argparse
import sys
import json
import csv
from datetime import datetime
from dateutil.parser import parse
import os

def getArgs():
    parser = argparse.ArgumentParser(description='''Given an input TSV with date, name, and url information on each row, creates a new JSON data file for each debate.
                                                  Uses the UCSB page ID as the debate id.''')
    parser.add_argument('inputFile', help="The input TSV.")
    parser.add_argument('outputDir', help="The location in which to create the output JSON files, one for each debate.")
    return parser.parse_args()

def encoderExtension(field):
    if type(field) == datetime:
        return datetime.strftime(field, "%Y/%m/%d")
    else: raise TypeError()

def main():
    args = getArgs()
    with open(args.inputFile, 'r') as inputTSV:
        reader = csv.DictReader(inputTSV, delimiter='\t')
        for row in reader:
            debateId = int(row['URL'].split('=')[1])
            debateFile = str(debateId)+".json"
            debate = {'id': debateId, 'date': parse(row['Date'].strip("\"")), 'url': row['URL']}
            with open(os.path.join(args.outputDir, debateFile), 'w') as outputFile:
                json.dump(debate, outputFile, sort_keys=True, indent=4, default=encoderExtension)

main()