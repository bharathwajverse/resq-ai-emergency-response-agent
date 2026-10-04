def resolve(clause1, clause2):
    c1 = set(clause1)
    c2 = set(clause2)
    for lit in c1:
        neg = f"~{lit}" if not lit.startswith("~") else lit[1:]
        if neg in c2:
            resolvent = (c1 - {lit}) | (c2 - {neg})
            return list(resolvent)
    return None

def demonstrate_resolution():
    c1 = ["A", "B"]
    c2 = ["~B", "C"]
    res = resolve(c1, c2)
    return {"clause1": c1, "clause2": c2, "resolvent": res}
