def flatten(S):
    q = []
    for item in S:
        if isinstance(item, list):
            q = q + flatten(item)
        else:
            q.append(item)

    return q
