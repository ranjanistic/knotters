from uuid import uuid4


def getLocalKey():
    return f'testing-{uuid4().hex}'


def getLocalValue():
    return f'testing-value-{uuid4().hex}'
