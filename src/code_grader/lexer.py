#
# Copyright © 2020 Stephan Seitz <stephan.seitz@fau.de>
#
# Distributed under terms of the GPLv3 license.
"""
Custom Java Lexer to highlight magic comments
"""

from pygments.lexer import bygroups, this, using
from pygments.lexers.jvm import JavaLexer
from pygments.token import (Comment, Generic, Keyword, Name, Number, Operator,
                            Punctuation, String, Text)


class CustomJavaLexer(JavaLexer):
    """
    Custom Java Lexer to highlight magic comments
    """
    name = 'CustomJavaLexer'

    tokens = {
        'root': [
            (r'[^\S\n]+', Text),
            # Our magic comments
            (r'///[\s]*.*?\n', Generic.Error),
            (r'//[\s]*?\[.*?:.*?(points|Points)?\]', Generic.Error),
            # Copied from JavaLexer
            (r'//.*?\n', Comment.Single),
            (r'/\*.*?\*/', Comment.Multiline),
            # keywords: go before method names to avoid lexing "throw new XYZ"
            # as a method signature
            (r'(assert|break|case|catch|continue|default|do|else|finally|for|'
             r'if|goto|instanceof|new|return|switch|this|throw|try|while)\b',
             Keyword),
            # method names
            (
                r'((?:(?:[^\W\d]|\$)[\w.\[\]$<>]*\s+)+?)'  # return arguments
                r'((?:[^\W\d]|\$)[\w$]*)'  # method name
                r'(\s*)(\()',  # signature start
                bygroups(using(this), Name.Function, Text, Punctuation)),
            (r'@[^\W\d][\w.]*', Name.Decorator),
            (r'(abstract|const|enum|extends|final|implements|native|private|'
             r'protected|public|static|strictfp|super|synchronized|throws|'
             r'transient|volatile)\b', Keyword.Declaration),
            (r'(boolean|byte|char|double|float|int|long|short|void)\b',
             Keyword.Type),
            (r'(package)(\s+)', bygroups(Keyword.Namespace, Text), 'import'),
            (r'(true|false|null)\b', Keyword.Constant),
            (r'(class|interface)(\s+)', bygroups(Keyword.Declaration,
                                                 Text), 'class'),
            (r'(var)(\s+)', bygroups(Keyword.Declaration, Text), 'var'),
            (r'(import(?:\s+static)?)(\s+)', bygroups(Keyword.Namespace,
                                                      Text), 'import'),
            (r'"(\\\\|\\"|[^"])*"', String),
            (r"'\\.'|'[^\\]'|'\\u[0-9a-fA-F]{4}'", String.Char),
            (r'(\.)((?:[^\W\d]|\$)[\w$]*)',
             bygroups(Punctuation, Name.Attribute)),
            (r'^\s*([^\W\d]|\$)[\w$]*:', Name.Label),
            (r'([^\W\d]|\$)[\w$]*', Name),
            (r'([0-9][0-9_]*\.([0-9][0-9_]*)?|'
             r'\.[0-9][0-9_]*)'
             r'([eE][+\-]?[0-9][0-9_]*)?[fFdD]?|'
             r'[0-9][eE][+\-]?[0-9][0-9_]*[fFdD]?|'
             r'[0-9]([eE][+\-]?[0-9][0-9_]*)?[fFdD]|'
             r'0[xX]([0-9a-fA-F][0-9a-fA-F_]*\.?|'
             r'([0-9a-fA-F][0-9a-fA-F_]*)?\.[0-9a-fA-F][0-9a-fA-F_]*)'
             r'[pP][+\-]?[0-9][0-9_]*[fFdD]?', Number.Float),
            (r'0[xX][0-9a-fA-F][0-9a-fA-F_]*[lL]?', Number.Hex),
            (r'0[bB][01][01_]*[lL]?', Number.Bin),
            (r'0[0-7_]+[lL]?', Number.Oct),
            (r'0|[1-9][0-9_]*[lL]?', Number.Integer),
            (r'[~^*!%&\[\]<>|+=/?-]', Operator),
            (r'[{}();:.,]', Punctuation),
            (r'\n', Text)
        ],
        'class': [(r'([^\W\d]|\$)[\w$]*', Name.Class, '#pop')],
        'var': [(r'([^\W\d]|\$)[\w$]*', Name, '#pop')],
        'import': [(r'[\w.]+\*?', Name.Namespace, '#pop')],
    }
