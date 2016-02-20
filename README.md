# lyx2web

`lyx2web` is a standalone Python script to convert a
[Lyx](https://www.lyx.org/) or a .tex document to a set of blog posts. This
little tool is suitable if you maintain notes in one Lyx document and want to
publish them as blog posts. 

* For each section (`\section` in Latex), the tool will write two files: a
  [markdown](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)
(.md) and a Latex file. The markdown file is suitable for publishing on the web
if you use a static site generator (e.g., Pelican, Jekyll). 

* The generated .tex file from each section is compilable with `pdflatex`.
The Latex preamble is copied from the input Lyx (or .tex) file.

For [Pelican](http://blog.getpelican.com/) setup that can directly support the
markdown output from this tool, see [the source cdoe of my
blog](https://github.com/wittawatj/pelican_blog) for example.

## Software dependency 

The tool is loosely tested on Ubuntu 14.04 with Python 2.7.11. 

Require

* Python 2.x. 
* `lyx` (used for converting the input Lyx file into .tex)
* `pandoc` (used for converting to markdown) 
* `iconv` (used for converting the tex source file in to UTF8 encoding)

## Usage 

    usage: lyx2web.py [-h] src dest

    Convert a .tex or .lyx file into a sequence of markdown files. Save them into
    the specified dest directory.

    positional arguments:
      src         Path to source file to be converted.
      dest        Destination directory to save exported markdown files.

    optional arguments:
      -h, --help  show this help message and exit

The repository contains `test.lyx` and `test.tex` (of identical content) for you 
to test. There are three sections in the document.

    python lyx2web.py test.lyx export 

will create a new folder `export/` that contains six files: (.tex, .md) files for 
each section.

### Post metadata

Many static site generators require each post to have metadata at the beginning 
of its markdown file. For example, in Pelican, the metadata look like 


    Title: some title here
    Date: 2014-06-29 
    Tags: probability, statistics
    Slug: prob_gaussian_ball

To specify this, first define a new command `\postmeta` in the Latex preamble with 

    \newcommand{\postmeta}[1]{}

At the beginning of each section, write 

    \postmeta{
    Title: some title here
    Date: 2014-06-29 
    Tags: probability, statistics
    Slug: prob_gaussian_ball
    }

This metadata will not show up in the compiled pdf as the command `\postmeta` is 
defined to do nothing. The only purpose is so that the tool can copy to the
beginning of the generated markdown file. The value of `Slug` will be used as
the generated file name. 

If `\postmeta{..}` is unspecified, the text specified in
`\section{...}` will be used as the slug (after normalizing and removing unsuitable
characters). Today's date will be used for the date. Tags will be set to empty.

## Limitations

This tool is written in a few hours and obviously nowhere near complete. 

Not supported (yet)

* Latex bibliography.

Supported 

* Latex's `\href` (more suitable for blog posts than Latex bibliography).
* `\footnote`.
