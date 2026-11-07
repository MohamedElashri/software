+++
title = "agrep"
description = "Arabic-aware grep."
template = "project"

[extra]
id = "agrep"
+++

A command-line search tool for Arabic-script text. It matches a query across spelling variants, diacritics, letter forms, consonant skeletons and transliteration, then prints the line as originally written, with the byte offsets of each match.

- Ignores diacritics and folds alef forms and ta-marbuta, so `مدرسه` finds `مَدْرَسَة`
- Strict, loose and consonant-skeleton (rasm) profiles to control what counts as a match
- Fuzzy matching for typos and OCR errors, and regular expressions over normalized text
- Latin-keyboard queries through Buckwalter transliteration, and Persian, Urdu and Kurdish spelling rules
- Reads CP1256, ISO-8859-6 and UTF-16 files, and writes JSON Lines with exact byte spans
- Familiar grep options such as `-r`, `-n` and `--include`, with grep exit codes
