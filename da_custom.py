def dummyfunctionfortransform(data, param):
    """
    data is a list of values
    parameter is an element

    Define functions here that can be used in transform command
    """
    out = [str(i) + str(param) for i in data]
    return out
