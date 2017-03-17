## three-cheers
This repository contains the parsing code described in Section 3.1 of _Three Cheers For Partisanship_ [1]. It is used to parse the raw transcripts of presidential primary debates [available from the American Presidency Project](http://www.presidency.ucsb.edu/debates.php) [2]. After crawling the raw transcripts from their respective URLs, place them in `data/debates/rawTranscripts/<id>.json`, where `<id>` is the value of the `pid` in the debate's URL query string. Then, run `TranscriptParser.py` to parse the transcripts (they will be output `data/debates/parsedTranscripts`).

## References
[1] Roday, Ethan. _Three Cheers For Partisanship: Lexical Framing and Applause in U.S. Presidential Primary Debates_. Master's thesis, University of Washington, 2017.

[2] Peters, Gerhard and Woolley John T. _The American Presidency Project_, 1999-2017. http://www.presidency.ucsb.edu/debates.php.
