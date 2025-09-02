import ply.lex as lex


class DLOGLexer:
    tokens = ['LPAREN', 'RPAREN', 'DOLLAR', 'COMMA', 'PERIOD', 'IMPLIES',
              'NOTOP', 'NAME', 'VARIABLE', 'COMPARISON', 'NUMBER', 'STRING']

    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_DOLLAR = r'\$'
    t_COMMA = r'\,'
    t_PERIOD = r'\.'
    t_IMPLIES = r':-'
    t_VARIABLE = r'[_A-Z][_A-Za-z0-9]*'
    t_COMPARISON = r'<>|<=|>=|<|>|='

    def t_NAME(self, t):
        r'[a-z][_a-zA-Z0-9]*'

        if t.value.upper() == 'NOT':

            t.type = 'NOTOP'

        else:

            t.type = 'NAME'

        return t

    def t_NUMBER(self, t):
        r'[-+]?[0-9]+(\.([0-9]+)+)?'
        if '.' in t.value:

            t.value = float(t.value)

        else:

            t.value = int(t.value)

        t.type = 'NUMBER'
        return t

    def t_STRING(self, t):
        r"'[^']*'"
        t.value = t.value.strip()[1:-1]
        t.type = 'STRING'
        return t

    # Ignored characters
    t_ignore = " \r\n\t"
    t_ignore_COMMENT = r'\#.*'

    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        # t.lexer.skip(1)
        raise Exception('LEXER ERROR')

    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
        return self.lexer
# Test it out
# data = '''
# answer(F,M,L) :-
#    employee(F,M,L,S,_,_,_,_,_,5),
#    works_on(S,P,H),
#    projects('ProductX',P,_,_),
#    H >= 10.
# $
# '''
#
# Give the lexer some input
# print("Tokenizing: ",data)
# lexer.input(data)
#
# Tokenize
# while True:
#    tok = lexer.token()
#    if not tok:
#        break      # No more input
#    print(tok)
