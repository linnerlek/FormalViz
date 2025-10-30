import ply.yacc as yacc
from DRCLexer import DRCLexer


class DRCParser:
    precedence = (('right', 'IMPLIES'),
                  ('left', 'AND', 'OR'), ('right', 'NOTOP'),)

    def p_Query(self, p):
        'Query : LBRACE varList BAR formula RBRACE'
        p[0] = {'type': 'query', 'varlist': p[2], 'child': p[4]}

    def p_varList_single(self, p):
        'varList : NAME'
        p[0] = [p[1]]

    def p_varList_append(self, p):
        'varList : varList COMMA NAME'
        p[0] = p[1] + [p[3]]

    def p_formula_atomic(self, p):
        'formula : atomic_formula'
        p[0] = p[1]

    def p_formula_and(self, p):
        'formula : formula AND formula'
        p[0] = {'type': 'and', 'left': p[1], 'right': p[3]}

    def p_formula_or(self, p):
        'formula : formula OR formula'
        p[0] = {'type': 'or', 'left': p[1], 'right': p[3]}

    def p_formula_paren(self, p):
        'formula : LPAREN formula RPAREN'
        p[0] = p[2]

    # do we need this? Can we not give NOT the highest precedence?
    # def p_formula_not_paren(p):
    #    'formula : NOTOP LPAREN formula RPAREN'
    #    inner = p[3]
    #    if isinstance(inner, dict) and inner.get('type') == 'not':
    #        p[0] = inner['child']
    #    else:
    #        p[0] = {'type': 'not', 'child': inner}

    def p_formula_not(self, p):
        'formula : NOTOP formula'
        inner = p[2]
        if isinstance(inner, dict) and inner.get('type') == 'not':
            p[0] = inner['child']
        else:
            p[0] = {'type': 'not', 'child': inner}

    def p_formula_exists(self, p):
        'formula : EXISTS LBRACK varList RBRACK LPAREN formula RPAREN'
        # exists[varList](formula)
        p[0] = {'type': 'exists', 'varlist': p[3], 'child': p[6]}

    def p_formula_forall(self, p):
        'formula : FORALL LBRACK varList RBRACK LPAREN formula RPAREN'
        # Transform FORALL into NOT (EXISTS varlist (NOT formula)).
        def _negate(node):
            if isinstance(node, dict):
                t = node.get('type')
                if t == 'not':
                    # not(not X) -> X
                    return node['child']
                if t == 'implies':
                    # not(P -> Q) == P and not Q
                    return {'type': 'and', 'left': node['left'], 'right': {'type': 'not', 'child': node['right']}}
            return {'type': 'not', 'child': node}

        inner_neg = _negate(p[6])
        exists_node = {'type': 'exists', 'varlist': p[3], 'child': inner_neg}
        p[0] = {'type': 'not', 'child': exists_node}

    def p_atomic_formula_predicate(self, p):
        'atomic_formula : NAME LPAREN arg_list RPAREN'
        p[0] = {'type': 'predicate', 'name': p[1], 'args': p[3]}

    def p_AtomicFormula_comp(self, p):
        'atomic_formula : arg COMPARISON arg'
        left_val, left_type = p[1]
        right_val, right_type = p[3]
        p[0] = {
            'type': 'comp',
            'left': left_val,
            'left_type': left_type,
            'op': p[2],
            'right': right_val,
            'right_type': right_type,
        }

    def p_arg_list_single(self, p):
        'arg_list : arg'
        p[0] = [p[1]]

    def p_arg_list_append(self, p):
        'arg_list : arg_list COMMA arg'
        p[0] = p[1] + [p[3]]

    def p_arg_name(self, p):
        'arg : NAME'
        p[0] = (p[1], 'col')

    def p_arg_string(self, p):
        'arg : STRING'
        p[0] = (p[1], 'str')

    def p_arg_number(self, p):
        'arg : NUMBER'
        p[0] = (p[1], 'num')

    def p_formula_implies(self, p):
        'formula : formula IMPLIES formula'
        p[0] = {'type': 'implies', 'left': p[1], 'right': p[3]}

    def p_error(self, p):
        raise TypeError("Syntax error: '%s'" % (p.value if p else 'EOF'))

    def __init__(self):
        self.lexer = DRCLexer()
        self.lexer.build()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self)

    def parse(self, s):
        return self.parser.parse(s, lexer=self.lexer.lexer)


if __name__ == '__main__':
    parser = DRCParser()
    # sample = "{A | actors(A) and not exists[M](acts(M,A) and not movies(M,'Kurosawa'))}"
    sample = "{A | actors(A) and not acts(M,A) and not movies(M,'Kurosawa')}"
    # sample = "{A | actors(A) and forall[M](acts(M, A) -> movies(M, 'Kurosawa'))}"
    print(sample)
    result = parser.parse(sample)
    import pprint
    pprint.pprint(result)
