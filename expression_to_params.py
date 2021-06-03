from collections import defaultdict

from glom import glom
from polar import Expression

"""
Functions for transforming Polar Expressions into query parameters for an upstream FHIR server
"""

class UnhandledExpression(Exception):
    pass


def expression_to_params(expr: Expression):
    # Stupidly simplified expression to query parameters. Really this should handle everything explicitly and
    # throw if we encountered something we didn't expect.
    if expr.operator == "Isa":
        # Skip these, we already know the types we're looking at
        return []
    elif expr.operator == "In" and expr.args[1].__repr__() == "Expression(Dot, [Variable('_this'), 'sourceIds'])":
        sourceId = expr.args[0]
        return [("_security", "http://fhir.patientsknowbest.com/codesystem/source-id|{}".format(sourceId))]
    elif expr.operator == "Unify" and expr.args[1].__repr__() == "Expression(Dot, [Variable('_this'), 'privacyFlag'])":
        privacyFlag = expr.args[0]
        return [("_security", "http://fhir.patientsknowbest.com/codesystem/privacy-label|{}".format(privacyFlag))]
    else:
        return []


def results_to_params(results):
    """
    This is a really noddy function for transforming Polar Expressions into query parameters for upstream FHIR server.
    Really it should take into account the existing search params, and if those are already a subset of the ones we're 
    allowed to search for, then don't modify the query. 
    Also we should handle multiple fields in combination properly, see documentation for composing FHIR SEARCH params: 
    https://www.hl7.org/fhir/search.html
    
    :param results: 
    :return: 
    """
    all_params = []
    for res in results:
        top_expr: Expression = glom(res, "bindings.resource")
        if top_expr.operator != "And":
            raise UnhandledExpression("Can't handle operator other than 'And' as top level expression")
        
        params = []
        for sub_expr in top_expr.args:
            params.extend(expression_to_params(sub_expr))
        if len(params) > 1:
            raise UnhandledExpression("Can't handle more than 1 set of params from a single top level expression")
        all_params.extend(params)
    # Combine the query parameters as an OR expression, that is comma separated 
    final_params = defaultdict(str)
    for (k, v) in all_params:
        val = final_params[k]
        if len(val) == 0:
            val = v
        else:
            if not v in val:
                val = val + "," + v
        final_params[k]= val
    if len(final_params) > 1:
        raise UnhandledExpression("Can't properly handle more than 1 field specified in authz query param")
    return list(final_params.items())