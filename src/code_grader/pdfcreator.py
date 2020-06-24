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
from os.path import basename, dirname, exists, join
import os
import shutil

try:
    from rich import print
except Exception:
    pass

from pprint import pprint
from shutil import copy

import jinja2
from pygments import highlight
from pygments.formatters import LatexFormatter

from code_grader.lexer import CustomJavaLexer

SCORING_REGEX = re.compile(
    r"//\s*\[(.*)\s*:\s*([0-9.,]+)\s*/\s*([0-9.,]+)\s*(point|Point|Punkten|Punkte|p.|P.)?s?\]")


class ScoringResult:
    def __init__(self, scored_points, total_points, file_points):
        self.scored_points = scored_points
        self.total_points = total_points
        self.file_points = file_points

    def __str__(self):
        return f"""{self.__class__,__name__}: {self.scored_points}/{self.total_points}: {self.file_points}"""


def open_pdf(path):
    if sys.platform == 'darwin':
        subprocess.call(["open", path])
    elif sys.platform == 'linux':
        subprocess.call(["xdg-open", path])
    elif sys.platform == 'win32':
        os.startfile(path)
    else:
        pass


def create_grading(files):
    total_points = 0
    scored_points = 0
    file_points = {}

    for filename in files:
        with open(filename, 'r', encoding='ascii', errors='ignore') as f:
            content = f.read()

            filename = basename(filename)
            file_points[filename] = {}
            file_points[filename]['tasks'] = []
            file_points[filename]['scored_points'] = 0
            file_points[filename]['max_points'] = 0

            for (task, points, max_points, _) in SCORING_REGEX.findall(content):
                points = float(points.replace(',', '.'))
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
        return None, None
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
        with open(filename, 'r', encoding="utf-8", errors="ignore") as f:
            code = f.read()
            doctext.append(f"\\section*{{{basename(filename)}}}")
            doctext.append(highlight(code, CustomJavaLexer(), formatter))

    doctext.append(r"\end{document}")

    return '\n'.join(doctext), scoring


def create_pdf(filenames, working_dir, silent=False):

    print("Creating LaTeX code...")
    tex_code, scoring = create_tex_file(filenames, working_dir)

    if not tex_code:
        print("No tex code generated")
        return None, None

    with tempfile.NamedTemporaryFile('w', suffix='.tex', delete=False) as f:
        f.write(tex_code)
        tex_file = f.name

    if shutil.which('latexmk'):
        cmd = [
            "latexmk", "-silent", "-pdf", "-shell-escape", "-file-line-error",
            "-synctex=1", "-f", "-interaction=nonstopmode", tex_file
        ]
    elif shutil.which('pdflatex'):
        cmd = ["pdflatex", "-shell-escape", "-interaction=nonstopmode", tex_file]
    else:
        print('"pdflatex" or "latexmk" need to be in $PATH!!!')
        exit(-1)

    print(f"Running \"{' '.join(cmd)}\" ...")
    subprocess.call(cmd, cwd=dirname(tex_file))

    pdf_file = tex_file.replace('.tex', '.pdf')
    if exists(pdf_file):
        print(f"Finished: {pdf_file}")
        return pdf_file, scoring

    else:
        print(f"Failed to find generated PDF ({pdf_file})")
        return None, None


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--input-folder', default='.')
    parser.add_argument('source_files', nargs='+')
    parser.add_argument('--language', default='java')
    parser.add_argument('--silent', action='store_true')
    parser.add_argument('--batch-grade', action='store_true')
    parser.add_argument('--total-points', type=float, default=10)
    args = parser.parse_args()

    assert args.language == 'java', 'Only supported language at the moment'

    if args.batch_grade:
        for subdir in os.listdir(args.input_folder):
            subdir = os.path.join(args.input_folder, subdir)
            if os.path.isdir(subdir):
                print(f'Analyzing folder "{subdir}"')
                pdf_file, scoring = create_pdf(args.source_files, subdir, args.silent)
                if scoring and scoring.total_points != args.total_points:
                    print(f'[red]Score is {scoring.total_points} but should be {args.total_points}![/red]')
                try:
                    target_file = join(args.input_folder, basename(subdir) + '_scoring.pdf')
                    copy(pdf_file, target_file)
                    if not args.silent:
                        open_pdf(target_file)
                except Exception:
                    pass
    else:
        pdf_file, scoring = create_pdf(args.source_files, args.input_folder, args.silent)
        if scoring and scoring.total_points != args.total_points:
            print(f'[red]Score is {scoring.total_points} but should be {args.total_points}![/red]')
        try:
            target_file = join(args.input_folder, 'scoring.pdf')
            copy(pdf_file, target_file)
            if not args.silent:
                open_pdf(target_file)
        except Exception:
            pass


if __name__ == '__main__':
    main()
