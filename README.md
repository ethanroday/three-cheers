## three-cheers
This repository contains the parsing code described in Section 3.1 of _Three Cheers For Partisanship_ [1]. It is used to parse the raw transcripts of presidential primary debates [available from the American Presidency Project](http://www.presidency.ucsb.edu/debates.php) [2].

To fetch and parse the debates, run the following *from the `src/` directory*:

    python TranscriptFetcher.py
    python TranscriptParser.py
    
The parsed transcripts will be output `data/debates/parsedTranscripts`).

## References
[1] Roday, Ethan. _Three Cheers For Partisanship: Lexical Framing and Applause in U.S. Presidential Primary Debates_. Master's thesis, University of Washington, 2017.

[2] Peters, Gerhard and Woolley John T. _The American Presidency Project_, 1999-2017. http://www.presidency.ucsb.edu/debates.php.
