from uuid import uuid4
from main.strings import url, DOCS, AUTH

B64 = "data:image/png;base64,PGh0bWwgbGFuZz0iZGUiPjxoZWFkPjxtZXRhIGh0dHAtZXF1aXY9IkNvbnRlbnQtVHlwZSIgY29udGVudD0idGV4dC9odG1sOyBjaGFyc2V0PUlTTy04ODU5LTEiPjx0aXRsZT5XZWl0ZXJsZWl0dW5nc2hpbndlaXM8L3RpdGxlPjxzdHlsZT5ib2R5LGRpdixhe2ZvbnQtZmFtaWx5OlJvYm90byxIZWx2ZXRpY2EgTmV1ZSxBcmlhbCxzYW5zLXNlcmlmfWJvZHl7YmFja2dyb3VuZC1jb2xvcjojZmZmO21hcmdpbi10b3A6M3B4fWRpdntjb2xvcjojMDAwfWE6bGlua3tjb2xvcjojNGIxMWE4fWE6dmlzaXRlZHtjb2xvcjojNGIxMWE4fWE6YWN0aXZle2NvbG9yOiNlYTQzMzV9ZGl2Lm15bUdve2JvcmRlci10b3A6MXB4IHNvbGlkICNkYWRjZTA7Ym9yZGVyLWJvdHRvbToxcHggc29saWQgI2RhZGNlMDtiYWNrZ3JvdW5kOiNmOGY5ZmE7bWFyZ2luLXRvcDoxZW07d2lkdGg6MTAwJX1kaXYuYVhnYUdie3BhZGRpbmc6MC41ZW0gMDttYXJnaW4tbGVmdDoxMHB4fWRpdi5mVGs3dmR7bWFyZ2luLWxlZnQ6MzVweDttYXJnaW4tdG9wOjM1cHh9PC9zdHlsZT48L2hlYWQ+PGJvZHk+PGRpdiBjbGFzcz0ibXltR28iPjxkaXYgY2xhc3M9ImFYZ2FHYiI+PGZvbnQgc3R5bGU9ImZvbnQtc2l6ZTpsYXJnZXIiPjxiPldlaXRlcmxlaXR1bmdzaGlud2VpczwvYj48L2ZvbnQ+PC9kaXY+PC9kaXY+PGRpdiBjbGFzcz0iZlRrN3ZkIj4mbmJzcDtEaWUgdm9uIGRpciBiZXN1Y2h0ZSBTZWl0ZSB2ZXJzdWNodCwgZGljaCBhbiA8YSBocmVmPSJodHRwczovL2F1dGgwLmNvbS9ibG9nL2ludHJvZHVjdGlvbi10by1kamFuZ28tMy1idWlsZGluZy1hdXRoZW50aWNhdGluZy1hbmQtZGVwbG95aW5nLXBhcnQtMS8iPmh0dHBzOi8vYXV0aDAuY29tL2Jsb2cvaW50cm9kdWN0aW9uLXRvLWRqYW5nby0zLWJ1aWxkaW5nLWF1dGhlbnRpY2F0aW5nLWFuZC1kZXBsb3lpbmctcGFydC0xLzwvYT4gd2VpdGVyenVsZWl0ZW4uPGJyPjxicj4mbmJzcDtGYWxscyBkdSBkaWVzZSBTZWl0ZSBuaWNodCBiZXN1Y2hlbiBt9mNodGVzdCwga2FubnN0IGR1IDxhIGhyZWY9IiMiIGlkPSJ0c3VpZDEiPnp1ciB2b3JoZXJpZ2VuIFNlaXRlIHp1cvxja2tlaHJlbjwvYT4uPHNjcmlwdCBub25jZT0iRmlSaVNPVWxJbC9jNnFMK1NWdTZIdz09Ij4oZnVuY3Rpb24oKXt2YXIgaWQ9J3RzdWlkMSc7KGZ1bmN0aW9uKCl7CmRvY3VtZW50LmdldEVsZW1lbnRCeUlkKGlkKS5vbmNsaWNrPWZ1bmN0aW9uKCl7d2luZG93Lmhpc3RvcnkuYmFjaygpO3JldHVybiExfTt9KS5jYWxsKHRoaXMpO30pKCk7KGZ1bmN0aW9uKCl7dmFyIGlkPSd0c3VpZDEnO3ZhciBjdD0nb3JpZ2lubGluayc7dmFyIG9pPSd1bmF1dGhvcml6ZWRyZWRpcmVjdCc7KGZ1bmN0aW9uKCl7CmRvY3VtZW50LmdldEVsZW1lbnRCeUlkKGlkKS5vbm1vdXNlZG93bj1mdW5jdGlvbigpe3ZhciBiPWRvY3VtZW50JiZkb2N1bWVudC5yZWZlcnJlcixhPXdpbmRvdyYmd2luZG93LmVuY29kZVVSSUNvbXBvbmVudD9lbmNvZGVVUklDb21wb25lbnQ6ZXNjYXBlLGM9IiI7YiYmKGM9YShiKSk7KG5ldyBJbWFnZSkuc3JjPSIvdXJsP3NhPVQmdXJsPSIrYysiJm9pPSIrYShvaSkrIiZjdD0iK2EoY3QpO3JldHVybiExfTt9KS5jYWxsKHRoaXMpO30pKCk7PC9zY3JpcHQ+PGJyPjxicj48YnI+PC9kaXY+PC9ib2R5PjwvaHRtbD4="


def getLegalName():
    return uuid4().hex
    
def getTestUrl():
    return f'https://knotters.org/{uuid4().hex}'

def getLegalPseudonym():
    return uuid4().hex


def getLegalContent():
    string = ""
    for i in range(100):
        string += uuid4().hex
    return string


def root(path='/', appendslash=False):
    return f"{url.getRoot('', not appendslash)}{path}"


def docroot(path='/', appendslash=False):
    return f"{url.getRoot(DOCS, not appendslash)}{path}"


def authroot(path='/', appendslash=False):
    return f"{url.getRoot(AUTH, not appendslash)}{path}"


def getRandomStr():
    return uuid4().hex
