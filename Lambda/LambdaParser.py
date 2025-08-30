
import ply.yacc as yacc
from Lambda.LambdaLexer import LambdaLexer


class LambdaParser:
    def __init__(self):
        self.lexer = LambdaLexer()
        self.lexer.build()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self)

    # Grammar rules as instance methods
    def p_exprStart_1(self, p):
        'exprStart : expr SEMI'
        p[0] = p[1]

    def p_exprStart_2(self, p):
        'exprStart : expr LBRACKET NAME EQUALS expr RBRACKET SEMI'
        p[0] = ['subst', p[1], p[3].upper(), p[5]]

    def p_exprStart_3(self, p):
        'exprStart : FV LBRACKET expr RBRACKET SEMI'
        p[0] = ['freevars', p[3]]

    def p_exprStart_4(self, p):
        'exprStart : ALPHA LBRACKET expr COMMA NAME RBRACKET SEMI'
        p[0] = ['alpha', p[3], p[5].upper()]

    def p_expr_1(self, p):
        'expr : NUMBER'
        p[0] = ['num', p[1]]

    def p_expr_2(self, p):
        'expr : NAME'
        p[0] = ['name', p[1].upper()]

    def p_expr_3(self, p):
        'expr : LPAREN expr expr RPAREN'
        if p[2][0] == 'lambda':
            p[0] = ['apply', p[2], p[3], True]  # beta-reduction possible
        else:
            p[0] = ['apply', p[2], p[3], False]  # beta-reduction not possible

    def p_expr_4(self, p):
        'expr : LPAREN LAMBDA NAME expr RPAREN'
        p[0] = ['lambda', p[3].upper(), p[4]]

    def p_expr_5(self, p):
        'expr : LPAREN OP expr expr RPAREN'
        p[0] = [p[2], p[3], p[4]]

    def p_error(self, p):
        print("Syntax error in input!")

    def parse(self, s):
        return self.parser.parse(s, lexer=self.lexer.lexer)
