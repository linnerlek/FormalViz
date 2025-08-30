import math
import json
from Lambda.LambdaParser import LambdaParser

lambda_parser = LambdaParser()


def free_variables(tree):
    if tree[0] == "name":
        return {tree[1]}
    elif tree[0] == "num":
        return set()
    elif tree[0] == "lambda":
        t = free_variables(tree[2])
        t.discard(tree[1])
        return t
    else:  # must be  "op" or "apply"
        return free_variables(tree[1]).union(free_variables(tree[2]))


def alpha_replace(tree, oldvar, newvar):
    if tree[0] == "name":
        if tree[1] == oldvar:
            return ["name", newvar]
        else:
            return ["name", tree[1]]
    elif tree[0] == "num":
        return ["num", tree[1]]
    elif tree[0] == "lambda":
        if tree[1] == oldvar:
            return ["lambda", oldvar, tree[2]]
        else:
            return ["lambda", tree[1], alpha_replace(tree[2], oldvar, newvar)]
    else:  # must be  "op" or "apply"
        return [tree[0], alpha_replace(tree[1], oldvar, newvar), alpha_replace(tree[2], oldvar, newvar)]


def alpha_convert(tree, var):
    if tree[0] == 'lambda':
        return ['lambda', var, alpha_replace(tree[2], tree[1], var)]
    else:
        return tree


def substitute(tree, var, val):
    if tree[0] == "name":
        if tree[1] == var:
            return val
        else:
            return tree
    elif tree[0] == "num":
        return tree
    elif tree[0] == "lambda":
        if tree[1] == var:
            return tree
        elif tree[1] not in free_variables(val):
            return ['lambda', tree[1], substitute(tree[2], var, val), tree[3]]
        else:
            global counter
            newvar = '_'+str(counter)
            counter += 1
            [a, b, new_body] = alpha_convert(tree, newvar)
            return ['lambda', newvar, substitute(new_body, var, val), tree[3]]
    else:  # must be  "op" or "apply"
        return [tree[0], substitute(tree[1], var, val), substitute(tree[2], var, val), tree[3]]


def to_string(tree):
    s = ""
    if tree[0] == "name":
        s += tree[1]
    elif tree[0] == "num":
        s += str(tree[1])
    elif tree[0] == "lambda":
        s += "(LAMBDA "+tree[1]+" "+to_string(tree[2])+")"
    elif tree[0] == "apply":
        s += "("+to_string(tree[1])+" "+to_string(tree[2])+")"
    else:  # must be  "op"
        s += "("+tree[0]+" "+to_string(tree[1])+" "+to_string(tree[2])+")"
    return s


def json2tree(jtree):
    if jtree["type"] == "num":
        return ["num", jtree["value"]]
    elif jtree["type"] == "name":
        return ["name", jtree["value"]]
    elif jtree["type"] == "lambda":
        return ["lambda", jtree["var"], json2tree(jtree["children"][0])]
    elif jtree["type"] == "apply":
        return ["apply", json2tree(jtree["children"][0]), json2tree(jtree["children"][1])]
    else:  # must be op
        return [jtree["value"], json2tree(jtree["children"][0]), json2tree(jtree["children"][1])]


def tree2dict(tree):
    if tree[0] == "name":
        return {"nodeid": tree[2], "type": tree[0], "value": tree[1], "children": []}
    elif tree[0] == "num":
        # print(tree)
        return {"nodeid": tree[2], "type": tree[0], "value": str(tree[1]), "children": []}
    elif tree[0] == "lambda":
        return {"nodeid": tree[3], "type": tree[0], "var": tree[1], "children": [tree2dict(tree[2])]}
    elif tree[0] == "apply":
        if tree[3]:
            return {"nodeid": tree[4], "type": tree[0], "beta": "YES", "children": [tree2dict(tree[1]), tree2dict(tree[2])]}
        else:
            return {"nodeid": tree[4], "type": tree[0], "beta": "NO", "children": [tree2dict(tree[1]), tree2dict(tree[2])]}
    else:  # must be  "op"
        return {"nodeid": tree[3], "type": "op", "value": tree[0], "children": [tree2dict(tree[1]), tree2dict(tree[2])]}


def add_node_ids(tree, prefix):
    if tree[0] in ['num', 'name']:
        return tree + [prefix]
    elif tree[0] == 'lambda':
        return ['lambda', tree[1], add_node_ids(tree[2], prefix+'0'), prefix]
    elif tree[0] == 'apply':
        return ['apply', add_node_ids(tree[1], prefix+'0'), add_node_ids(tree[2], prefix+'1'), tree[3], prefix]
    else:  # must be op
        return [tree[0], add_node_ids(tree[1], prefix+'0'), add_node_ids(tree[2], prefix+'1'), prefix]


def remove_node_ids(tree):
    if tree[0] in ['num', 'name']:
        return tree[0:-1]
    elif tree[0] == 'lambda':
        return ['lambda', tree[1], remove_node_ids(tree[2])]
    elif tree[0] == 'apply':
        return [tree[0], remove_node_ids(tree[1]), remove_node_ids(tree[2]), tree[3]]
    else:  # must be op
        return [tree[0], remove_node_ids(tree[1]), remove_node_ids(tree[2])]


def adjust_betaBool(tree):
    if tree[0] in ['num', 'name']:
        return tree[0:2]
    elif tree[0] == 'lambda':
        return [tree[0], tree[1], adjust_betaBool(tree[2])]
    elif tree[0] == 'apply':
        leftChildLambda = (tree[1][0] == 'lambda')
        return ['apply', adjust_betaBool(tree[1]), adjust_betaBool(tree[2]), leftChildLambda]
    else:  # must be op
        return [tree[0], adjust_betaBool(tree[1]), adjust_betaBool(tree[2])]


def get_initial_tree(expr):
    try:
        tree = lambda_parser.parse(expr)
        tree = adjust_betaBool(tree)
        tree = add_node_ids(tree, 'R')
        jsonDict = tree2dict(tree)
        result = {"status": "OK", "expr_tree_json": jsonDict}
        return result
    except Exception as inst:
        print(inst.args[0])
        result = {"status": "ERROR", "message": inst.args[0]}
        return result


def specific_beta_reduction(etree, nodeid):
    # make sure beta Boolean is reset on new tree (write a separate function to do this)
    if etree[0] == "name" or etree[0] == "num":
        return (False, etree)
    elif etree[0] == "lambda":
        (b, t) = specific_beta_reduction(etree[2], nodeid)
        if b:
            return (True, ["lambda", etree[1], t, etree[3]])
        else:
            return (False, etree)
    elif etree[0] == "apply":
        if etree[4] == nodeid:
            return (True, substitute(etree[1][2], etree[1][1], etree[2]))
        else:
            (b, t) = specific_beta_reduction(etree[1], nodeid)
            if b:
                leftChildLambda = (t[0] == 'lambda')
                return (True, ["apply", t, etree[2], leftChildLambda, etree[4]])
            else:
                (b, t) = specific_beta_reduction(etree[2], nodeid)
                if b:
                    leftChildLambda = (t[0] == 'lambda')
                    return (True, ["apply", etree[1], t, leftChildLambda, etree[4]])
                else:
                    return (False, etree)
    else:  # must be "op"
        (b, t) = specific_beta_reduction(etree[1], nodeid)
        if b:
            return (True, [etree[0], t, etree[2], etree[3]])
        else:
            (b, t) = specific_beta_reduction(etree[2], nodeid)
            if b:
                return (True, [etree[0], etree[1], t, etree[3]])
            else:
                return (False, etree)


def get_next_tree(jtree, nodeid):
    etree = json2tree(jtree)
    etree = adjust_betaBool(etree)
    etree = add_node_ids(etree, 'R')
    (status, etree) = specific_beta_reduction(etree, nodeid)
    if status:
        etree = remove_node_ids(etree)
        etree = adjust_betaBool(etree)
        etree = add_node_ids(etree, 'R')
        return etree
    else:
        print('Something went WRONG!')
        return None


def get_next_tree_after_math(jtree, nodeid):
    etree = json2tree(jtree)
    etree = adjust_betaBool(etree)
    # print("before add_node_ids in eval_math",etree)
    etree = add_node_ids(etree, 'R')
    # print("before eval_math",etree)
    # this will alter the tree and nodeids will be messed up
    etree = eval_math(etree, nodeid)
    # print("after eval_math",etree)
    etree = remove_node_ids(etree)
    etree = add_node_ids(etree, 'R')
    return etree


def eval_math(tree, nodeid):
    if tree[0] == "name" or tree[0] == "num":
        return tree
    elif tree[0] == "lambda":
        return ["lambda", tree[1], eval_math(tree[2], nodeid), tree[3]]
    elif tree[0] == "apply":
        return ["apply", eval_math(tree[1], nodeid), eval_math(tree[2], nodeid), tree[3]]
    elif tree[-1] != nodeid:  # is "op" and does not match nodeid
        return [tree[0], eval_math(tree[1], nodeid), eval_math(tree[2], nodeid), tree[3]]
    else:  # is "op" and matches nodeid
        return apply_math(tree)


def apply_math(tree):
    # tree = remove_node_ids(tree)
    val1 = process_math(tree[1])
    val2 = process_math(tree[2])
    # tree = add_node_ids(tree,'R')
    if val1[0] == "num" and val2[0] == "num":
        if tree[0] == "+":
            return ["num", float(val1[1])+float(val2[1]), ""]
        elif tree[0] == "-":
            return ["num", float(val1[1])-float(val2[1]), ""]
        elif tree[0] == "*":
            return ["num", float(val1[1])*float(val2[1]), ""]
        elif val2[1] != 0:
            return ["num", float(val1[1])/float(val2[1]), ""]
        else:
            return ["num", math.nan, ""]
    elif val1[0] == "num" and val2[0] != "num":
        return [tree[0], ["num", val1[1]], val2, ""]
    elif val1[0] != "num" and val2[0] == "num":
        return [tree[0], val1, ["num", val2[1]], ""]
    else:
        return [tree[0], val1, val2, ""]


def process_math(tree):
    if tree[0] == "name" or tree[0] == "num":
        return tree
    elif tree[0] == "lambda":
        return ["lambda", tree[1], process_math(tree[2]), tree[3]]
    elif tree[0] == "apply":
        return ["apply", process_math(tree[1]), process_math(tree[2]), tree[3]]
    else:  # must be "op"
        val1 = process_math(tree[1])
        val2 = process_math(tree[2])
        if val1[0] == "num" and val2[0] == "num":
            if tree[0] == "+":
                return ["num", float(val1[1])+float(val2[1]), ""]
            elif tree[0] == "-":
                return ["num", float(val1[1])-float(val2[1]), ""]
            elif tree[0] == "*":
                return ["num", float(val1[1])*float(val2[1]), ""]
            elif val2[1] != 0:
                return ["num", float(val1[1])/float(val2[1]), ""]
            else:
                return ["num", math.nan, ""]
        elif val1[0] == "num" and val2[0] != "num":
            return [tree[0], ["num", val1[1]], val2, ""]
        elif val1[0] != "num" and val2[0] == "num":
            return [tree[0], val1, ["num", val2[1]], ""]
        else:
            return [tree[0], val1, val2, ""]
