"""Turn the full exported weapon KeyValues into JSON, retaining raw values."""
import re
import csv
from extract_sources import LIBRARY, write_json


def parse(text):
    token = re.compile(r'\s+|//[^\n]*|"((?:\\.|[^"\\])*)"|([{}])')
    tokens, pos = [], 0
    while pos < len(text):
        match = token.match(text, pos)
        if not match:
            raise ValueError(f"Unrecognized KeyValues at {pos}: {text[pos:pos + 40]!r}")
        if match.group(1) is not None:
            tokens.append(match.group(1).replace('\\"', '"').replace('\\\\', '\\'))
        elif match.group(2):
            tokens.append(match.group(2))
        pos = match.end()
    pos = 0

    def obj(nested=False):
        nonlocal pos
        result = {}
        while pos < len(tokens):
            key = tokens[pos]
            pos += 1
            if key == "}":
                assert nested
                return result
            assert pos < len(tokens)
            value = tokens[pos]
            pos += 1
            if value == "{":
                value = obj(True)
            # These files genuinely repeat pattern names. Preserve every value;
            # JSON arrays represent repeated KeyValues keys, never overwrite.
            if key in result:
                if not isinstance(result[key], list):
                    result[key] = [result[key]]
                result[key].append(value)
            else:
                result[key] = value
        assert not nested, "Unclosed KeyValues object"
        return result

    return obj()


if __name__ == "__main__":
    definitions = {}
    for path in sorted((LIBRARY / "assets/weapon").glob("*.txt")):
        definitions[path.stem] = dict(source=path.relative_to(LIBRARY).as_posix(), data=parse(path.read_text()))
    write_json(LIBRARY / "evidence/weapon_definitions.json", definitions)
    print(f"Parsed {len(definitions)} complete definitions, including nested mods/attachments")
    rows = list(csv.DictReader((LIBRARY / "evidence/common_assets.csv").open(encoding="utf-8-sig")))
    dependencies = {r[0]: r[1:] for r in csv.reader(
        (LIBRARY / "evidence/common_dependencies.csv").open(encoding="utf-8-sig")) if r}
    names = {r["asset_name"]: r for r in rows}
    queue = [r["asset_name"] for r in rows if any(w in r["asset_name"].lower()
        for w in ("r99", "r97", "peacekeeper", "energy_shotgun"))]
    seen = set()
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        queue.extend(dependencies.get(name, []))
    write_json(LIBRARY / "evidence/weapon_dependency_closure.json", [
        dict(names.get(n, dict(asset_name=n, type="unresolved")), dependencies=dependencies.get(n, []))
        for n in sorted(seen)])
