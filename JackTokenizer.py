import re
import sys
from collections import namedtuple

Token = namedtuple('Token', ('type', 'value'))


class JackTokenizer:

    # Expressions for lexical elements in Jack
    INT = '\d+'
    STR = '"[^"]*"'
    ID = '[A-z_][A-z_\d]*'
    SYMBOL = '\{|\}|\(|\)|\[|\]|\.|,|;|\+|-|\*|/|&|\||\<|\>|=|~'
    KEYWORD = ('(class|constructor|function|method|field|static|var|int|char|'
               'boolean|void|true|false|null|this|let|do|if|else|while|return)')

    # A list of tuples of a regular expression and its type as string
    LEXICAL_TYPES = [(KEYWORD, 'keyword'),
                     (SYMBOL, 'symbol'),
                     (INT, 'integerConstant'),
                     (STR, 'stringConstant'),
                     (ID, 'identifier')]

    # A regular expression to split between lexical components/tokens
    SPLIT = '(' + '|'.join(expr for expr in [SYMBOL, STR]) + ')|\s+'

    @staticmethod
    def removeComments(file):

        # Use non-greedy regex to avoid eating lines of code
        uncommented = re.sub('//.*?\n', '\n', file)
        uncommented = re.sub('/\*.*?\*/', '', uncommented, flags=re.DOTALL)
        return uncommented

    def __init__(self, file):
        self.code = JackTokenizer.removeComments(file)
        self.tokens = self.tokenize()

    def tokenize(self):
        splitCode = re.split(self.SPLIT, self.code)
        tokens = []

        for lex in splitCode:
            # Skip non-tokens
            if lex is None or re.match('^\s*$', lex):
                continue

            # Check all possible lexical types, if
            for expr, lexType in self.LEXICAL_TYPES:
                if re.match(expr, lex):
                    tokens.append(Token(lexType, lex))
                    break
            else:
                print('Error: unknown token', lex)
                sys.exit(1)

        return tokens

    def curToken(self):
        return self.tokens[0] if self.tokens else None

    def advance(self):
        return self.tokens.pop(0) if self.tokens else None
