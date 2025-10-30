from DRCParser import DRCParser
from SQLite3 import SQLite3


def semantic_checks(tree, db):
    # initialize global-like variables
    argdetail = []
    finalfree_variable_max_conj = []
    finallimited_variable = []
    free_variable_max_conj_recursion = []
    limited_variable_recursion = []
    comp_variable = []
    flag = 0
    count_not = 0
    not_operator = 0
    not_operator_lc = 0

    # perform checks
    result = semantic_check(tree, db, argdetail)
    if result != "OK":
        return result

    result = max_conj_and_check(tree, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
    if result != "OK":
        return result

    result = check_not(tree, flag, count_not)
    if result != "OK":
        return result

    return "OK"


def semantic_check(tree, db, argdetail):
    if tree is None:
        return "OK"

    node_type = tree.get('type')

    if node_type in ('comp', 'predicate'):
        # leaf nodes
        if node_type == 'comp':
            free_variable = []
            left_val = tree['left']
            left_type = tree['left_type']
            right_val = tree['right']
            right_type = tree['right_type']

            if left_type == 'col':
                ind = find_arg_index(argdetail, left_val.upper())
                if ind == -1:
                    return f"argument {left_val} not found"
                ind_columntype = ind + 2
                lcol_data_type = argdetail[ind_columntype] if ind_columntype < len(argdetail) else None
                if lcol_data_type is None:
                    return f"argument {left_val} not found"

                if right_type == 'col':
                    free_variable.append(left_val)
                    free_variable.append(right_val)
                    ind = find_arg_index(argdetail, right_val.upper())
                    if ind == -1:
                        return f"argument {right_val} not found"
                    ind_columntype = ind + 2
                    rcol_data_type = argdetail[ind_columntype] if ind_columntype < len(argdetail) else None
                    if rcol_data_type is None:
                        return f"argument {right_val} not found"
                    if lcol_data_type.upper() == "VARCHAR":
                        if rcol_data_type.upper() != "VARCHAR":
                            return f"mismatch types: {left_val} and {right_val}"
                    else:
                        if rcol_data_type.upper() == "VARCHAR":
                            return f"mismatch types: {left_val} and {right_val}"
                else:
                    # left col, right str or num
                    free_variable.append(left_val)
                    if (lcol_data_type.upper() == "VARCHAR" and right_type == "num") or \
                       (lcol_data_type.upper() == "DECIMAL" and right_type == "str") or \
                       (lcol_data_type.upper() == "INTEGER" and right_type == "str"):
                        return f"mismatch types: {left_val} and {right_val}"
            tree['free_var_list'] = free_variable
            return "OK"

        elif node_type == 'predicate':
            free_variable = []
            rname = tree['name'].upper()
            if not db.relationExists(rname):
                return f"relation {rname} does not exist"
            atts = db.getAttributes(rname)
            doms = db.getDomains(rname)
            attrsize = len(atts)
            arguments = tree['args']
            arg_size = len(arguments)
            if attrsize != arg_size:
                return f"relation {rname} does not have same number of columns in query as in database"
            for i in range(len(atts)):
                domaintype = doms[i].upper()
                val, datatype = arguments[i]
                attrname = atts[i]
                if datatype in ('num', 'str'):
                    if (domaintype == "INTEGER" and datatype == "str") or \
                       (domaintype == "DECIMAL" and datatype == "str") or \
                       (domaintype == "VARCHAR" and datatype == "num"):
                        return f"mismatch types in ({i+1}) argument of relation: {rname} required type: {domaintype} available type: {datatype}"
                else:
                    free_variable.append(val)
                argdetail.append(val.upper())
                argdetail.append(attrname)
                argdetail.append(domaintype)
            tree['free_var_list'] = free_variable
            return "OK"

    elif node_type in ('exists', 'forall'):
        free_variable = []
        free_variable_child = []
        bound_variable = tree['varlist']
        child = tree['child']

        # check for multiple same bound variables
        seen = set()
        for var in bound_variable:
            if var.upper() in seen:
                return f"multiple bound variables with same name in forall or exists ({var})"
            seen.add(var.upper())

        result = semantic_check(child, db, argdetail)
        if result != "OK":
            return result

        free_variable_child = child.get('free_var_list', [])
        for var in free_variable_child:
            if var not in bound_variable:
                free_variable.append(var)
        tree['free_var_list'] = free_variable
        return "OK"

    elif node_type == 'not':
        free_variable = []
        child = tree['child']
        result = semantic_check(child, db, argdetail)
        if result != "OK":
            return result
        free_variable = child.get('free_var_list', [])
        tree['free_var_list'] = free_variable
        return "OK"

    elif node_type == 'query':
        child = tree['child']
        free_var_query = tree['varlist']
        result = semantic_check(child, db, argdetail)
        if result != "OK":
            return result
        free_var = child.get('free_var_list', [])
        if len(free_var) != len(free_var_query):
            return f"the free variables before '|' in query {free_var_query} should be same as free variable after '|' in query {free_var}"
        for var in free_var:
            if var not in free_var_query:
                return f"the free variables before '|' in query {free_var_query} should be same as free variable after '|' in query {free_var}"
        return "OK"

    elif node_type in ('and', 'or'):
        free_variable = []
        free_variable_lc = []
        free_variable_rc = []
        left = tree['left']
        right = tree['right']

        result1 = semantic_check(left, db, argdetail)
        result2 = semantic_check(right, db, argdetail)
        if result1 != "OK":
            return result1
        if result2 != "OK":
            return result2

        free_variable_lc = left.get('free_var_list', [])
        free_variable_rc = right.get('free_var_list', [])

        if node_type == 'and':
            for var in free_variable_lc:
                free_variable.append(var)
            for var in free_variable_rc:
                if var not in free_variable_lc:
                    free_variable.append(var)
            tree['free_var_list'] = free_variable
            return "OK"
        else:  # or
            if len(free_variable_lc) != len(free_variable_rc):
                return f"formulas connected with 'or' does not have same free variables: left formula free variables are {free_variable_lc} and right formula free variables are {free_variable_rc}"
            for i in range(len(free_variable_lc)):
                if free_variable_lc[i] != free_variable_rc[i]:
                    return f"formulas connected with 'or' does not have same free variables: left formula free variables are {free_variable_lc} and right formula free variables are {free_variable_rc}"
            tree['free_var_list'] = free_variable_lc
            return "OK"

    return "OK"


def find_arg_index(argdetail, name):
    for i in range(0, len(argdetail), 3):
        if argdetail[i] == name:
            return i
    return -1


def max_conj_and_check(tree, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable):
    if tree is None:
        return "OK"

    node_type = tree.get('type')

    if node_type in ('comp', 'predicate'):
        if node_type == 'comp':
            free_variable_max_conj = []
            limited_variable = []
            left_val = tree['left']
            left_type = tree['left_type']
            right_val = tree['right']
            right_type = tree['right_type']
            if left_type == 'col':
                if right_type == 'col':
                    free_variable_max_conj.append(left_val)
                    free_variable_max_conj.append(right_val)
                    limited_variable = None
                    comp_variable.append(left_val)
                    comp_variable.append(right_val)
                else:
                    free_variable_max_conj.append(left_val)
                    limited_variable.append(left_val)
            tree['free_var_list_max_conj'] = free_variable_max_conj
            tree['limited_var_list'] = limited_variable
            return "OK"
        elif node_type == 'predicate':
            free_variable_max_conj = []
            arguments = tree['args']
            for val, datatype in arguments:
                if datatype == 'col':
                    free_variable_max_conj.append(val)
            tree['free_var_list_max_conj'] = free_variable_max_conj
            tree['limited_var_list'] = free_variable_max_conj
            return "OK"

    elif node_type == 'not':
        limited_variable = []
        child = tree['child']
        result = max_conj_and_check(child, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
        if result != "OK":
            return result
        if child.get('type') == 'predicate':
            tree['free_var_list_max_conj'] = child.get('free_var_list_max_conj', [])
            limited_variable = None
            tree['limited_var_list'] = limited_variable
        elif child.get('type') == 'exists':
            bound_variable = child.get('varlist', [])
            lc_child = child['child']
            result = max_conj_and_check(lc_child, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
            if result != "OK":
                return result
            free_var = lc_child.get('free_var_list', [])
            ltd_var = lc_child.get('limited_var_list', [])
            new_free_var = []
            for var in free_var:
                if var in bound_variable:
                    if ltd_var is not None:
                        if var not in ltd_var:
                            if ltd_var is None:
                                ltd_var = [var]
                            else:
                                ltd_var.append(var)
                    else:
                        ltd_var = [var]
                else:
                    new_free_var.append(var)
            for var in new_free_var:
                if var in ltd_var:
                    if ltd_var is not None:
                        ltd_var.remove(var)
            tree['free_var_list_max_conj'] = new_free_var
            tree['limited_var_list'] = ltd_var
        else:
            tree['free_var_list_max_conj'] = child.get('free_var_list_max_conj', [])
            tree['limited_var_list'] = child.get('limited_var_list', [])
        return "OK"

    elif node_type == 'exists':
        bound_variable = tree.get('varlist', [])
        limited_variable = []
        child = tree['child']
        result = max_conj_and_check(child, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
        if result != "OK":
            return result
        bound_variable = tree.get('varlist', [])
        free_var_child = child.get('free_var_list', [])
        ltd_var_child = child.get('limited_var_list', [])
        for var in free_var_child:
            if var in bound_variable:
                if ltd_var_child is not None:
                    if var not in ltd_var_child:
                        if ltd_var_child is None:
                            ltd_var_child = [var]
                        else:
                            ltd_var_child.append(var)
                else:
                    ltd_var_child = [var]
        tree['free_var_list_max_conj'] = free_var_child
        tree['limited_var_list'] = ltd_var_child
        return "OK"

    elif node_type == 'query':
        child = tree['child']
        result = max_conj_and_check(child, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
        if result != "OK":
            return result
        tree['free_var_list_max_conj'] = child.get('free_var_list_max_conj', [])
        tree['limited_var_list'] = child.get('limited_var_list', [])
        return "OK"

    elif node_type == 'or':
        left = tree['left']
        right = tree['right']
        free_variable_max_conj = []
        limited_variable = []
        result1 = max_conj_and_check(left, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
        result2 = max_conj_and_check(right, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
        if result1 != "OK":
            return result1
        if result2 != "OK":
            return result2
        return "OK"

    elif node_type == 'and':
        free_variable_max_conj = []
        limited_variable = []
        left = tree['left']
        right = tree['right']

        if right.get('type') == 'and':
            # collect from left
            result = max_conj_and_check(left, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
            if result != "OK":
                return result
            free_variable_max_conj = left.get('free_var_list_max_conj', [])
            limited_variable = left.get('limited_var_list', [])
            for var in free_variable_max_conj:
                if var not in finalfree_variable_max_conj:
                    finalfree_variable_max_conj.append(var)
            if limited_variable is not None:
                for var in limited_variable:
                    if var not in finallimited_variable:
                        finallimited_variable.append(var)
            # recurse on right
            result = max_conj_and_check(right, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
            if result != "OK":
                return result
        else:
            # right is not 'and'
            if right.get('type') in ('not', 'or', 'exists'):
                rc_child = right['child'] if right.get('type') in ('not', 'exists') else None
                if rc_child:
                    result = max_conj_and_check(rc_child, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
                    if result != "OK":
                        return result
                result1 = max_conj_and_check(left, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
                if result1 != "OK":
                    return result1
                free_variable_max_conj_lc = left.get('free_var_list_max_conj', [])
                limited_variable_lc = left.get('limited_var_list', [])
                for var in free_variable_max_conj_lc:
                    if var not in finalfree_variable_max_conj:
                        finalfree_variable_max_conj.append(var)
                if limited_variable_lc is not None:
                    for var in limited_variable_lc:
                        if var not in finallimited_variable:
                            finallimited_variable.append(var)
                # store recursion
                for var in finalfree_variable_max_conj:
                    if var not in free_variable_max_conj_recursion:
                        free_variable_max_conj_recursion.append(var)
                if finallimited_variable is not None:
                    for var in finallimited_variable:
                        if var not in limited_variable_recursion:
                            limited_variable_recursion.append(var)
                # reset
                finalfree_variable_max_conj.clear()
                finallimited_variable.clear()
                # handle specific cases
                if right.get('type') in ('not', 'exists'):
                    lc_not_or_exists = right['child']
                    if lc_not_or_exists.get('type') in ('comp', 'predicate'):
                        result = max_conj_and_check(lc_not_or_exists, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
                        free_variable_max_conj_rc = lc_not_or_exists.get('free_var_list_max_conj', [])
                        limited_variable_rc = None if right.get('type') == 'not' else lc_not_or_exists.get('limited_var_list', [])
                    else:
                        result2 = max_conj_and_check(right, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
                        if result2 != "OK":
                            return result2
                        free_variable_max_conj_rc = right.get('free_var_list_max_conj', [])
                        limited_variable_rc = right.get('limited_var_list', [])
                        for var in free_variable_max_conj_rc:
                            if var not in finalfree_variable_max_conj:
                                finalfree_variable_max_conj.append(var)
                        if limited_variable_rc is not None:
                            for var in limited_variable_rc:
                                if var not in finallimited_variable:
                                    finallimited_variable.append(var)
                        for var in finalfree_variable_max_conj:
                            if var not in free_variable_max_conj_rc:
                                free_variable_max_conj_rc.append(var)
                        if limited_variable_rc is not None:
                            for var in finallimited_variable:
                                if var not in limited_variable_rc:
                                    limited_variable_rc.append(var)
                        for var in free_variable_max_conj_recursion:
                            if var not in finalfree_variable_max_conj:
                                finalfree_variable_max_conj.append(var)
                        if limited_variable_recursion is not None:
                            for var in limited_variable_recursion:
                                if var not in finallimited_variable:
                                    finallimited_variable.append(var)
                elif right.get('type') == 'or':
                    result2 = max_conj_and_check(right, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
                    if result2 != "OK":
                        return result2
                    free_variable_max_conj_rc = right.get('free_var_list_max_conj', [])
                    limited_variable_rc = right.get('limited_var_list', [])
                    for var in free_variable_max_conj_rc:
                        if var not in finalfree_variable_max_conj:
                            finalfree_variable_max_conj.append(var)
                    if limited_variable_rc is not None:
                        for var in limited_variable_rc:
                            if var not in finallimited_variable:
                                finallimited_variable.append(var)
                    for var in finalfree_variable_max_conj:
                        if var not in free_variable_max_conj_rc:
                            free_variable_max_conj_rc.append(var)
                    if limited_variable_rc is not None:
                        for var in finallimited_variable:
                            if var not in limited_variable_rc:
                                limited_variable_rc.append(var)
                    for var in free_variable_max_conj_recursion:
                        if var not in finalfree_variable_max_conj:
                            finalfree_variable_max_conj.append(var)
                    if limited_variable_recursion is not None:
                        for var in limited_variable_recursion:
                            if var not in finallimited_variable:
                                finallimited_variable.append(var)
            elif right.get('type') in ('comp', 'predicate'):
                result1 = max_conj_and_check(left, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
                result2 = max_conj_and_check(right, db, finalfree_variable_max_conj, finallimited_variable, free_variable_max_conj_recursion, limited_variable_recursion, comp_variable)
                if result1 != "OK":
                    return result1
                if result2 != "OK":
                    return result2
                free_variable_max_conj_lc = left.get('free_var_list_max_conj', [])
                limited_variable_lc = left.get('limited_var_list', [])
                free_variable_max_conj_rc = right.get('free_var_list_max_conj', [])
                limited_variable_rc = right.get('limited_var_list', [])
                for var in free_variable_max_conj_lc:
                    if var not in finalfree_variable_max_conj:
                        finalfree_variable_max_conj.append(var)
                if limited_variable_lc is not None:
                    for var in limited_variable_lc:
                        if var not in finallimited_variable:
                            finallimited_variable.append(var)
                for var in free_variable_max_conj_rc:
                    if var not in finalfree_variable_max_conj:
                        finalfree_variable_max_conj.append(var)
                if limited_variable_rc is not None:
                    for var in limited_variable_rc:
                        if var not in finallimited_variable:
                            finallimited_variable.append(var)
                # handle comp_variable
                for i in range(0, len(comp_variable), 2):
                    if comp_variable[i] in finallimited_variable:
                        if comp_variable[i+1] not in finallimited_variable:
                            finallimited_variable.append(comp_variable[i+1])
                    elif comp_variable[i+1] in finallimited_variable:
                        if comp_variable[i] not in finallimited_variable:
                            finallimited_variable.append(comp_variable[i])
                not_limited_var = []
                for var in finalfree_variable_max_conj:
                    if var not in finallimited_variable:
                        not_limited_var.append(var)
                if not_limited_var:
                    return f"the free variable {not_limited_var} is not limited hence violating rule # 3 of safe drc formula"
                tree['limited_var_list'] = finallimited_variable
    return "OK"


def check_not(tree, flag, count_not):
    if tree is None:
        return "OK"

    node_type = tree.get('type')

    if node_type in ('comp', 'predicate'):
        return "OK"

    elif node_type == 'not':
        return "rule # 4 of safe drc formula is violated: a 'not' operator can only be applied to a formula if it is connected to a non negated formula with an 'and'"

    elif node_type in ('exists', 'forall', 'query'):
        child = tree['child']
        result = check_not(child, flag, count_not)
        if result != "OK":
            return result
        return "OK"

    elif node_type == 'or':
        left = tree['left']
        right = tree['right']
        if left.get('type') == 'not' or right.get('type') == 'not':
            return "rule # 4 of safe drc formula is violated: a 'not' operator can only be applied to a formula if it is connected to a non negated formula with an 'and'"
        result1 = check_not(left, flag, count_not)
        if result1 != "OK":
            return result1
        result2 = check_not(right, flag, count_not)
        if result2 != "OK":
            return result2
        return "OK"

    elif node_type == 'and':
        left = tree['left']
        right = tree['right']
        if left.get('type') == 'not':
            count_not += 1
        else:
            flag = 1
        if right.get('type') == 'and':
            result = check_not(right, flag, count_not)
            if result != "OK":
                return result
        else:
            if right.get('type') == 'not':
                if flag == 1:
                    lc_not = right['child']
                    flag = 0
                    count_not = 0
                    result = check_not(lc_not, flag, count_not)
                    if result != "OK":
                        return result
                else:
                    return "rule # 4 of safe drc formula is violated: a 'not' operator can only be applied to a formula if it is connected to a non negated formula with an 'and'"
            else:
                flag = 1
                if count_not != 0 and flag == 0:
                    return "rule # 4 of safe drc formula is violated: a 'not' operator can only be applied to a formula if it is connected to a non negated formula with an 'and'"
                else:
                    flag = 0
                    count_not = 0
                    result = check_not(right, flag, count_not)
                    if result != "OK":
                        return result
    return "OK"


def test_semantic_checks():
    parser = DRCParser()
    sample = "{A | actors(A) and not exists[M](acts(M,A) and not movies(M,'Kurosawa'))}"

    # this one should fail because it doesnt have exists or foreall binding M so it is a free variable like A
    # sample = "{A | actors(A) and not acts(M,A) and not movies(M,'Kurosawa')}"
    # including M allows it to pass the semantic checks
    #sample = "{A, M | actors(A) and not acts(M,A) and not movies(M,'Kurosawa')}"

    # sample = "{A | actors(A) and forall[M](acts(M, A) -> movies(M, 'Kurosawa'))}"

    print("parsing:", sample)
    tree = parser.parse(sample)
    print("parsed tree:")
    import pprint
    pprint.pprint(tree)

    db = SQLite3()
    db.open('/Users/linn/Documents/FormalViz/databases/movies2.db')
    result = semantic_checks(tree, db)
    print("semantic check result:", result)
    db.close()


if __name__ == "__main__":
    test_semantic_checks()
