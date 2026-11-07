+++
title = "Sivro"
description = "A local, read-only explorer for Parquet, CSV, JSON, Excel and SQLite."
template = "project"

[extra]
id = "sivro"
+++

A desktop app for opening a data file and looking through it without changing it or writing any code. Each file opens in its own tab, where you can search, filter and sort it, then export the view you ended up with. Sivro is a pre-1.0 beta.

- Opens Parquet, Arrow IPC/Feather V2, HDF5, CSV, TSV, JSON, JSON Lines, Excel workbooks and SQLite databases
- Search, filter, sort, hide columns, profile a column or inspect a row, with exact row counts for filtered views
- Exports the current view to Parquet, Arrow, HDF5, CSV, TSV or JSON
- Never modifies source files, runs no macros or formulas, accepts no SQL and works offline
- Keeps large integers and decimals exact instead of rounding them through floating point
- Shows JSON that isn't a table as a navigable document tree
