# BeNeither
Code for [BeNeither](https://twitter.com/beneither)

## What
The basic idea is to search twitter for tweets that look like "i'm not a X i'm a Y".
The strings are parsed with Spacy and then we do some fuzzy voodoo to find the things
the tweet's author claims to (not) be. That gets dumped into the template string and
sent out through the tubes.

## Prereqs
This uses [spacy](https://spacy.io), so make sure you run
`python -m spacy.en.download --force` before you try anything. See
[the docs](https://spacy.io/#install) for more information.

## Run
Use [twurl](https://github.com/twitter/twurl) or whatever to get your creds.
Save them to a JSON file, and then run `./beneither.py /path/to/your/creds.json`.

## Copyright
Copyright © 2016 Sam Raker (sam dot raker at gmail dot com)
This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. See the COPYING file for more details.
