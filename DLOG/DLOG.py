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

def rename_vars_in_body(d,body):
  result = []
  for lit in body:
    new_args = []
    if lit[1][0] == 'regular':
      for arg in lit[1][2]:
        if arg[0] == 'var' and arg[1] in d:
          new_args.append(('var',d[arg[1]]))
        else:
          new_args.append(arg)
      newlit = (lit[0],('regular',lit[1][1],new_args))
      result.append(newlit)
    else: # must be comparison literal
      lop = lit[1][1]
      if lit[1][1][0] == 'var' and lit[1][1][1] in d:
        lop = ('var',d[lit[1][1][1]])
      rop = lit[1][3]
      if lit[1][3][0] == 'var' and lit[1][3][1] in d:
        rop = ('var',d[lit[1][3][1]])
      result.append((lit[0],('comparison',lop,lit[1][2],rop)))
  return result

def construct_data_structure(rules):
  result = {}
  for (head,body) in rules:
    if head[1] in result:
      d = {v[0][1]:v[1][1] for v in zip(head[2],result[head[1]][0])} 
      new_body = rename_vars_in_body(d,body)
      result[head[1]] = (result[head[1]][0],result[head[1]][1]+[new_body])
    else:
      result[head[1]] = (head[2],[body])
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

def construct_ordered_predicates(all_preds,dgraph):
  print("inside construct_ordered_predicates")
  # since no recursion, we will simply +1 to head predicate
  strata = {p:0 for p in all_preds}
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
  print("max_strata",max_strata)
  print("strata",strata)
  strata_inv = {i:[] for i in range(max_strata+1)}
  for p in strata:
    strata_inv[strata[p]].append(p)
  print(strata_inv)
  result = []
  for i in range(1,1+max_strata):
    result = result + strata_inv[i]
    print(result)
  print("result",result)
  return result

def all_predicates(dgraph):
  result = set([p for p in dgraph])
  for p in dgraph:
    result = result.union(dgraph[p])
  return result

def semantic_checks(db, pred_dict):
    idb_preds = set(pred_dict.keys())  # IDB predicates, appear in head of rules   
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
    #print("IDB predicates:", idb_preds) 
    #print("All body predicates:", all_body_preds)

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

def generate_ra(pred,pred_dict):
  return "RA Expr"

def main():
  dbfile = sys.argv[1]
  db = SQLite3()
  db.open(dbfile)
  while True:
    data = read_input() 
    if data == 'exit;':
      break
    if data[0] == '@':
      with open(data[1:-1]) as f:
        query = f.read()
        try:
          rules = dlog_parser.parse(query)
          print(rules)
          if rules is not None:
            pred_dict = construct_data_structure(rules)
            print(pred_dict)
            result = semantic_checks(db,pred_dict)
            if result == "OK":
              dgraph = construct_dependency_graph(pred_dict)
              print(dgraph)
              all_preds = all_predicates(dgraph)
              pred_list = construct_ordered_predicates(all_preds,dgraph)
              print(pred_list) 
              ra_expr_dict = {}
              for pred in pred_list:
                ra_expr = generate_ra(pred,pred_dict)
                print(ra_expr)
                ra_expr_dict[pred] = ra_expr
            else:
              print(result)
        except Exception as inst:
          print(inst.args[0])
 

if __name__ == "__main__":
    main()
