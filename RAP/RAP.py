
import sys
import sqlite3
import ply.yacc as yacc
import ply.lex as lex

# RAPParser class encapsulating the parser and lexer to avoid issues with other parsers


class RAPParser:

    reserved = {
        'project': 'PROJECT', 'rename': 'RENAME', 'union': 'UNION', 'intersect': 'INTERSECT',
        'minus': 'MINUS', 'join': 'JOIN', 'times': 'TIMES', 'select': 'SELECT', 'and': 'AND',
        'aggregate': 'AGGREGATE'
    }
    tokens = [
        'SEMI', 'COMPARISON', 'LPARENT', 'RPARENT', 'COMMA', 'NUMBER', 'ID', 'STRING',
        'LBRACKET', 'RBRACKET', 'AGG_OP'
    ] + list(reserved.values())

    def __init__(self):
        # Build lexer and parser
        self.lexer = lex.lex(module=self)
        self.parser = yacc.yacc(
            module=self, start='query', debug=False, write_tables=False)

    t_SEMI = r';'
    t_AND = r'[Aa][Nn][Dd]'
    t_LPARENT = r'\('
    t_RPARENT = r'\)'
    t_PROJECT = r'[Pp][Rr][Oo][Jj][Ee][Cc][Tt]'
    t_RENAME = r'[Rr][Ee][Nn][Aa][Mm][Ee]'
    t_UNION = r'[Uu][Nn][Ii][Oo][Nn]'
    t_MINUS = r'[Mm][Ii][Nn][Uu][Ss]'
    t_INTERSECT = r'[Ii][Nn][Tt][Ee][Rr][Ss][Ee][Cc][Tt]'
    t_JOIN = r'[Jj][Oo][Ii][Nn]'
    t_TIMES = r'[Tt][Ii][Mm][Ee][Ss]'
    t_SELECT = r'[Ss][Ee][Ll][Ee][Cc][Tt]'
    t_COMMA = r','
    t_COMPARISON = r'<>|<=|>=|<|>|='
    t_RBRACKET = r'\]'
    t_LBRACKET = r'\['
    t_AGGREGATE = r'[Aa][Gg][Gg][Rr][Ee][Gg][Aa][Tt][Ee]'
    t_ignore = ' \t'

    def t_STRING(self, t):
        r"'[^']*'"
        t.value = t.value.strip()[1:-1]
        t.type = 'STRING'
        return t

    def t_NUMBER(self, t):
        r'[-+]?[1-9][0-9]*(\.([0-9]+)?)?'
        t.type = 'NUMBER'
        return t

    def t_ID(self, t):
        r'[a-zA-Z][_a-zA-Z0-9]*'
        if t.value.lower() in ['sum', 'avg', 'count', 'min', 'max']:
            t.type = 'AGG_OP'
        else:
            t.type = self.reserved.get(t.value.lower(), 'ID')
        t.value = t.value.upper()
        return t

    t_ignore_COMMENT = r'\#.*'

    def t_newline(self, t):
        r'[\r\n]+'
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        print("Illegal Character '%s'" % t.value[0])
        t.lexer.skip(1)

    precedence = (
        ('right', 'UNION', 'MINUS', 'INTERSECT'),
        ('right', 'TIMES', 'JOIN'),
    )

    def p_query(self, p):
        'query : expr SEMI'
        p[0] = p[1]

    def p_expr(self, p):
        '''expr : proj_expr 
                | rename_expr 
                | union_expr     
                | minus_expr 
                | intersect_expr 
                | join_expr 
                | times_expr 
                | paren_expr 
                | select_expr 
                | aggregate_expr_1
                | aggregate_expr_2
                | aggregate_expr_3 '''
        p[0] = p[1]

    def p_ID(self, p):
        'expr : ID'
        n = Node("relation", None, None)
        n.set_relation_name(p[1])
        p[0] = n

    def p_proj_expr(self, p):
        'proj_expr : PROJECT LBRACKET attr_list RBRACKET LPARENT expr RPARENT'
        n = Node("project", p[6], None)
        n.set_columns(p[3])
        p[0] = n

    def p_rename_expr(self, p):
        'rename_expr : RENAME LBRACKET attr_list RBRACKET LPARENT expr RPARENT'
        n = Node("rename", p[6], None)
        n.set_columns(p[3])
        p[0] = n

    def p_attr_list(self, p):
        'attr_list : ID'
        p[0] = [p[1].upper()]

    def p_attr_list_2(self, p):
        'attr_list : attr_list COMMA ID'
        p[0] = p[1] + [p[3].upper()]

    def p_union_expr(self, p):
        'union_expr : expr UNION expr'
        n = Node("union", p[1], p[3])
        p[0] = n

    def p_minus_expr(self, p):
        'minus_expr : expr MINUS expr '
        n = Node("minus", p[1], p[3])
        p[0] = n

    def p_intersect_expr(self, p):
        'intersect_expr : expr INTERSECT expr'
        n = Node("intersect", p[1], p[3])
        p[0] = n

    def p_join_expr(self, p):
        'join_expr : expr JOIN expr'
        n = Node("join", p[1], p[3])
        p[0] = n

    def p_times_expr(self, p):
        'times_expr : expr TIMES expr'
        n = Node("times", p[1], p[3])
        p[0] = n

    def p_paren_expr(self, p):
        'paren_expr : LPARENT expr RPARENT'
        p[0] = p[2]

    def p_select_expr(self, p):
        'select_expr : SELECT LBRACKET condition RBRACKET LPARENT expr RPARENT'
        n = Node("select", p[6], None)
        n.set_conditions(p[3])
        p[0] = n

    def p_condition(self, p):
        'condition : simple_condition'
        p[0] = [p[1]]

    def p_condition_2(self, p):
        'condition : condition AND simple_condition'
        p[0] = p[1] + [p[3]]

    def p_simple_condition(self, p):
        'simple_condition : operand COMPARISON operand'
        p[0] = [p[1][0], p[1][1], p[2], p[3][0], p[3][1]]

    def p_operand_1(self, p):
        'operand : ID'
        p[0] = ['col', p[1].upper()]

    def p_operand_2(self, p):
        'operand : STRING'
        p[0] = ['str', p[1]]

    def p_operand_3(self, p):
        'operand : NUMBER'
        p[0] = ['num', float(p[1])]

    # AGGREGATE Rules
    def p_aggregate_expr_1(self, p):
        'aggregate_expr_1 : AGGREGATE LBRACKET LPARENT attr_list RPARENT COMMA LPARENT gen_attr_list RPARENT RBRACKET LPARENT expr RPARENT'
        n = Node("aggregate1", p[12], None)
        n.set_columns(p[4])
        n.set_aggregate_project_list(p[8])
        p[0] = n

    def p_aggregate_expr_2(self, p):
        'aggregate_expr_2 : AGGREGATE LBRACKET LPARENT attr_list RPARENT COMMA LPARENT gen_attr_list RPARENT COMMA LPARENT attr_list RPARENT RBRACKET LPARENT expr RPARENT'
        n = Node("aggregate2", p[16], None)
        n.set_columns(p[4])
        n.set_aggregate_project_list(p[8])
        n.set_aggregate_groupby_list(p[12])
        p[0] = n

    def p_aggregate_expr_3(self, p):
        'aggregate_expr_3 : AGGREGATE LBRACKET LPARENT attr_list RPARENT COMMA LPARENT gen_attr_list RPARENT COMMA LPARENT attr_list RPARENT COMMA LPARENT gen_condition RPARENT RBRACKET LPARENT expr RPARENT'
        n = Node("aggregate3", p[20], None)
        n.set_columns(p[4])
        n.set_aggregate_project_list(p[8])
        n.set_aggregate_groupby_list(p[12])
        n.set_aggregate_having_condition(p[16])
        p[0] = n

    def p_gen_attr_list_1(self, p):
        'gen_attr_list : gen_attr'
        p[0] = [p[1]]

    def p_gen_attr_list_2(self, p):
        'gen_attr_list : gen_attr_list COMMA gen_attr'
        p[0] = p[1] + [p[3]]

    def p_gen_attr_1(self, p):
        'gen_attr : ID'
        p[0] = ('id', p[1].upper())

    def p_gen_attr_2(self, p):
        'gen_attr : AGG_OP LPARENT ID RPARENT'
        p[0] = ('agg', (p[1].upper(), p[3].upper()))

    def p_gen_condition_1(self, p):
        'gen_condition : simple_gen_condition'
        p[0] = [p[1]]

    def p_gen_condition_2(self, p):
        'gen_condition : gen_condition AND simple_gen_condition'
        p[0] = p[1] + [p[3]]

    def p_simple_gen_condition_1(self, p):
        'simple_gen_condition : gen_operand COMPARISON gen_operand'
        p[0] = [p[1][0], p[1][1], p[2], p[3][0], p[3][1]]

    def p_simple_gen_condition_2(self, p):
        'simple_gen_condition : gen_operand COMPARISON operand'
        p[0] = [p[1][0], p[1][1], p[2], p[3][0], p[3][1]]

    def p_simple_gen_condition_3(self, p):
        'simple_gen_condition : operand COMPARISON gen_operand'
        p[0] = [p[1][0], p[1][1], p[2], p[3][0], p[3][1]]

    def p_simple_gen_condition_4(self, p):
        'simple_gen_condition : operand COMPARISON operand'
        p[0] = [p[1][0], p[1][1], p[2], p[3][0], p[3][1]]

    def p_gen_operand(self, p):
        'gen_operand : AGG_OP LPARENT ID RPARENT'
        p[0] = ('agg', (p[1].upper(), p[3].upper()))

    def p_error(self, p):
        raise TypeError(f"Syntax error: '{getattr(p, 'value', None)}'")

    # --- Public method to parse input ---
    def parse(self, data):
        return self.parser.parse(data, lexer=self.lexer)


# data = '''project[dname](
# select[dnumber="25"](department)
# );'''
#
# lexer.input(data)
#
# while True:
#    tok = lexer.token()
#    if not tok:
#        break
#    print(tok)
# from Node import *
# from RALexer import tokens

class SQLite3():

    def __init__(self):
        self.relations = []
        self.attributes = {}
        self.domains = {}
        self.conn = None

    def open(self, dbfile):
        self.conn = sqlite3.connect(dbfile)
        query = "select name from sqlite_schema where type='table'"
        c = self.conn.cursor()
        c.execute(query)
        records = c.fetchall()
        for record in records:
            self.relations.append(record[0].upper())
        for rname in self.relations:
            query = "select name,type from pragma_table_info('"+rname+"')"
            c.execute(query)
            records = c.fetchall()
            attrs = []
            doms = []
            for record in records:
                attrs.append(record[0].upper())
                col_type = record[1].upper()
                if col_type.startswith("INT") or col_type.startswith("NUM"):
                    doms.append("INTEGER")
                elif col_type.startswith("DEC"):
                    doms.append("DECIMAL")
                elif col_type.startswith("CHAR") or col_type.startswith("VARCHAR") or col_type.startswith("TEXT"):
                    doms.append("VARCHAR")
                else:
                    doms.append("VARCHAR")
            self.attributes[rname] = attrs
            self.domains[rname] = doms

    def close(self):
        self.conn.close()

    def relationExists(self, rname):
        return rname in self.relations

    def getAttributes(self, rname):
        return self.attributes[rname]

    def getDomains(self, rname):
        return self.domains[rname]

    def displayDatabaseSchema(self):
        print("*********************************************")
        for rname in self.relations:
            print(rname+"(", end="")
            attrs = self.attributes[rname]
            doms = self.domains[rname]
            for i, (aname, atype) in enumerate(zip(attrs, doms)):
                if i == len(attrs)-1:
                    print(aname+":"+atype+")")
                else:
                    print(aname+":"+atype+",", end="")
        print("*********************************************")

    def displayQueryResults(self, query, tree):
        print("\nANSWER(", end="")
        nCols = len(tree.get_attributes())
        for i, col in enumerate(tree.get_attributes()):
            if i == (nCols-1):
                print(col+":"+tree.get_domains()[i]+")")
            else:
                print(col+":"+tree.get_domains()[i]+",", end="")
        # execute the query against sqlite3 database
        c = self.conn.cursor()
        # print("Executing query:",query)
        c.execute(query)
        records = c.fetchall()
        rowCount = len(records)
        print("Number of tuples = "+str(rowCount)+"\n")
        for record in records:
            for val in record:
                print(str(val)+":", end="")
            print()
        print()
        c.close()

    def isQueryResultEmpty(self, query):
        c = self.conn.cursor()
        records = c.execute(query)
        c.close()
        return len(records) == 0


class Node:

    def __init__(self, ntype, lc, rc):
        self.node_type = ntype		# "relation", "select", "project", "times",...
        self.left_child = lc		# left child
        self.right_child = rc		# right child
        self.columns = None		# list of column names for RENAME and PROJECT and AGGREGATE
        # list of conditions for SELECT [(lop,lot,c,rop,rot)..]
        self.conditions = None

        # the following variables are populated in RA.py
        # relation name at node (tempN interior, regular leaf)
        self.relation_name = None
        self.attributes = None		# holds schema attributes at node
        self.domains = None		# holds schema domains of attributes at node
        self.join_columns = []		# holds common column names for join

        # added for AGGREGATE
        self.aggregate_project_list = []
        self.aggregate_groupby_list = []
        self.aggregate_having_condition = []

    def get_attributes(self):
        return self.attributes

    def get_columns(self):
        return self.columns

    def get_conditions(self):
        return self.conditions

    def get_right_child(self):
        return self.right_child

    def get_left_child(self):
        return self.left_child

    def get_domains(self):
        return self.domains

    def get_node_type(self):
        return self.node_type

    def get_relation_name(self):
        return self.relation_name

    def get_join_columns(self):
        return self.join_columns

    def get_aggregate_project_list(self):
        return self.aggregate_project_list

    def get_aggregate_groupby_list(self):
        return self.aggregate_groupby_list

    def get_aggregate_having_condition(self):
        return self.aggregate_having_condition

    def set_attributes(self, attributes):
        self.attributes = attributes

    def set_conditions(self, conditions):
        self.conditions = conditions

    def set_right_child(self, right_node):
        self.right_child = right_node

    def set_left_child(self, left_node):
        self.left_child = left_node

    def set_columns(self, cols):
        self.columns = cols

    def set_domains(self, doms):
        self.domains = doms

    def set_node_type(self, n_type):
        self.node_type = n_type

    def set_relation_name(self, r_name):
        self.relation_name = r_name

    def set_join_columns(self, jc):
        self.join_columns = jc

    def set_aggregate_project_list(self, apl):
        self.aggregate_project_list = apl

    def set_aggregate_groupby_list(self, agl):
        self.aggregate_groupby_list = agl

    def set_aggregate_having_condition(self, hc):
        self.aggregate_having_condition = hc

    def print_tree(self, n):
        if self.node_type == "relation":
            print(" "*n, end="")
            print("NODE TYPE: " + self.node_type + "  ")
            print(" "*n, end="")
            print("Relation Name is : " + self.relation_name)
            if self.attributes != None:
                print(" "*n, end="")
                print("Schema is : " + str(self.attributes))
            if self.domains != None:
                print(" "*n, end="")
                print("Datatypes is : " + str(self.domains)+"\n")
        elif self.node_type == "project" or self.node_type == "rename":
            print(" "*n, end="")
            print("NODE TYPE: " + self.node_type + "  ")
            print(" "*n, end="")
            print("Atributes are : "+str(self.columns))
            if self.relation_name != None:
                print(" "*n, end="")
                print("Relation Name is : " + self.relation_name)
            if self.attributes != None:
                print(" "*n, end="")
                print("Schema is : " + str(self.attributes))
            if self.domains != None:
                print(" "*n, end="")
                print("Datatypes is : " + str(self.domains)+"\n")
            self.left_child.print_tree(n+4)
        elif self.node_type == "select":
            print(" "*n, end="")
            print("NODE TYPE: " + self.node_type + "  ")
            for cond in self.conditions:
                print(" "*n, end="")
                print(cond[0], end="")
                print(":", end="")
                print(cond[1], end="")
                print(":", end="")
                print(cond[2], end="")
                print(":", end="")
                print(cond[3], end="")
                print(":", end="")
                print(cond[4])
            if self.relation_name != None:
                print(" "*n, end="")
                print("Relation Name is : " + self.relation_name)
            if self.attributes != None:
                print(" "*n, end="")
                print("Schema is : " + str(self.attributes))
            if self.domains != None:
                print(" "*n, end="")
                print("Datatypes is : " + str(self.domains)+"\n")
            self.left_child.print_tree(n+4)
        elif self.node_type in ["union", "minus", "join", "intersect", "times"]:
            print(" "*n, end="")
            print("NODE TYPE: "+self.node_type+"  ")
            if self.relation_name != None:
                print(" "*n, end="")
                print("Relation Name is : " + self.relation_name)
            if self.attributes != None:
                print(" "*n, end="")
                print("Schema is : " + str(self.attributes))
            if self.domains != None:
                print(" "*n, end="")
                print("Datatypes is : " + str(self.domains)+"\n")
            self.left_child.print_tree(n+4)
            self.right_child.print_tree(n+4)
        elif self.node_type == "aggregate1":
            print(" "*n, end="")
            print("NODE TYPE: " + self.node_type + "  ")
            print(" "*n, end="")
            print("Rename Atributes are : "+str(self.columns), end="")
            print("Project Atributes are : "+str(self.aggregate_project_list))
            self.left_child.print_tree(n+4)
        elif self.node_type == "aggregate2":
            print(" "*n, end="")
            print("NODE TYPE: " + self.node_type + "  ")
            print(" "*n, end="")
            print("Rename Atributes are : "+str(self.columns), end="")
            print("Project Atributes are : " +
                  str(self.aggregate_project_list), end="")
            print("Groupby Atributes are : "+str(self.aggregate_groupby_list))
            self.left_child.print_tree(n+4)
        elif self.node_type == "aggregate3":
            print(" "*n, end="")
            print("NODE TYPE: " + self.node_type + "  ")
            print(" "*n, end="")
            print("Rename Atributes are : "+str(self.columns), end="")
            print("Project Atributes are : " +
                  str(self.aggregate_project_list), end="")
            print("Groupby Atributes are : " +
                  str(self.aggregate_groupby_list), end="")
            print("Having condition is : "+str(self.aggregate_having_condition))
            self.left_child.print_tree(n+4)
        else:
            pass


# Global variable used for setting temporary table names
count = 0

# Instantiate the RAPParser class
rap_parser = RAPParser()


def execute_file(filename, db):
    try:
        with open(filename) as f:
            data = f.read().splitlines()
        result = " ".join(
            list(filter(lambda x: len(x) > 0 and x[0] != "#", data)))
        try:
            tree = rap_parser.parse(result)
            set_temp_table_names(tree)
            msg = semantic_checks(tree, db)
            if msg == 'OK':
                query = generateSQL(tree, db)
                db.displayQueryResults(query, tree)
            else:
                print(msg)
        except Exception as inst:
            print(inst.args[0])
    except FileNotFoundError:
        print("FileNotFoundError: A file with name '" +
              filename + "' cannot be found")


def read_input():
    result = ''
    data = input('RA: ').strip()
    while True:
        if ';' in data:
            i = data.index(';')
            result += data[0:i+1]
            break
        else:
            result += data + ' '
            data = input('> ').strip()
    return result


def set_temp_table_names(tree):
    if tree != None and tree.get_node_type() != 'relation':
        global count
        set_temp_table_names(tree.get_left_child())
        tree.set_relation_name('TEMP_' + str(count))
        count += 1
        if tree.right_child != None:
            set_temp_table_names(tree.get_right_child())

# perform semantic checks; set tree.attributes and tree.domains along the way
# return "OK" or ERROR message


def semantic_checks(tree, db):
    if tree.get_node_type() == 'relation':
        rname = tree.get_relation_name()
        if not db.relationExists(rname):
            return "Relation '" + rname + "' does not exist"
        tree.set_attributes(db.getAttributes(rname))
        tree.set_domains(db.getDomains(rname))
        return 'OK'

    if tree.get_node_type() == 'select':
        status = semantic_checks(tree.get_left_child(), db)
        if status != 'OK':
            return status
        conditions = tree.get_conditions()
        attrs = tree.get_left_child().get_attributes()
        doms = tree.get_left_child().get_domains()

        for condition in conditions:
            lot = condition[0]
            lop = condition[1]
            rot = condition[3]
            rop = condition[4]
            if lot == "col" and lop not in attrs:
                return "SEMANTIC ERROR (SELECT): Invalid Attribute: " + lop
            if rot == "col" and rop not in attrs:
                return "SEMANTIC ERROR (SELECT): Invalid Attribute: " + rop
            if lot == "col":
                ltype = "str" if doms[attrs.index(lop)] == "VARCHAR" else "num"
            else:
                ltype = lot
            if rot == "col":
                rtype = "str" if doms[attrs.index(rop)] == "VARCHAR" else "num"
            else:
                rtype = rot
            if ltype != rtype:
                return "SEMANTIC ERROR (SELECT): Invalid type comparison " + \
                       lop+":"+ltype+" vs "+rop+":"+rtype
        tree.set_attributes(attrs)
        tree.set_domains(doms)
        return 'OK'

    if tree.get_node_type() == 'times':
        status = semantic_checks(tree.get_left_child(), db)
        if status != 'OK':
            return status
        status = semantic_checks(tree.get_right_child(), db)
        if status != 'OK':
            return status

        lattrs = tree.get_left_child().get_attributes()
        rattrs = tree.get_right_child().get_attributes()
        ldoms = tree.get_left_child().get_domains()
        rdoms = tree.get_right_child().get_domains()

        # Find duplicates
        duplicates = set(lattrs) & set(rattrs)
        t_attrs = []
        t_doms = []

        for i, attr in enumerate(lattrs):
            if attr in duplicates:
                t_attrs.append(attr + "_L")
            else:
                t_attrs.append(attr)
            t_doms.append(ldoms[i])

        for i, attr in enumerate(rattrs):
            if attr in duplicates:
                t_attrs.append(attr + "_R")
            else:
                t_attrs.append(attr)
            t_doms.append(rdoms[i])

        tree.set_attributes(t_attrs)
        tree.set_domains(t_doms)
        return 'OK'

    if tree.get_node_type() in ['union', 'intersect', 'minus']:
        status = semantic_checks(tree.get_left_child(), db)
        if status != 'OK':
            return status
        status = semantic_checks(tree.get_right_child(), db)
        if status != 'OK':
            return status

        lattrs = tree.get_left_child().get_attributes()
        rattrs = tree.get_right_child().get_attributes()
        ldoms = tree.get_left_child().get_domains()
        rdoms = tree.get_right_child().get_domains()

        if len(lattrs) != len(rattrs):
            return "SEMANTIC ERROR (UNION): Incompatible Relations - different number of columns"

        for i, dom in enumerate(ldoms):
            if dom != rdoms[i]:
                return "SEMANTIC ERROR (UNION): " + lattrs[i] + " and " + rattrs[i] + \
                       " have different data types: " + \
                    ldoms[i] + " and " + rdoms[i]

        tree.set_attributes(lattrs)
        tree.set_domains(ldoms)
        return 'OK'

    if tree.get_node_type() == 'join':
        status = semantic_checks(tree.get_left_child(), db)
        if status != 'OK':
            return status
        status = semantic_checks(tree.get_right_child(), db)
        if status != 'OK':
            return status

        lattrs = tree.get_left_child().get_attributes()
        rattrs = tree.get_right_child().get_attributes()
        ldoms = tree.get_left_child().get_domains()
        rdoms = tree.get_right_child().get_domains()

        j_attrs = []
        j_doms = []
        jcols = []

        for i, attr in enumerate(lattrs):
            j_attrs.append(attr)
            j_doms.append(ldoms[i])
            if attr in rattrs:
                jcols.append(attr)

        for i, attr in enumerate(rattrs):
            if attr not in lattrs:
                j_attrs.append(attr)
                j_doms.append(rdoms[i])

        tree.set_join_columns(jcols)
        tree.set_attributes(j_attrs)
        tree.set_domains(j_doms)
        return 'OK'

    if tree.get_node_type() == 'project':
        status = semantic_checks(tree.get_left_child(), db)
        if status != 'OK':
            return status

        p_attrs = tree.get_columns()

        left_child = tree.get_left_child()
        has_aggregate = False
        if left_child.get_node_type() == "join":
            left_grandchild = left_child.get_left_child()
            right_grandchild = left_child.get_right_child()
            has_aggregate = (left_grandchild.get_node_type() in ['aggregate1', 'aggregate2', 'aggregate3'] or
                             right_grandchild.get_node_type() in ['aggregate1', 'aggregate2', 'aggregate3'])

        attrs = left_child.get_attributes()
        doms = left_child.get_domains()

        for attr in p_attrs:
            if '(' in attr and ')' in attr:
                func_name, col_name = attr.split('(')
                col_name = col_name.strip(')')

                if func_name.upper() not in ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']:
                    return f"SEMANTIC ERROR (PROJECT): Unsupported aggregate function {func_name}"

                if col_name != '*' and col_name not in attrs:
                    return f"SEMANTIC ERROR (PROJECT): Attribute {col_name} does not exist for aggregate {func_name}({col_name})"
            else:
                if attr not in attrs:
                    if has_aggregate:
                        if left_child.get_node_type() == "join":
                            left_grandchild = left_child.get_left_child()
                            right_grandchild = left_child.get_right_child()

                            if left_grandchild.get_node_type() in ['aggregate1', 'aggregate2', 'aggregate3']:
                                if attr in left_grandchild.get_columns():
                                    continue

                            if right_grandchild.get_node_type() in ['aggregate1', 'aggregate2', 'aggregate3']:
                                if attr in right_grandchild.get_columns():
                                    continue

                    return f"SEMANTIC ERROR (PROJECT): Attribute {attr} does not exist"

        # Set attributes and preserve correct domains for projected columns
        tree.set_attributes(p_attrs)
        # Map domains from child attributes to projected columns
        projected_domains = []
        for attr in p_attrs:
            if attr in attrs:
                projected_domains.append(doms[attrs.index(attr)])
            elif '(' in attr and ')' in attr:
                # Aggregate functions: treat as INTEGER (or more precise if needed)
                projected_domains.append("INTEGER")
            else:
                # Fallback: treat as VARCHAR
                projected_domains.append("VARCHAR")
        tree.set_domains(projected_domains)
        return 'OK'

    if tree.get_node_type() == 'rename':
        status = semantic_checks(tree.get_left_child(), db)
        if status != 'OK':
            return status
        r_attrs = tree.get_columns()
        attrs = tree.get_left_child().get_attributes()
        doms = tree.get_left_child().get_domains()

        # Check for attribute length mismatch
        if len(r_attrs) != len(attrs):
            return "SEMANTIC ERROR (RENAME): " + str(r_attrs) + " and " + str(attrs) + " are of different sizes"

        # Check for duplicate attributes
        if len(list(set(r_attrs))) != len(r_attrs):
            return "SEMANTIC ERROR (RENAME): " + str(r_attrs) + " has duplicates!"

        # Set attributes and domains
        r_doms = doms[:]
        tree.set_attributes(r_attrs)
        tree.set_domains(doms)

        # Map original attributes to renamed ones for recognition in parent nodes
        renamed_attr_map = {attrs[i]: r_attrs[i] for i in range(len(attrs))}
        tree.set_join_columns(
            [renamed_attr_map.get(col, col)
             for col in tree.get_left_child().get_join_columns()]
        )

        return 'OK'

    if tree.get_node_type() in ['aggregate1', 'aggregate2', 'aggregate3']:
        status = semantic_checks(tree.get_left_child(), db)
        if status != 'OK':
            return status

        relation_attrs = tree.get_left_child().get_attributes()

        agg_project_list = tree.get_aggregate_project_list()
        agg_groupby_list = tree.get_aggregate_groupby_list() if tree.get_node_type() in [
            'aggregate2', 'aggregate3'] else []
        agg_having_condition = tree.get_aggregate_having_condition(
        ) if tree.get_node_type() == 'aggregate3' else []

        for attr in agg_project_list:
            if attr[0] == 'id':
                col_name = attr[1]
                if col_name not in relation_attrs:
                    return f"SEMANTIC ERROR (AGGREGATE): Column '{col_name}' does not exist in the relation."
                if tree.get_node_type() != 'aggregate1' and col_name not in agg_groupby_list:
                    return f"SEMANTIC ERROR (AGGREGATE): Column '{col_name}' must be in GROUP BY or used in an aggregate function."
            elif attr[0] == 'agg':
                func_name, col_name = attr[1]
                if col_name not in relation_attrs:
                    return f"SEMANTIC ERROR (AGGREGATE): Cannot apply '{func_name}' on non-existent column '{col_name}'."
                if func_name.upper() not in ['SUM', 'AVG', 'COUNT', 'MIN', 'MAX']:
                    return f"SEMANTIC ERROR (AGGREGATE): Unsupported aggregate function '{func_name}'."

        for group_attr in agg_groupby_list:
            if group_attr not in relation_attrs:
                return f"SEMANTIC ERROR (AGGREGATE): GROUP BY column '{group_attr}' does not exist."

        for condition in agg_having_condition:
            left_type, left_op = condition[0], condition[1]
            right_type, right_op = condition[3], condition[4]

            if left_type == 'id' and left_op not in relation_attrs:
                return f"SEMANTIC ERROR (AGGREGATE): HAVING condition references non-existent column '{left_op}'."
            if right_type == 'id' and right_op not in relation_attrs:
                return f"SEMANTIC ERROR (AGGREGATE): HAVING condition references non-existent column '{right_op}'."

        tree.set_attributes(
            [col[1] if col[0] == 'id' else f"{col[1][0]}({col[1][1]})" for col in agg_project_list])
        tree.set_domains(["INTEGER" for _ in tree.get_attributes()])

        # print("Tree after semantic checks:")
        # tree.print_tree(0)
        return 'OK'

    return 'OK'


# given the relational algebra expression tree, generate an equivalent
# sqlite3 query.


def generateSQL(tree, db):
    # print("Tree before generatesql")
    # tree.print_tree(0)
    if tree.get_node_type() == 'relation':
        query = f"SELECT * FROM {tree.get_relation_name()}"
        # print("Generated SQL Query (relation):", query)
        return query

    elif tree.get_node_type() == "union":
        left_is_aggregate = tree.get_left_child().get_node_type() in [
            'aggregate1', 'aggregate2', 'aggregate3']
        right_is_aggregate = tree.get_right_child().get_node_type() in [
            'aggregate1', 'aggregate2', 'aggregate3']

        lquery = generateSQL(tree.get_left_child(), db)
        rquery = generateSQL(tree.get_right_child(), db)

        if left_is_aggregate or right_is_aggregate:
            lquery = f"({lquery})"
            rquery = f"({rquery})"

        return f"{lquery} UNION {rquery}"

    elif tree.get_node_type() == "times":
        left_is_aggregate = tree.get_left_child().get_node_type() in [
            'aggregate1', 'aggregate2', 'aggregate3']
        right_is_aggregate = tree.get_right_child().get_node_type() in [
            'aggregate1', 'aggregate2', 'aggregate3']

        lquery = generateSQL(tree.get_left_child(), db)
        if tree.get_left_child().get_node_type() == "union":
            lquery = f"({lquery})"

        rquery = generateSQL(tree.get_right_child(), db)
        if tree.get_right_child().get_node_type() == "union":
            rquery = f"({rquery})"

        # Use unique aliases for each side, even if the same relation is used twice
        left_alias = tree.get_left_child().get_relation_name() + "_L"
        right_alias = tree.get_right_child().get_relation_name() + "_R"

        # Remove any dots from attribute names for SQL compatibility
        # Determine duplicates for suffixing
        left_attrs = tree.get_left_child().get_attributes()
        right_attrs = tree.get_right_child().get_attributes()
        duplicates = set(left_attrs) & set(right_attrs)
        select_cols = []
        for attr in left_attrs:
            if attr in duplicates:
                select_cols.append(f"{left_alias}.\"{attr}\" AS {attr}_L")
            else:
                select_cols.append(f"{left_alias}.\"{attr}\" AS {attr}")
        for attr in right_attrs:
            if attr in duplicates:
                select_cols.append(f"{right_alias}.\"{attr}\" AS {attr}_R")
            else:
                select_cols.append(f"{right_alias}.\"{attr}\" AS {attr}")
        select_clause = ", ".join(select_cols)

        query = f"SELECT {select_clause} FROM ({lquery}) {left_alias}, ({rquery}) {right_alias}"
        return query

    elif tree.get_node_type() == "project":
        lquery = generateSQL(tree.get_left_child(), db)
        query = "SELECT "

        # Check if we're projecting from a join that includes an aggregate
        left_child = tree.get_left_child()
        if left_child.get_node_type() == "join":
            left_grandchild = left_child.get_left_child()
            right_grandchild = left_child.get_right_child()
            left_has_aggregate = left_grandchild and left_grandchild.get_node_type() in [
                'aggregate1', 'aggregate2', 'aggregate3']
            right_has_aggregate = right_grandchild and right_grandchild.get_node_type() in [
                'aggregate1', 'aggregate2', 'aggregate3']

            if left_has_aggregate or right_has_aggregate:
                left_columns = left_grandchild.get_columns(
                ) if left_has_aggregate else left_grandchild.get_attributes()
                right_columns = right_grandchild.get_columns(
                ) if right_has_aggregate else right_grandchild.get_attributes()

                all_columns = {}
                for col in left_columns:
                    all_columns[col.upper()] = ("left", col)
                for col in right_columns:
                    all_columns[col.upper()] = ("right", col)

                for attr in tree.get_columns():
                    attr_upper = attr.upper()

                    if attr in left_columns:
                        query += f"{attr}, "
                    elif attr in right_columns:
                        query += f"{attr}, "
                    elif attr_upper in all_columns:
                        side, original_col = all_columns[attr_upper]
                        query += f"{original_col} AS {attr}, "
                    else:
                        query += f"{attr}, "

                query = query[:-2]
                query += f" FROM ({lquery})"
                return query

        for attr in tree.get_columns():
            query += f"{attr}, "

        query = query[:-2]
        query += f" FROM ({lquery})"

        non_aggregate_cols = [
            col for col in tree.get_columns() if '(' not in col]
        if non_aggregate_cols and not (tree.get_left_child().get_node_type() in ['aggregate1', 'aggregate2', 'aggregate3']):
            query += f" GROUP BY {', '.join(non_aggregate_cols)}"

        return query

    elif tree.get_node_type() == "rename":
        lquery = generateSQL(tree.get_left_child(), db)
        if tree.get_left_child().get_node_type() == "union":
            lquery = f"({lquery})"
        query = "SELECT "
        for i, attr in enumerate(tree.get_attributes()):
            query += f"{tree.get_left_child().get_attributes()[i]} AS {attr}, "
        query = query[:-2]
        query += f" FROM ({lquery}) {tree.get_left_child().get_relation_name()}"
        # print("Generated SQL Query (rename):", query)
        return query

    elif tree.get_node_type() == "select":
        lquery = generateSQL(tree.get_left_child(), db)
        left_is_aggregate = tree.get_left_child().get_node_type() in [
            'aggregate1', 'aggregate2', 'aggregate3']
        if tree.get_left_child().get_node_type() == "union" or left_is_aggregate:
            lquery = f"({lquery})"
        query = f"SELECT * FROM ({lquery}) {tree.get_left_child().get_relation_name()} WHERE "
        for condition in tree.get_conditions():
            c1 = condition[1]
            if condition[0] == 'str':
                c1 = f"'{c1}'"
            c4 = condition[4]
            if condition[3] == 'str':
                c4 = f"'{c4}'"
            if condition[2] == 'LIKE':
                query += f"{c1} LIKE {c4} AND "
            else:
                query += f"{c1} {condition[2]} {c4} AND "

        query = query[:-5]
        # print("Generated SQL Query (select):", query)
        return query

    elif tree.get_node_type() == "join":
        left_is_aggregate = tree.get_left_child().get_node_type() in [
            'aggregate1', 'aggregate2', 'aggregate3']
        right_is_aggregate = tree.get_right_child().get_node_type() in [
            'aggregate1', 'aggregate2', 'aggregate3']

        lquery = generateSQL(tree.get_left_child(), db)
        if tree.get_left_child().get_node_type() == "union" or left_is_aggregate:
            lquery = f"({lquery})"

        rquery = generateSQL(tree.get_right_child(), db)
        if tree.get_right_child().get_node_type() == "union" or right_is_aggregate:
            rquery = f"({rquery})"

        left_alias = tree.get_left_child().get_relation_name()
        right_alias = tree.get_right_child().get_relation_name()

        left_columns = tree.get_left_child().get_columns(
        ) if left_is_aggregate else tree.get_left_child().get_attributes()
        right_columns = tree.get_right_child().get_columns(
        ) if right_is_aggregate else tree.get_right_child().get_attributes()

        valid_join_conditions = []
        for join_col in tree.get_join_columns():
            left_has_col = join_col in left_columns
            right_has_col = join_col in right_columns

            if left_has_col and right_has_col:
                valid_join_conditions.append((join_col, join_col))

        if not valid_join_conditions or (left_is_aggregate and right_is_aggregate):
            query = "SELECT "
            join_columns_added = set()

            for col in left_columns:
                query += f"{left_alias}.{col} AS {col}, "
                join_columns_added.add(col)

            for col in right_columns:
                if col not in join_columns_added:
                    query += f"{right_alias}.{col} AS {col}, "

            if query.endswith(", "):
                query = query[:-2]

            query += f" FROM ({lquery}) {left_alias}, ({rquery}) {right_alias}"
            return query
        else:
            query = "SELECT "
            join_columns_added = set()

            for join_col, _ in valid_join_conditions:
                query += f"{left_alias}.{join_col} AS {join_col}, "
                join_columns_added.add(join_col)

            for col in left_columns:
                if col not in join_columns_added:
                    query += f"{left_alias}.{col} AS {col}, "

            for col in right_columns:
                if col not in join_columns_added and col not in tree.get_join_columns():
                    query += f"{right_alias}.{col} AS {col}, "

            if query.endswith(", "):
                query = query[:-2]

            query += f" FROM ({lquery}) {left_alias}, ({rquery}) {right_alias} WHERE "

            join_conditions = []
            for left_col, right_col in valid_join_conditions:
                join_conditions.append(
                    f"{left_alias}.{left_col} = {right_alias}.{right_col}")

            query += " AND ".join(join_conditions)
            return query

    elif tree.get_node_type() == "intersect":
        lquery = generateSQL(tree.get_left_child(), db)
        if tree.get_left_child().get_node_type() == "union":
            lquery = f"({lquery})"
        rquery = generateSQL(tree.get_right_child(), db)
        if tree.get_right_child().get_node_type() == "union":
            rquery = f"({rquery})"
        query = f"SELECT * FROM ({lquery}) {tree.get_left_child().get_relation_name()} WHERE ("
        for attr in tree.get_attributes():
            query += f"{attr}, "
        query = query[:-2] + ") IN "
        query += f"(SELECT * FROM ({rquery}) {tree.get_right_child().get_relation_name()})"
        # print("Generated SQL Query (intersect):", query)
        return query

    elif tree.get_node_type() == "aggregate1":
        lquery = generateSQL(tree.get_left_child(), db)
        query = "SELECT "

        for i, attr in enumerate(tree.get_aggregate_project_list()):
            if i < len(tree.get_columns()):
                if attr[0] == 'agg':
                    query += f"{attr[1][0]}({attr[1][1]}) AS {tree.get_columns()[i]}, "
                else:
                    query += f"{attr[1]} AS {tree.get_columns()[i]}, "

        query = query[:-2]
        query += f" FROM ({lquery})"

        # print("Generated SQL Query (aggregate1):", query)
        return query

    elif tree.get_node_type() == "aggregate2":
        lquery = generateSQL(tree.get_left_child(), db)
        query = "SELECT "

        for i, attr in enumerate(tree.get_aggregate_project_list()):
            if i < len(tree.get_columns()):
                if attr[0] == 'agg':
                    query += f"{attr[1][0]}({attr[1][1]}) AS {tree.get_columns()[i]}, "
                else:
                    query += f"{attr[1]} AS {tree.get_columns()[i]}, "

        query = query[:-2]
        query += f" FROM ({lquery})"

        groupby_list = tree.get_aggregate_groupby_list()
        if groupby_list:
            query += f" GROUP BY {', '.join(groupby_list)}"

        # print("Generated SQL Query (aggregate2):", query)
        return query

    elif tree.get_node_type() == "aggregate3":
        lquery = generateSQL(tree.get_left_child(), db)
        query = "SELECT "

        for i, attr in enumerate(tree.get_aggregate_project_list()):
            if i < len(tree.get_columns()):
                if attr[0] == 'agg':
                    query += f"{attr[1][0]}({attr[1][1]}) AS {tree.get_columns()[i]}, "
                else:
                    query += f"{attr[1]} AS {tree.get_columns()[i]}, "

        query = query[:-2]
        query += f" FROM ({lquery})"

        groupby_list = tree.get_aggregate_groupby_list()
        if groupby_list:
            query += f" GROUP BY {', '.join(groupby_list)}"

        having_conditions = tree.get_aggregate_having_condition()
        if having_conditions:
            query += " HAVING "
            for condition in having_conditions:
                c1 = condition[1]
                if condition[0] == 'agg':
                    c1 = f"{condition[1][0]}({condition[1][1]})"
                elif condition[0] == 'str':
                    c1 = f"'{c1}'"
                c4 = condition[4]
                if condition[3] == 'agg':
                    c4 = f"{condition[4][0]}({condition[4][1]})"
                elif condition[3] == 'str':
                    c4 = f"'{c4}'"
                if condition[2] == 'LIKE':
                    query += f"{c1} LIKE {c4} AND "
                else:
                    query += f"{c1} {condition[2]} {c4} AND "
            query = query[:-5]
        return query

    else:
        lquery = generateSQL(tree.get_left_child(), db)
        if tree.get_left_child().get_node_type() == "union":
            lquery = f"({lquery})"
        rquery = generateSQL(tree.get_right_child(), db)
        if tree.get_right_child().get_node_type() == "union":
            rquery = f"({rquery})"
        query = f"SELECT * FROM ({lquery}) {tree.get_left_child().get_relation_name()} WHERE ("
        for attr in tree.get_attributes():
            query += f"{attr}, "
        query = query[:-2] + ") NOT IN "
        query += f"(SELECT * FROM ({rquery}) {tree.get_right_child().get_relation_name()})"
        # print("Generated SQL Query (else):", query)
        return query


# ------------------------ Dash app Functions -------------------------------
def tree_to_json(node, db, node_counter=[0]):
    if node is None:
        return None

    relation_name = node.get_relation_name() if node.get_relation_name() else "UNKNOWN"
    node_id = f"node_{node_counter[0]}"
    node_counter[0] += 1

    node_json = {
        'node_id': node_id,
        'node_type': node.get_node_type(),
        'relation_name': relation_name,
        'left_child': tree_to_json(node.get_left_child(), db, node_counter),
        'right_child': tree_to_json(node.get_right_child(), db, node_counter),
        'attributes': node.get_attributes()
    }

    if node.get_node_type() == 'project':
        node_json['columns'] = node.get_columns()
    elif node.get_node_type() == 'rename':
        node_json['new_columns'] = node.get_columns()
    elif node.get_node_type() == 'select':
        node_json['conditions'] = node.get_conditions()
    elif node.get_node_type() == 'join':
        node_json['join_columns'] = node.get_join_columns()
        node_json['attributes'] = node.get_attributes()
    elif node.get_node_type() == 'times':
        # For times, show the explicit column names as in the backend
        node_json['columns'] = node.get_attributes(
        ) if node.get_attributes() else []

    if node.get_node_type() in ['aggregate1', 'aggregate2', 'aggregate3']:
        node_json['aggregate_project_list'] = node.get_aggregate_project_list()
        node_json['aggregate_groupby_list'] = node.get_aggregate_groupby_list()
        node_json['aggregate_having_condition'] = node.get_aggregate_having_condition()
        node_json['columns'] = node.get_columns()  # Include renamed columns

    return node_json


def generate_tree_from_query(query, db, node_counter=[0]):
    try:
        tree = rap_parser.parse(query)

        set_temp_table_names(tree)

        validation_msg = semantic_checks(tree, db)
        if validation_msg != 'OK':
            return {'error': f"Semantic check failed: {validation_msg}"}

        # print("Generated Tree Structure:")
        # tree.print_tree(0)

        json_tree = tree_to_json(tree, db, node_counter)

        return json_tree
    except Exception as e:
        return {'error': str(e)}


# Recursively traverse the JSON tree to find the node with the given node_id.
def get_node_by_id(json_tree, node_id):
    if json_tree is None:
        return None

    if json_tree.get('node_id') == node_id:
        return json_tree

    left_result = get_node_by_id(json_tree.get('left_child'), node_id)
    if left_result:
        return left_result

    right_result = get_node_by_id(json_tree.get('right_child'), node_id)
    return right_result


# Reconstruct a Node object from a JSON representation.
def json_to_node(json_node):
    if json_node is None:
        return None

    node = Node(json_node['node_type'],
                json_to_node(json_node.get('left_child')),
                json_to_node(json_node.get('right_child')))

    if node.get_node_type() == 'rename':
        if 'new_columns' in json_node:
            new_cols = json_node['new_columns']
            node.set_columns(new_cols)
            node.set_relation_name(new_cols[0])

    node.set_relation_name(json_node.get('relation_name'))
    node.set_attributes(json_node.get('attributes'))

    if 'columns' in json_node:
        node.set_columns(json_node['columns'])

    if 'conditions' in json_node:
        node.set_conditions(json_node['conditions'])
    if 'join_columns' in json_node:
        node.set_join_columns(json_node.get('join_columns', []))

    if node.get_node_type() in ['aggregate1', 'aggregate2', 'aggregate3']:
        node.set_aggregate_project_list(
            json_node.get('aggregate_project_list', []))
        node.set_aggregate_groupby_list(
            json_node.get('aggregate_groupby_list', []))
        node.set_aggregate_having_condition(
            json_node.get('aggregate_having_condition', []))
        if 'columns' in json_node:
            node.set_columns(json_node['columns'])

    return node


def get_node_info_from_db(node_id, json_tree, db):
    try:
        node_json = get_node_by_id(json_tree, node_id)

        if node_json is None:
            return {'error': 'Node not found in the tree.'}

        node = json_to_node(node_json)
        query = generateSQL(node, db)

        c = db.conn.cursor()
        c.execute(query)
        records = c.fetchall()

        sql_columns = [desc[0] for desc in c.description]

        if node.get_columns():
            columns = node.get_columns()
        else:
            columns = sql_columns

        return {'columns': columns, 'rows': records}

    except Exception as e:
        return {'error': f"Error: {str(e)}"}


def fetch_schema_info(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        schema_info = {}
        for table_name in tables:
            table_name = table_name[0].upper()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            schema_info[table_name] = []
            for col in columns:
                base_type = col[2].split('(')[0].upper()
                schema_info[table_name].append({
                    'attribute': col[1].upper(),
                    'domain': base_type
                })

        conn.close()
        return schema_info

    except sqlite3.Error as e:
        return f"Error retrieving schema: {str(e)}"


# ---------------------- Main  ----------------------
def main():
    db = SQLite3()
    db.open(sys.argv[1])

    while True:
        data = read_input()
        if data == 'schema;':
            db.displayDatabaseSchema()
            continue
        if data.strip().split()[0] == "source":
            filename = data.strip().split()[1][:-1]
            execute_file(filename, db)
            continue
        if data == 'help;' or data == "h;":
            print("\nschema; 		# to see schema")
            print("source filename; 	# to run query in file")
            print("query terminated with ;	# to run query")
            print("exit; or quit; or q; 	# to exit\n")
            continue
        if data == 'exit;' or data == "quit;" or data == "q;":
            break
        try:
            tree = rap_parser.parse(data)
        except Exception as inst:
            print(inst.args[0])
            continue
        # print("********************************")
        # tree.print_tree(0)
        # print("********************************")
        set_temp_table_names(tree)
        msg = semantic_checks(tree, db)
        # print("********************************")
        # tree.print_tree(0)
        # print("********************************")
        if msg == 'OK':
            # print('Passed semantic checks')
            query = generateSQL(tree, db)
            db.displayQueryResults(query, tree)
        else:
            print(msg)
    db.close()


if __name__ == '__main__':
    main()
