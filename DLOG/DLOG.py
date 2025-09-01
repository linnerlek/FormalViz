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


# --- SQL Generation ---

def format_sql_value(arg):
    if arg[0] == 'num':
        return str(arg[1])
    if arg[0] == 'str':
        return f"'{arg[1]}'"
    if arg[0] == 'var':
        return arg[1]
    return str(arg[1])


def generate_sql(pred, pred_dict, db=None, edb_tables=None, cte_defs=None, visited=None):
    """
    Generate SQL for the given predicate using the Datalog program in pred_dict.
    Handles negation, comparisons, temps, and multi-rule predicates.
    Returns a string with the SQL query for the predicate.
    db: SQLite3 instance (required for EDB schema lookup)
    """
    if edb_tables is None:
        edb_tables = set()
    if cte_defs is None:
        cte_defs = {}
    if visited is None:
        visited = set()

    if pred in visited:
        return cte_defs.get(pred, None)  # Already generated
    visited.add(pred)

    # EDB predicate: just select from the table with real column names
    if pred not in pred_dict:
        if db is None:
            raise Exception(
                "Database handle (db) required for EDB predicate SQL generation.")
        if not db.relationExists(pred):
            raise Exception(f"EDB predicate '{pred}' not found in database.")
        col_names = db.getAttributes(pred)
        select_sql = f"SELECT {', '.join(col_names)} FROM {pred}"
        return select_sql

    # Build complete SQL with all necessary CTEs
    return generate_complete_sql(pred, pred_dict, db)


def generate_complete_sql(target_pred, pred_dict, db):
    """
    Generate a complete SQL query with CTEs for all IDB predicates that the target predicate depends on.
    """
    # Find all IDB predicates that need to be defined
    needed_preds = find_dependencies(target_pred, pred_dict)

    # Sort predicates in dependency order (bottom-up)
    ordered_preds = topological_sort(needed_preds, pred_dict)

    # Generate CTE definitions
    cte_parts = []

    for pred in ordered_preds:
        if pred != target_pred:  # Don't include the target predicate in CTEs
            cte_sql = generate_predicate_sql(
                pred, pred_dict, db, use_cte_names=True, is_cte=True)
            cte_parts.append(f"{pred} AS (\n{cte_sql}\n)")

    # Generate the main query for the target predicate (with original variable names)
    main_sql = generate_predicate_sql(
        target_pred, pred_dict, db, use_cte_names=True, is_cte=False)

    # Combine CTEs and main query
    if cte_parts:
        full_sql = f"WITH {',\n'.join(cte_parts)}\n{main_sql}"
    else:
        full_sql = main_sql

    return full_sql


def find_dependencies(pred, pred_dict, visited=None):
    """Find all IDB predicates that this predicate depends on (transitively)."""
    if visited is None:
        visited = set()

    if pred in visited:
        return set()
    visited.add(pred)

    dependencies = {pred}

    if pred in pred_dict:
        args, rules = pred_dict[pred]
        for body in rules:
            for lit in body:
                sign, atom = lit
                if atom[0] == 'regular':
                    dep_pred = atom[1]
                    if dep_pred in pred_dict:  # IDB predicate
                        dependencies.update(find_dependencies(
                            dep_pred, pred_dict, visited.copy()))

    return dependencies


def topological_sort(preds, pred_dict):
    """Sort predicates in dependency order (bottom-up)."""
    # Simple topological sort - predicates with no IDB dependencies come first
    result = []
    remaining = set(preds)

    while remaining:
        # Find predicates with no remaining dependencies
        ready = []
        for pred in remaining:
            if pred in pred_dict:
                args, rules = pred_dict[pred]
                has_idb_deps = False
                for body in rules:
                    for lit in body:
                        sign, atom = lit
                        if atom[0] == 'regular':
                            dep_pred = atom[1]
                            if dep_pred in pred_dict and dep_pred in remaining and dep_pred != pred:
                                has_idb_deps = True
                                break
                    if has_idb_deps:
                        break
                if not has_idb_deps:
                    ready.append(pred)
            else:
                ready.append(pred)  # EDB predicate

        if not ready:
            # Break cycles by picking one arbitrarily
            ready = [next(iter(remaining))]

        result.extend(ready)
        remaining -= set(ready)

    return result


def generate_predicate_sql(pred, pred_dict, db, use_cte_names=False, is_cte=True):
    """
    Generate SQL for a single predicate, using CTE names for IDB predicates if use_cte_names is True.
    If is_cte is True, use standardized column names (c0, c1, etc.) for consistency.
    If is_cte is False, use the original variable names from the predicate head.
    """
    if pred not in pred_dict:
        # EDB predicate
        if db is None:
            raise Exception(
                "Database handle required for EDB predicate SQL generation.")
        if not db.relationExists(pred):
            raise Exception(f"EDB predicate '{pred}' not found in database.")
        col_names = db.getAttributes(pred)
        return f"SELECT {', '.join(col_names)} FROM {pred}"

    args, rules = pred_dict[pred]
    select_cols = [a[1] for a in args]  # Variable names for the head
    rule_sqls = []

    for body in rules:
        # Track tables/predicates used in this rule
        join_tables = []  # (tablename, alias, args, sign)
        comparison_conditions = []
        var_map = {}  # Maps variables to their first occurrence column reference
        table_count = 0

        # First pass: identify all predicates and build variable mappings
        for lit in body:
            sign, atom = lit
            if atom[0] == 'regular':
                tablename = atom[1]
                table_alias = f"t{table_count}"
                table_count += 1

                # Determine column names
                if use_cte_names and tablename in pred_dict:
                    # IDB predicate - use c0, c1, c2, etc.
                    col_names = [f"c{i}" for i in range(len(atom[2]))]
                elif db is not None and tablename not in pred_dict:
                    # EDB predicate - use actual column names
                    col_names = db.getAttributes(tablename)
                else:
                    # IDB predicate without CTEs - use c0, c1, c2, etc.
                    col_names = [f"c{i}" for i in range(len(atom[2]))]

                join_tables.append(
                    (tablename, table_alias, atom[2], sign, col_names))

                # Map variables to columns (only for positive literals)
                if sign == 'pos':
                    for i, arg in enumerate(atom[2]):
                        if arg[0] == 'var' and arg[1] != '_':
                            var_name = arg[1]
                            col_ref = f"{table_alias}.{col_names[i]}"
                            if var_name not in var_map:
                                var_map[var_name] = col_ref

            elif atom[0] == 'comparison':
                # Handle comparison predicates
                left_arg, op, right_arg = atom[1], atom[2], atom[3]
                comparison_conditions.append((left_arg, op, right_arg))

        # Build FROM clause (only positive literals)
        from_tables = []
        for tablename, table_alias, args, sign, col_names in join_tables:
            if sign == 'pos':
                from_tables.append(f"{tablename} {table_alias}")

        # Build WHERE conditions
        where_conditions = []

        # Variable equality conditions
        for tablename, table_alias, args, sign, col_names in join_tables:
            if sign == 'pos':
                for i, arg in enumerate(args):
                    col_ref = f"{table_alias}.{col_names[i]}"
                    if arg[0] == 'var' and arg[1] != '_':
                        var_name = arg[1]
                        if var_map[var_name] != col_ref:
                            # This variable appears elsewhere, add equality condition
                            where_conditions.append(
                                f"{col_ref} = {var_map[var_name]}")
                    elif arg[0] in ('num', 'str'):
                        # Constant condition
                        where_conditions.append(
                            f"{col_ref} = {format_sql_value(arg)}")

        # Comparison conditions
        for left_arg, op, right_arg in comparison_conditions:
            left_val = format_comparison_operand(left_arg, var_map)
            right_val = format_comparison_operand(right_arg, var_map)
            where_conditions.append(f"{left_val} {op} {right_val}")

        # Negation conditions (NOT EXISTS)
        for tablename, table_alias, args, sign, col_names in join_tables:
            if sign == 'neg':
                # Build NOT EXISTS subquery
                sub_conditions = []
                for i, arg in enumerate(args):
                    col_ref = f"{table_alias}.{col_names[i]}"
                    if arg[0] == 'var' and arg[1] != '_' and arg[1] in var_map:
                        sub_conditions.append(f"{col_ref} = {var_map[arg[1]]}")
                    elif arg[0] in ('num', 'str'):
                        sub_conditions.append(
                            f"{col_ref} = {format_sql_value(arg)}")

                if sub_conditions:
                    not_exists = f"NOT EXISTS (SELECT 1 FROM {tablename} {table_alias} WHERE {' AND '.join(sub_conditions)})"
                else:
                    not_exists = f"NOT EXISTS (SELECT 1 FROM {tablename} {table_alias})"
                where_conditions.append(not_exists)

        # Build SELECT clause - use original variable names if this is the final query
        select_exprs = []
        for i, var_name in enumerate(select_cols):
            if var_name in var_map:
                if is_cte:
                    # For CTEs, use standardized column names
                    select_exprs.append(f"{var_map[var_name]} AS c{i}")
                else:
                    # For final query, use original variable names as aliases
                    col_ref = var_map[var_name]
                    select_exprs.append(f"{col_ref} AS {var_name}")
            else:
                if is_cte:
                    select_exprs.append(f"NULL AS c{i}")
                else:
                    select_exprs.append(f"NULL AS {var_name}")

        # Construct the SQL for this rule
        select_clause = f"SELECT {', '.join(select_exprs)}"
        from_clause = f"FROM {', '.join(from_tables)}" if from_tables else ""
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

        rule_sql = f"{select_clause} {from_clause} {where_clause}".strip()
        rule_sqls.append(rule_sql)

    # Union all rules for this predicate
    if len(rule_sqls) == 1:
        union_sql = rule_sqls[0]
    else:
        union_sql = "\nUNION\n".join(rule_sqls)

    return union_sql


def format_comparison_operand(arg, var_map):
    """Format an operand in a comparison, handling variables and constants."""
    if arg[0] == 'var':
        if arg[1] in var_map:
            return var_map[arg[1]]
        else:
            return arg[1]  # Unbound variable, use as-is
    else:
        return format_sql_value(arg)


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
                                sql_query = generate_sql(pred, pred_dict, db)
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
