import ply.yacc as yacc
from DLOG.DLOGLexer import DLOGLexer

class DLOGParser:
    def __init__(self):
        self.lexer = DLOGLexer()
        self.lexer.build()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self)

    def p_ddb(self, p):
        'ddb : idb_rules DOLLAR'
        p[0] = p[1]

    def p_idb_rules_1(self, p):
        'idb_rules : idb_rule'
        p[0] = [p[1]]

    def p_idb_rules_2(self, p):
        'idb_rules : idb_rules idb_rule'
        p[0] = p[1] + [p[2]]

    def p_idb_rule(self, p):
        'idb_rule : predicate IMPLIES idb_body PERIOD'
        p[0] = (p[1],p[3])

    def p_idb_body_1(self, p):
        'idb_body : literal'
        p[0] = [p[1]]

    def p_idb_body_2(self, p):
        'idb_body : idb_body COMMA literal'
        p[0] = p[1] + [p[3]]

    def p_literal_1(self, p):
        'literal : NOTOP predicate'
        p[0] = ('neg',p[2])

    def p_literal_2(self, p):
        'literal : predicate'
        p[0] = ('pos',p[1])

    def p_predicate_1(self, p):
        'predicate ::= NAME LPAREN arg_list RPAREN'
        p[0] = ('regular',p[1],p[3])

    def p_predicate_2(self, p):
        'predicate : arg COMPARISON arg'
        p[0] = ('comparison',p[1],p[2],p[3])

    def p_arg_list_1(self, p):
        'arg_list : arg'
        p[0] = [p[1]]

    def p_arg_list_2(self, p):
        'arg_list : arg_list COMMA arg'
        p[0] = p[1] + [p[3]]

    def p_arg_1(self, p):
        'arg : NUMBER'
        p[0] = ('num',p[1])

    def p_arg_2(self, p):
        'arg : STRING'
        p[0] = ('str',p[1])

    def p_arg_3(self, p):
        'arg : VARIABLE'
        p[0] = ('var',p[1])

    def p_error(self, p):
        raise TypeError("Syntax error: '%s'" % p.value)

    def parse(self, s):
        return self.parser.parse(s, lexer=self.lexer.lexer)
