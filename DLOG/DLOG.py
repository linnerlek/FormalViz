import sys
from DLOG.DLOGParser import DLOGParser
from DLOG.SQLite3 import *

dlog_parser = DLOGParser()


def read_input():
    result = ''
    while True:
        data = input('DLOG: ').strip()
        if ';' in data:
            i = data.index(';')
            result += data[0:i+1]
            break
        else:
            result += data + ' '
    return result.strip()


def rename_vars_in_body(d, body):
    result = []
    for lit in body:
        new_args = []
        if lit[1][0] == 'regular':
            for arg in lit[1][2]:
                if arg[0] == 'var' and arg[1] in d:
                    new_args.append(('var', d[arg[1]]))
                else:
                    new_args.append(arg)
            newlit = (lit[0], ('regular', lit[1][1], new_args))
            result.append(newlit)
        else:  # must be comparison literal
            lop = lit[1][1]
            if lit[1][1][0] == 'var' and lit[1][1][1] in d:
                lop = ('var', d[lit[1][1][1]])
            rop = lit[1][3]
            if lit[1][3][0] == 'var' and lit[1][3][1] in d:
                rop = ('var', d[lit[1][3][1]])
            result.append((lit[0], ('comparison', lop, lit[1][2], rop)))
    return result


def construct_data_structure(rules):
    result = {}
    for (head, body) in rules:
        if head[1] in result:
            d = {v[0][1]: v[1][1] for v in zip(head[2], result[head[1]][0])}
            new_body = rename_vars_in_body(d, body)
            result[head[1]] = (result[head[1]][0],
                               result[head[1]][1]+[new_body])
        else:
            result[head[1]] = (head[2], [body])
    return result


def construct_dependency_graph(predicates):
    result = {}
    for pred in predicates:
        if pred not in result:
            result[pred] = []
        for body in predicates[pred][1]:
            for p in body:
                if p[1][0] == 'regular' and p[1][1] not in result[pred]:
                    result[pred].append(p[1][1])
    return result


def construct_ordered_predicates(all_preds, dgraph):
    print("inside construct_ordered_predicates")
    # since no recursion, we will simply +1 to head predicate
    strata = {p: 0 for p in all_preds}
    while True:
        unchanged = True
        for p in dgraph:
            max_body = max([strata[q] for q in dgraph[p]])
            if strata[p] <= max_body:
                strata[p] = 1+max_body
                unchanged = False
        if unchanged:
            break
    max_strata = max([strata[p] for p in strata])
    print("max_strata", max_strata)
    print("strata", strata)
    strata_inv = {i: [] for i in range(max_strata+1)}
    for p in strata:
        strata_inv[strata[p]].append(p)
    print(strata_inv)
    result = []
    for i in range(1, 1+max_strata):
        result = result + strata_inv[i]
        print(result)
    print("result", result)
    return result


def all_predicates(dgraph):
    result = set([p for p in dgraph])
    for p in dgraph:
        result = result.union(dgraph[p])
    return result


def semantic_checks(db, pred_dict):
    # IDB predicates, appear in head of rules
    idb_preds = set(pred_dict.keys())
    edb_preds = set()                  # EDB predicates, only in bodies not heads
    all_body_preds = set()
    idb_arities = {}
    edb_arities = {}

    # Collect all predicates in bodies and their arities
    for head, (args, bodies) in pred_dict.items():
        idb_arities.setdefault(head, len(args))
        for body in bodies:
            for lit in body:
                if lit[1][0] == 'regular':
                    pred = lit[1][1]
                    all_body_preds.add(pred)
                    if pred not in idb_preds:
                        edb_preds.add(pred)
                        if pred not in edb_arities:
                            edb_arities[pred] = len(lit[1][2])

    # IDB and EDB predicates are disjoint
    if idb_preds & edb_preds:
        return f"SEMANTIC ERROR: IDB and EDB predicates overlap: {idb_preds & edb_preds}"

    # debug
    # print("IDB predicates:", idb_preds)
    # print("All body predicates:", all_body_preds)

    # All predicates in body are IDB or DB tables
    for pred in all_body_preds:
        if pred not in idb_preds and not db.relationExists(pred):
            return f"SEMANTIC ERROR: Predicate '{pred}' in rule body is not IDB or DB table"

    # Arity of EDB predicates matches DB table columns
    for pred in edb_preds:
        if db.relationExists(pred):
            db_arity = len(db.getAttributes(pred))
            if edb_arities[pred] != db_arity:
                return f"SEMANTIC ERROR: Arity mismatch for EDB predicate '{pred}': rule has {edb_arities[pred]}, DB has {db_arity}"
        else:
            return f"SEMANTIC ERROR: EDB predicate '{pred}' not found in DB"

    # IDB predicates with multiple rules have same arity
    for pred, (args, bodies) in pred_dict.items():
        for body in bodies:
            if len(args) != idb_arities[pred]:
                return f"SEMANTIC ERROR: IDB predicate '{pred}' has inconsistent arity"

    # Type checks
    for head, (args, bodies) in pred_dict.items():
        for body in bodies:
            var_types = {}
            for lit in body:
                if lit[1][0] == 'regular':
                    pred = lit[1][1]
                    terms = lit[1][2]
                    if db.relationExists(pred):
                        col_types = [t.upper() for t in db.getDomains(pred)]
                        for i, term in enumerate(terms):
                            if term[0] == 'const':
                                val = term[1]
                                db_type = col_types[i]
                                # Constant type matches DB column type
                                if db_type == "INTEGER" and not isinstance(val, int):
                                    return f"SEMANTIC ERROR: Constant '{val}' does not match INTEGER in '{pred}'"
                                if db_type == "TEXT" and not isinstance(val, str):
                                    return f"SEMANTIC ERROR: Constant '{val}' does not match TEXT in '{pred}'"
                            elif term[0] == 'var' and term[1] != '_':
                                # Repeating variable types are the same within a rule
                                if term[1] in var_types:
                                    if var_types[term[1]] != col_types[i]:
                                        return f"SEMANTIC ERROR: Variable '{term[1]}' has inconsistent types in rule"
                                else:
                                    var_types[term[1]] = col_types[i]
                elif lit[1][0] == 'comparison':
                    lop, op, rop = lit[1][1], lit[1][2], lit[1][3]
                    for side in [lop, rop]:
                        if side[0] == 'const':
                            val = side[1]
                            # Constant types in comparisons are valid
                            if not isinstance(val, (int, float, str)):
                                return f"SEMANTIC ERROR: Invalid constant '{val}' in comparison"
    return "OK"


def format_sql_value(arg):
    if arg[0] == 'num':
        return str(arg[1])
    if arg[0] == 'str':
        return f"'{arg[1]}'"
    if arg[0] == 'var':
        return arg[1]
    return str(arg[1])


def generate_sql(pred, pred_dict, db=None, rules=None, specific_args=None):
    if db is None:
        raise Exception("Database handle (db) required for SQL generation.")

    if pred not in pred_dict:
        if not db.relationExists(pred):
            raise Exception(f"EDB predicate '{pred}' not found in database.")

        col_names = db.getAttributes(pred)

        target_args = specific_args
        if not target_args and rules:
            for rule in rules:
                _, body = rule
                for lit in body:
                    if lit[1][0] == 'regular' and lit[1][1] == pred:
                        target_args = lit[1][2]
                        break
                if target_args:
                    break

        if not target_args:
            return f"SELECT {', '.join(col_names)} FROM {pred}"

        select_parts = []
        filter_conditions = []

        for idx, arg in enumerate(target_args):
            if idx < len(col_names):
                col_name = col_names[idx]
                if arg[0] == 'var' and arg[1] and arg[1] != '_':
                    select_parts.append(f"{col_name} AS {arg[1]}")
                elif arg[0] in ('num', 'str'):
                    select_parts.append(col_name)
                    filter_conditions.append(
                        f"{col_name} = {format_sql_value(arg)}")

        if not select_parts:
            select_parts = col_names

        if rules and target_args:
            for rule in rules:
                _, body = rule
                target_literal = None
                for lit in body:
                    if (lit[1][0] == 'regular' and lit[1][1] == pred and
                            len(lit[1][2]) == len(target_args)):
                        args_match = True
                        for i, (target_arg, lit_arg) in enumerate(zip(target_args, lit[1][2])):
                            if (target_arg[0] == 'var' and target_arg[1] != '_' and
                                lit_arg[0] == 'var' and lit_arg[1] != '_' and
                                    target_arg[1] != lit_arg[1]):
                                args_match = False
                                break
                            elif (target_arg[0] in ('num', 'str') and
                                  (lit_arg[0] != target_arg[0] or lit_arg[1] != target_arg[1])):
                                args_match = False
                                break
                            elif target_arg[0] == 'var' and target_arg[1] == '_' and lit_arg[0] == 'var':
                                continue 

                        if args_match:
                            target_literal = lit
                            break

                if target_literal:
                    var_map = {}
                    for idx, arg in enumerate(target_literal[1][2]):
                        if arg[0] == 'var' and arg[1] and arg[1] != '_' and idx < len(col_names):
                            var_map[arg[1]] = col_names[idx]

                    for comp_lit in body:
                        if comp_lit[1][0] == 'comparison':
                            left, op, right = comp_lit[1][1], comp_lit[1][2], comp_lit[1][3]

                            left_is_our_var = (
                                left[0] == 'var' and left[1] in var_map)
                            right_is_our_var = (
                                right[0] == 'var' and right[1] in var_map)

                            if left_is_our_var or right_is_our_var:
                                left_val = var_map.get(
                                    left[1], left[1]) if left[0] == 'var' else format_sql_value(left)
                                right_val = var_map.get(
                                    right[1], right[1]) if right[0] == 'var' else format_sql_value(right)

                                condition = f"{left_val} {op} {right_val}"
                                if condition not in filter_conditions:
                                    filter_conditions.append(condition)

                    break

        where_clause = f" WHERE {' AND '.join(filter_conditions)}" if filter_conditions else ''
        return f"SELECT {', '.join(select_parts)} FROM {pred}{where_clause}"

    def find_deps(target_pred, visited=None):
        if visited is None:
            visited = set()
        if target_pred in visited:
            return set()
        visited.add(target_pred)

        dependencies = {target_pred}
        if target_pred in pred_dict:
            args, rules = pred_dict[target_pred]
            for body in rules:
                for lit in body:
                    sign, atom = lit
                    if atom[0] == 'regular':
                        dep_pred = atom[1]
                        if dep_pred in pred_dict:
                            dependencies.update(
                                find_deps(dep_pred, visited.copy()))
        return dependencies

    needed_preds = find_deps(pred)

    def topo_sort(preds):
        result = []
        remaining = set(preds)

        while remaining:
            ready = []
            for p in remaining:
                if p in pred_dict:
                    args, rules = pred_dict[p]
                    has_idb_deps = False
                    for body in rules:
                        for lit in body:
                            sign, atom = lit
                            if atom[0] == 'regular':
                                dep_pred = atom[1]
                                if dep_pred in pred_dict and dep_pred in remaining and dep_pred != p:
                                    has_idb_deps = True
                                    break
                        if has_idb_deps:
                            break
                    if not has_idb_deps:
                        ready.append(p)
                else:
                    ready.append(p)

            if not ready:
                ready = [next(iter(remaining))]

            result.extend(ready)
            remaining -= set(ready)

        return result

    ordered_preds = topo_sort(needed_preds)

    def gen_pred_sql(target_pred, use_cte_names=False, is_cte=True):
        if target_pred not in pred_dict:
            # EDB predicate
            col_names = db.getAttributes(target_pred)
            return f"SELECT {', '.join(col_names)} FROM {target_pred}"

        args, rules = pred_dict[target_pred]
        select_cols = [a[1] for a in args]
        rule_sqls = []

        for body in rules:
            join_tables = []
            comparison_conditions = []
            var_map = {}
            table_count = 0

            for lit in body:
                sign, atom = lit
                if atom[0] == 'regular':
                    tablename = atom[1]
                    table_alias = f"t{table_count}"
                    table_count += 1

                    if use_cte_names and tablename in pred_dict:
                        col_names = [f"c{i}" for i in range(len(atom[2]))]
                    elif tablename not in pred_dict:
                        col_names = db.getAttributes(tablename)
                    else:
                        col_names = [f"c{i}" for i in range(len(atom[2]))]

                    join_tables.append(
                        (tablename, table_alias, atom[2], sign, col_names))

                    if sign == 'pos':
                        for i, arg in enumerate(atom[2]):
                            if arg[0] == 'var' and arg[1] != '_':
                                var_name = arg[1]
                                col_ref = f"{table_alias}.{col_names[i]}"
                                if var_name not in var_map:
                                    var_map[var_name] = col_ref

                elif atom[0] == 'comparison':
                    left_arg, op, right_arg = atom[1], atom[2], atom[3]
                    comparison_conditions.append((left_arg, op, right_arg))

            positive_tables = []
            for tablename, table_alias, args, sign, col_names in join_tables:
                if sign == 'pos':
                    positive_tables.append(
                        (tablename, table_alias, args, col_names))

            join_conditions = []
            filter_conditions = []

            for tablename, table_alias, args, sign, col_names in join_tables:
                if sign == 'pos':
                    for i, arg in enumerate(args):
                        col_ref = f"{table_alias}.{col_names[i]}"
                        if arg[0] == 'var' and arg[1] != '_':
                            var_name = arg[1]
                            if var_map[var_name] != col_ref:
                                other_ref = var_map[var_name]
                                if '.' in other_ref and other_ref.split('.')[0] != table_alias:
                                    join_conditions.append(
                                        f"{col_ref} = {other_ref}")
                                else:
                                    filter_conditions.append(
                                        f"{col_ref} = {other_ref}")
                        elif arg[0] in ('num', 'str'):
                            filter_conditions.append(
                                f"{col_ref} = {format_sql_value(arg)}")

            # Comparison
            for left_arg, op, right_arg in comparison_conditions:
                left_val = var_map.get(
                    left_arg[1], left_arg[1]) if left_arg[0] == 'var' else format_sql_value(left_arg)
                right_val = var_map.get(
                    right_arg[1], right_arg[1]) if right_arg[0] == 'var' else format_sql_value(right_arg)
                filter_conditions.append(f"{left_val} {op} {right_val}")

            # FROM
            if not positive_tables:
                from_clause = ""
            elif len(positive_tables) == 1:
                tablename, table_alias, _, _ = positive_tables[0]
                from_clause = f"FROM {tablename} {table_alias}"
            else:
                from_parts = [
                    f"FROM {positive_tables[0][0]} {positive_tables[0][1]}"]
                used_join_conditions = set()

                for i in range(1, len(positive_tables)):
                    tablename, table_alias, _, _ = positive_tables[i]
                    table_join_condition = None

                    for join_cond in join_conditions:
                        if f"{table_alias}." in join_cond and join_cond not in used_join_conditions:
                            table_join_condition = join_cond
                            used_join_conditions.add(join_cond)
                            break

                    if table_join_condition:
                        from_parts.append(
                            f"JOIN {tablename} {table_alias} ON {table_join_condition}")
                    else:
                        from_parts.append(
                            f"CROSS JOIN {tablename} {table_alias}")

                from_clause = " ".join(from_parts)

            # Negation
            for tablename, table_alias, args, sign, col_names in join_tables:
                if sign == 'neg':
                    sub_conditions = []
                    for i, arg in enumerate(args):
                        col_ref = f"{table_alias}.{col_names[i]}"
                        if arg[0] == 'var' and arg[1] != '_' and arg[1] in var_map:
                            sub_conditions.append(
                                f"{col_ref} = {var_map[arg[1]]}")
                        elif arg[0] in ('num', 'str'):
                            sub_conditions.append(
                                f"{col_ref} = {format_sql_value(arg)}")

                    if sub_conditions:
                        not_exists = f"NOT EXISTS (SELECT 1 FROM {tablename} {table_alias} WHERE {' AND '.join(sub_conditions)})"
                    else:
                        not_exists = f"NOT EXISTS (SELECT 1 FROM {tablename} {table_alias})"
                    filter_conditions.append(not_exists)

            # SELECT
            select_exprs = []
            for i, var_name in enumerate(select_cols):
                if var_name in var_map:
                    if is_cte:
                        select_exprs.append(f"{var_map[var_name]} AS c{i}")
                    else:
                        select_exprs.append(
                            f"{var_map[var_name]} AS {var_name}")
                else:
                    if is_cte:
                        select_exprs.append(f"NULL AS c{i}")
                    else:
                        select_exprs.append(f"NULL AS {var_name}")

            select_clause = f"SELECT {', '.join(select_exprs)}"
            where_clause = f"WHERE {' AND '.join(filter_conditions)}" if filter_conditions else ""
            rule_sql = f"{select_clause} {from_clause} {where_clause}".strip()
            rule_sqls.append(rule_sql)

        # Union
        if len(rule_sqls) == 1:
            return rule_sqls[0]
        else:
            return "\nUNION\n".join(rule_sqls)

    # cte
    cte_parts = []
    for p in ordered_preds:
        if p != pred:
            cte_sql = gen_pred_sql(p, use_cte_names=True, is_cte=True)
            cte_parts.append(f"{p} AS (\n{cte_sql}\n)")

    main_sql = gen_pred_sql(pred, use_cte_names=True, is_cte=False)

    if cte_parts:
        cte_clause = ',\n'.join(cte_parts)
        return f"WITH {cte_clause}\n{main_sql}"
    else:
        return main_sql


def main():
    dbfile = sys.argv[1]
    db = SQLite3()
    db.open(dbfile)
    while True:
        data = read_input()
        if data == 'exit;':
            break
        if data[0] == '@':
            with open(data[1:-1], encoding='utf-8') as f:
                query = f.read()
                try:
                    rules = dlog_parser.parse(query)
                    print(rules)
                    if rules is not None:
                        pred_dict = construct_data_structure(rules)
                        print(pred_dict)
                        result = semantic_checks(db, pred_dict)
                        if result == "OK":
                            dgraph = construct_dependency_graph(pred_dict)
                            print(dgraph)
                            all_preds = all_predicates(dgraph)
                            pred_list = construct_ordered_predicates(
                                all_preds, dgraph)
                            print(pred_list)
                            sql_dict = {}
                            for pred in pred_list:
                                sql_query = generate_sql(
                                    pred, pred_dict, db, rules)
                                print(f"SQL for {pred}:")
                                print(sql_query)
                                sql_dict[pred] = sql_query
                        else:
                            print(result)
                except (TypeError, ValueError, SyntaxError) as inst:
                    print(inst.args[0])
                except Exception as inst:
                    print(f"Unexpected error: {inst}")


if __name__ == "__main__":
    main()
