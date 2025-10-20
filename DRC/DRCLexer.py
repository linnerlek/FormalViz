import ply.lex as lex

class DRCLexer:
    tokens = [
        'COMMA', 'BAR',
        'AND', 'OR', 'NOTOP', 'EXISTS', 'FORALL',
        'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
        'NAME', 'COMPARISON', 'IMPLIES', 'NUMBER', 'STRING', 'LBRACK', 'RBRACK'
    ]

    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_COMMA = r','
    t_BAR = r'\|'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_LBRACK = r'\['
    t_RBRACK = r'\]'
    t_COMPARISON = r'<=|>=|<>|=|<|>'
    t_IMPLIES = r'->'


    def t_NAME(t):
        r'[A-Za-z_][_A-Za-z0-9]*'
        low = t.value.lower()
        if low == 'and':
            t.type = 'AND'
        elif low == 'or':
            t.type = 'OR'
        elif low == 'not':
            t.type = 'NOTOP'
        elif low == 'exists':
            t.type = 'EXISTS'
        elif low == 'forall':
            t.type = 'FORALL'
        else:
            t.type = 'NAME'
        return t


    def t_NUMBER(t):
        r'[-+]?[0-9]+(\.([0-9]+)+)?'
        t.value = float(t.value)
        t.type = 'NUMBER'
        return t


    def t_STRING(t):
        r"'[^']*'"
        t.value = t.value.strip()[1:-1]
        t.type = 'STRING'
        return t


    t_ignore = ' \r\n\t'
    t_ignore_COMMENT = r'\#.*'


    def t_error(t):
        print("Illegal character '%s'" % t.value[0])
        raise RuntimeError('LEXER ERROR')


    lexer = lex.lex()

# testing it out
# if __name__ == '__main__':
#     data = "{A | actors(A) and (forall M)(acts(M,A) -> movies(M,'Kurosawa'))}"
#     print('Tokenizing sample:')
#     DRCLexer.lexer.input(data)
#     while True:
#         tok = DRCLexer.lexer.token()
#         if not tok:
#             break
#         print(tok)
