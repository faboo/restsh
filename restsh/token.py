from typing import Tuple, Type, List
import re

class Token:
    openParse = True

    def __init__(self, text:str) -> None:
        self.text:str = text

    def __repr__(self) -> str:
        return '%s(%s)' % (self.__class__.__name__, self.text)

class Eq(Token): pass

class Dot(Token): pass

class LParen(Token): pass

class RParen(Token): pass

class LAngle(Token): pass

class RAngle(Token): pass

class LBrace(Token): pass

class RBrace(Token): pass

class LBracket(Token): pass

class RBracket(Token): pass

class Comma(Token): pass

class Colon(Token): pass

class SemiColon(Token): pass

class Bang(Token): pass

class BSlash(Token): pass

class Let(Token): pass

class Imp(Token): pass

class Help(Token):
    openParse = False

class Ext(Token): pass

class Try(Token): pass

class If(Token): pass

class Then(Token): pass

class Else(Token): pass

class Sym(Token):
    openParse = False

class Op(Token): pass

class Str(Token):
    openParse = False

class Flt(Token):
    openParse = False

class Int(Token):
    openParse = False

tokens:List[Tuple[Type[Token], re.Pattern]] = \
    [ (Eq, re.compile(r'=($|\b|(?=\s))')) # EOT isn't a boundary??
    , (Dot, re.compile(r'\.'))
    , (LParen, re.compile(r'\('))
    , (RParen, re.compile(r'\)'))
    , (LBrace, re.compile(r'{'))
    , (RBrace, re.compile(r'}'))
    , (LBracket, re.compile(r'\['))
    , (RBracket, re.compile(r'\]'))
    , (Comma, re.compile(r','))
    , (Colon, re.compile(':'))
    , (SemiColon, re.compile(';'))
    , (Bang, re.compile('!'))
    , (BSlash, re.compile(r'\\'))

    , (Let, re.compile(r'let\b'))
    , (Imp, re.compile(r'import\b'))
    , (Help, re.compile(r'help\b'))
    , (Ext, re.compile(r'exit\b'))
    , (Try, re.compile(r'try\b'))

    , (If, re.compile(r'if\b'))
    , (Then, re.compile(r'then\b'))
    , (Else, re.compile(r'else\b'))

    , (Sym, re.compile('[_a-zA-Z][_a-zA-Z0-9]*'))
    , (Op, re.compile('[-+*/|&^$@?~=<>]+'))
    , (Str, re.compile(r'"(\\"|[^"])*"'))
    , (Flt, re.compile(r'[+-]?[0-9]+\.[0-9]+'))
    , (Int, re.compile('[+-]?[0-9]+'))
    ]

