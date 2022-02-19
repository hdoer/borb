import typing

from borb.io.read.types import Dictionary, Name, List, String


class NameTree:
    def __init__(self, document: Dictionary, name: Name):
        self._document: Dictionary = document
        self._name: Name = name

    def put(self, key: str, value: typing.Any):

        assert "XRef" in self._document
        assert "Trailer" in self._document["XRef"]
        assert "Root" in self._document["XRef"]["Trailer"]
        root = self._document["XRef"]["Trailer"]["Root"]

        # set up /Names dictionary
        if "Names" not in root:
            root[Name("Names")] = Dictionary()
        names = root["Names"]

        # set up /JavaScript
        if self._name not in names:
            names[self._name] = Dictionary()
            names[self._name][Name("Kids")] = List()

        # find parent
        parent = names[self._name]
        while "Kids" in parent:
            for k in parent["Kids"]:
                lower_limit = str(k["Limits"][0])
                upper_limit = str(k["Limits"][1])
                if lower_limit == upper_limit:
                    continue
                if lower_limit < key < upper_limit:
                    parent = k
                    break
            break

        # insert as new child, or replace existing child?
        if (
            len([x for x in parent["Kids"] if x["Limits"][0] == x["Limits"][1] == key])
            == 0
        ):
            self._put_new(parent, key, value)
        else:
            self._put_existing(parent, key, value)

    def _put_new(self, parent: Dictionary, key: str, value: typing.Any):

        kid = Dictionary()
        kid[Name("F")] = String(key)
        kid[Name("Limits")] = List()
        for _ in range(0, 2):
            kid["Limits"].append(String(key))
        kid[Name("Names")] = List()
        kid[Name("Names")].append(String(key))

        # build leaf /Filespec dictionary
        if self._name == "EmbeddedFiles":
            kid[Name("Names")].append(value)
            kid[Name("Type")] = Name("EF")

        # build leaf /JavaScript dictionary
        if self._name == "JavaScript":
            kid[Name("Names")].append(value)

        # append
        parent["Kids"].append(kid)

    def _put_existing(self, parent: Dictionary, key: str, value: typing.Any):
        pass

    #
    # dictionary methods
    #

    def get_keys(self) -> typing.List[String]:
        return [k for k, v in self.items()]

    def get_values(self) -> typing.List[typing.Any]:
        return [v for k, v in self.items()]

    def items(self) -> typing.Iterable[typing.Tuple[String, typing.Any]]:

        assert "XRef" in self._document
        assert "Trailer" in self._document["XRef"]
        assert "Root" in self._document["XRef"]["Trailer"]
        root = self._document["XRef"]["Trailer"]["Root"]

        # set up /Names dictionary
        if "Names" not in root:
            root[Name("Names")] = Dictionary()
        names = root["Names"]

        nodes_to_visit = [names[self._name]]
        keys = []
        values = []
        while len(nodes_to_visit) > 0:
            n = nodes_to_visit[0]
            nodes_to_visit.pop(0)
            if "Kids" in n:
                for k in n["Kids"]:
                    nodes_to_visit.append(k)
            if "Limits" in n:
                lower_limit = str(n["Limits"][0])
                upper_limit = str(n["Limits"][1])
                if upper_limit == lower_limit:
                    keys.append(upper_limit)
                    values.append(n["Names"][1])

        # return
        return zip(keys, values)

    #
    # utility functions
    #

    def _get_root_or_empty(self):
        assert "XRef" in self._document
        assert "Trailer" in self._document["XRef"]
        assert "Root" in self._document["XRef"]["Trailer"]
        root = self._document["XRef"]["Trailer"]["Root"]
        return root.get(Name("Names"), Dictionary())

    def __len__(self):
        return len(self._get_root_or_empty())
