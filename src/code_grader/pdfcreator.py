#
# Copyright © 2020 Stephan Seitz <stephan.seitz@fau.de>
#
# Distributed under terms of the GPLv3 license.
"""

"""

import argparse
import subprocess
import sys
import tempfile
from glob import escape, glob
from os.path import basename, dirname, exists, join

from pygments import highlight
from pygments.formatters import LatexFormatter

from code_grader.lexer import CustomJavaLexer


def create_tex_file(filenames, working_dir):
    all_files = glob(join(escape(working_dir), '**', '*'), recursive=True)

    relevant_files = list(filter(lambda x: basename(x) in filenames,
                                 all_files))
    if not relevant_files:
        return None
    else:
        print(f"Found files: {relevant_files}")

    formatter = LatexFormatter(style='friendly',
                               title="This is a title",
                               linenos=True,
                               escapeinside="xx",
                               titel="This is a title",
                               verboptions="fontsize=\\scriptsize")

    doctext = []
    doctext.append(r'''\documentclass[10pt]{article}

\usepackage{geometry}
\geometry{
   a4paper,
   right=10mm,
   bottom=15mm,
   left=10mm,
   top=10mm,
  }
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{minted} 
''')
    doctext.append(formatter.get_style_defs())
    doctext.append(r"""
\begin{document}""")

    for filename in relevant_files:
        with open(filename) as f:
            code = f.read()
            doctext.append(f"\\section*{{{basename(filename)}}}")
            doctext.append(highlight(code, CustomJavaLexer(), formatter))

    doctext.append(r"\end{document}")

    return '\n'.join(doctext)


def create_pdf(filenames, working_dir):

    print(f"Creating LaTeX code...")
    tex_code = create_tex_file(filenames, working_dir)

    if not tex_code:
        print("No tex code generated")

    with tempfile.NamedTemporaryFile('w', suffix='.tex', delete=False) as f:
        f.write(tex_code)
        tex_file = f.name

    cmd = [
        "latexmk", "-pdf", "-shell-escape", "-verbose", "-file-line-error",
        "-synctex=1", "-interaction=nonstopmode", tex_file
    ]
    print(f"Running \"{' '.join(cmd)}\" ...")
    subprocess.call(cmd, cwd=dirname(tex_file))

    pdf_file = tex_file.replace('.tex', '.pdf')
    if exists(pdf_file):
        print(f"Finished: {pdf_file}")
        if sys.platform == 'darwin':
            subprocess.call(["open", pdf_file])
        elif sys.platform == 'linux':
            subprocess.call(["xdg-open", pdf_file])
        else:
            pass

    else:
        print(f"Failed to find generated PDF ({pdf_file})")


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--input_folder', default='.')
    parser.add_argument('source_files', nargs='+')
    parser.add_argument('--language', default='java')
    args = parser.parse_args()

    assert args.language == 'java', 'Only supported language at the moment'

    create_pdf(args.source_files, args.input_folder)


if __name__ == '__main__':
    main()
