import os
from enum import Enum, auto
from io import TextIOWrapper
from typing import List, Dict
from dataclasses import dataclass
from collections import defaultdict

import numpy as np

class ElementType(Enum):
    V = auto()
    I = auto()
    R = auto()


@dataclass
class Element:
    name: str
    element_type: ElementType
    value: int
    node_1: str
    node_2: str


PARAMETER_ORDERING = {
    "R": {
        "name": 0,
        "value": 3,
        "node_1": 1,
        "node_2": 2
    },
    "V": {
        "name": 0,
        "value": 4,
        "node_1": 1,
        "node_2": 2
    },
    "I": {
        "name": 0,
        "value": 4,
        "node_1": 1,
        "node_2": 2
    }
}


class Circuit():
    def __init__(self) -> None:
        self.graph: Dict[str, Dict[str, str]] = defaultdict(dict)
        self.nodes: Dict[str, int] = dict()

        self.voltage_sources: Dict[str, Element] = dict()
        self.current_sources: Dict[str, Element] = dict()
        self.passive_elements: Dict[str, Element] = dict()

        self.eqns = np.zeros((0, 0))

    @property
    def num_voltage_sources(self):
        return len(self.voltage_sources)

    @property
    def num_current_sources(self):
        return len(self.current_sources)

    @property
    def num_resistors(self):
        return len(self.passive_elements)

    @property
    def num_eqns(self):
        return len(self.nodes)


    def add_element(self, name: str, element_type: ElementType, value: str, node_1: str, node_2: str) -> None:
        element = Element(name, element_type, float(value), node_1, node_2)
        self.graph[node_1][node_2] = name
        self.graph[node_2][node_1] = name

        if element_type == ElementType.R:
            self.passive_elements[name] = element
        elif element_type == ElementType.V:
            self.voltage_sources[name] = element
        else:
            self.current_sources[name] = element


    def read_circuit(self, circuit_file: TextIOWrapper) -> None:
        start_circuit = False

        for line in circuit_file:
            line = line.strip()

            if line == ".circuit":
                start_circuit = True
            elif line == ".end":
                if start_circuit:
                    break
                else:
                    raise ValueError("Circuit was never started!")
            elif start_circuit and line:
                tokens = line.split()
                params = {key: tokens[idx] for key, idx in PARAMETER_ORDERING[tokens[0][0]].items()}
                self.add_element(element_type=ElementType[params["name"][0]], **params)
        else:
            raise ValueError("Circuit was never ended!")

        for idx, node in enumerate(self.graph):
            self.nodes[node] = idx;

        if self.nodes["GND"] != 0:
            for node, idx in self.nodes.items():
                if idx == 0:
                    self.nodes[node] = self.nodes["GND"]
                    self.nodes["GND"] = 0
                    break


    def generate_eqns(self) -> None:
        eqns_copy = np.zeros((self.num_eqns + 1, self.num_eqns + 1))

        for idx, el_name in enumerate(self.passive_elements):
            element = self.passive_elements[el_name]
            node_1_idx = self.nodes[element.node_1]
            node_2_idx = self.nodes[element.node_2]

            eqns_copy[node_1_idx][node_1_idx] += 1. / element.value
            eqns_copy[node_1_idx][node_2_idx] -= 1. / element.value
            eqns_copy[node_2_idx][node_1_idx] -= 1. / element.value
            eqns_copy[node_2_idx][node_2_idx] += 1. / element.value

        for idx, el_name in enumerate(self.current_sources):
            element = self.current_sources[el_name]
            node_1_idx = self.nodes[element.node_1]
            node_2_idx = self.nodes[element.node_2]

            eqns_copy[node_1_idx][-1] -= element.value
            eqns_copy[node_2_idx][-1] += element.value

        self.eqns = eqns_copy

        self.supernodes = {i:set([i]) for i in self.nodes.keys()}
        print(self.supernodes)

        for el_name, element in self.voltage_sources.items():
            for node, grouping in self.supernodes.items():
                if element.node_1 in grouping and element.node_2 in grouping:
                    raise ValueError()
                elif element.node_1 in grouping:
                    self.add_supernode_eqns(node, element.node_1, element.node_2, element.value)
                    break
                elif element.node_2 in grouping:
                    self.add_supernode_eqns(node, node_2, node_1, -element.value)
                    break
            else:
                self.add_supernode_eqns(element.node_1, element.node_1, element.node_2, -element.value)

        print(self.supernodes, self.nodes)
        self.eqns[-1][0] = 1
        
    def add_supernode_eqns(self, supernode: str, node_1: str, node_2: str, voltage: float):
        self.supernodes[supernode] |= self.supernodes[node_2]
        del self.supernodes[node_2]

        print(supernode, node_1, node_2)
        
        supernode_idx = self.nodes[supernode]
        node_1_idx = self.nodes[node_1]
        node_2_idx = self.nodes[node_2]

        self.eqns[supernode_idx] = self.eqns[supernode_idx] + self.eqns[node_2_idx]
        self.eqns[node_2_idx] = 0
        self.eqns[node_2_idx][node_1_idx] = 1
        self.eqns[node_2_idx][node_2_idx] = -1
        self.eqns[node_2_idx][-1] = voltage


def evalSpice(filename: str):
    if not os.path.exists(filename):
        raise FileNotFoundError("Please give the name of a valid SPICE file as input")

    circuit = Circuit()

    with open(filename, "r") as circuit_file:
        circuit.read_circuit(circuit_file)

    circuit.generate_eqns()
    print(circuit.eqns, circuit.nodes)
    solve = lambda A, b: np.linalg.lstsq(A, b)
    print(solve(circuit.eqns[:,:-1], circuit.eqns[:,-1]))

    return ({}, {})


if __name__ == "__main__":
    evalSpice("testing.ckt")
