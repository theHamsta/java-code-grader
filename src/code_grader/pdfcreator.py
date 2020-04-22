#
# Copyright © 2020 Stephan Seitz <stephan.seitz@fau.de>
#
# Distributed under terms of the GPLv3 license.
"""

"""

import argparse
import re
import subprocess
import sys
import tempfile
from glob import escape, glob
from os.path import basename, dirname, exists, join, startfile
from pprint import pprint
from shutil import copy

import jinja2
from pygments import highlight
from pygments.formatters import LatexFormatter

from code_grader.lexer import CustomJavaLexer

SCORING_REGEX = re.compile(
    r"//\s*\[(.*)\s*:\s*([0-9.]+)\s*/\s*([0-9.]+)\s*points\]")


class ScoringResult:
    def __init__(self, scored_points, total_points, file_points):
        self.scored_points = scored_points
        self.total_points = total_points
        self.file_points = file_points

    def __str__(self):
        return f"""{self.__class__,__name__}: {self.scored_points}/{self.total_points}: {self.file_points}"""


def create_grading(files):
    total_points = 0
    scored_points = 0
    file_points = {}

    for filename in files:
        with open(filename) as f:
            content = f.read()

            filename = basename(filename)
            file_points[filename] = {}
            file_points[filename]['tasks'] = []
            file_points[filename]['scored_points'] = 0
            file_points[filename]['max_points'] = 0

            for (task, points, max_points) in SCORING_REGEX.findall(content):
                points = float(points)
                max_points = float(max_points)

                print(f'{task}: {points} of {max_points}')
                file_points[filename]['tasks'].append(
                    (task, points, max_points))

                scored_points += points
                total_points += max_points

                file_points[filename]['scored_points'] += points
                file_points[filename]['max_points'] += max_points

    return ScoringResult(scored_points, total_points, file_points)


def create_tex_file(filenames, working_dir):
    all_files = glob(join(escape(working_dir), '**', '*'), recursive=True)

    relevant_files = list(filter(lambda x: basename(x) in filenames,
                                 all_files))

    if not relevant_files:
        return None
    else:
        print(f"Found files: {relevant_files}")

    scoring = create_grading(relevant_files)
    print(scoring)
    pprint(scoring.file_points)

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

\setlength{\parindent}{0cm}
\renewcommand{\familydefault}{\sfdefault}
''')
    doctext.append(formatter.get_style_defs())
    doctext.append(r"""
\begin{document}""")

    doctext.append(
        jinja2.Template(r"""

\section*{Scoring}

{% for file, scoring in file_points.items() %}
\paragraph{ {{file}}: {{scoring.scored_points}} / {{scoring.max_points}} }
\begin{itemize}
{% for task in scoring.tasks %}
    \item {{ task[0] }}: {{task[1]}} / {{task[2]}}
{% endfor %}
\end{itemize}
{% endfor %}
\paragraph{ Total: {{scored_points}} / {{total_points}} }
""").render(scoring.__dict__))

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

    if sys.platform in ('linux', 'darwin'):
        cmd = [
            "latexmk", "-silent", "-pdf", "-shell-escape", "-file-line-error",
            "-synctex=1", "-interaction=nonstopmode", tex_file
        ]
    elif sys.platform == 'win32':
        cmd = ["pdflatex","-shell-escape", "-interaction=nonstopmode", tex_file]


    print(f"Running \"{' '.join(cmd)}\" ...")
    subprocess.call(cmd, cwd=dirname(tex_file))

    pdf_file = tex_file.replace('.tex', '.pdf')
    if exists(pdf_file):
        print(f"Finished: {pdf_file}")
        if sys.platform == 'darwin':
            subprocess.call(["open", pdf_file])
        elif sys.platform == 'linux':
            subprocess.call(["xdg-open", pdf_file])
        elif sys.platform == 'win32':
            startfile(pdf_file)
        else:
            pass

        return pdf_file

    else:
        print(f"Failed to find generated PDF ({pdf_file})")


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--input_folder', default='.')
    parser.add_argument('source_files', nargs='+')
    parser.add_argument('--language', default='java')
    args = parser.parse_args()

    assert args.language == 'java', 'Only supported language at the moment'

    pdf_file = create_pdf(args.source_files, args.input_folder)
    try:
        copy(pdf_file, join(args.input_folder, 'scoring.pdf'))
    except Exception:
        pass


if __name__ == '__main__':
    main()
