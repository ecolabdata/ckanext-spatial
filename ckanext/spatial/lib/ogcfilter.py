"""
Small functions to handle OGC filters.

Syntax is similar to OWSLib's classes, albeit suited
to JSON encoding.
"""

import owslib.fes as ows


# OWSLib classes for OGC Filter operators
# with list of allowed types for each parameter
ogc_filter_operators = {
    'PropertyIsLike': [[str], [str]],
    'PropertyIsNull': [[str]],
    'PropertyIsBetween': [[str], [str, int, float], [str, int, float]],
    'PropertyIsGreaterThanOrEqualTo': [[str], [str, int, float]],
    'PropertyIsLessThanOrEqualTo': [[str], [str, int, float]],
    'PropertyIsGreaterThan': [[str], [str, int, float]],
    'PropertyIsLessThan': [[str], [str, int, float]],
    'PropertyIsNotEqualTo': [[str], [str, int, float]],
    'PropertyIsEqualTo': [[str], [str, int, float]],
    'BBox': [[int, float], [int, float], [int, float], [int, float]]
    }


def as_owslib_constraint(constraint):
    """
    Rewrite an individual constraint using OWSLib classes (PropertyIsLike...)

    Parameter
    ---------
    - constraint : a list, such as
    ["PropertyIsLike", "MyProperty1", "MyValue1"]
    
    First element should be the name of an OGC Filter operator,
    other elements are parameters for the OWSLib constructor.
    
    To negate the operator, add "Not" as first element :
    ["Not", "PropertyIsLike", "MyProperty1", "MyValue1"]
    
    """
    neg = (constraint[0].upper() == 'NOT')

    if neg:
        constraint = constraint[1:]

    if not constraint[0] in ogc_filter_operators:
        raise ValueError("Unknow operator '{}' in ogcfilter".format(constraint[0]))

    if len(constraint[1:]) < len(ogc_filter_operators[constraint[0]]):
        raise ValueError("Missing some parameters for operator '{}' in ogcfilter".format(constraint[0]))

    if len(constraint[1:]) > len(ogc_filter_operators[constraint[0]]):
        raise ValueError("Too much parameters for operator '{}' in ogcfilter".format(constraint[0]))
    
    if not all(
        map(
            lambda x, s: any(
                map(
                    lambda t: isinstance(x, t),
                    s
                    )
                ),
            constraint[1:],
            ogc_filter_operators[constraint[0]]
            )
        ):
        raise TypeError("At least one parameter of incorrect type for operator '{}' in ogcfilter".format(constraint[0]))
    
    s = "ows.{}([{}])" if constraint[0]=='BBox' else "ows.{}({})"
    # BBox is expecting a list of numbers
    
    if neg:
        s = "ows.Not([{}])".format(s)

    return eval(s.format(constraint[0],", ".join([repr(e) for e in constraint[1:]])))



def parse_constraints(ogcfilter, rec=None):
    """
    Make a valid constraints list out of user-defined ogcfilter parameter

    Parameters
    ---------
    - ogcfilter : a list retrieved from user configuration
    - rec is intended for recursive execution only

    For example, this json configuration
    {
        "ogcfilter": [
            ["PropertyIsLike", "MyProperty1", "MyValue1"],
            ["Not", "PropertyIsEqualTo", "MyProperty2", "MyValue2"]
        ]
    }

    would be interpreted as
    [
        PropertyIsLike("MyProperty1", "MyValue1"),
        Not( [ PropertyIsEqualTo("MyProperty2", "MyValue2") ] )
    ]

    Result is intended for use as "constraints" parameter of OWSLib's
    functions such as getrecords2.
    
    """

    if rec is None:
        rec = []
        
    for i in range(len(ogcfilter)):
        
        if not isinstance(ogcfilter[i], list):
            raise TypeError("Malformed ogcfilter, expecting a list of lists")

        if isinstance(ogcfilter[i][0], str):        
            rec.append(as_owslib_constraint(ogcfilter[i]))
        else:
            rec.append([])            
            parse_constraints(ogcfilter[i], rec[i]) 
        
    return rec
    
