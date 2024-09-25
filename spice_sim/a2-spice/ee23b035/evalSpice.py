import os

from enum import Enum, auto
from io import TextIOWrapper
from dataclasses import dataclass
from collections import defaultdict
from typing import List, Dict, Tuple, Set

import numpy as np

TOL = 1e-200


class ElementType(Enum):
    """
    Enum class to store element type -
    Voltage/Current source, or Resistor
    """

    V = auto()
    I = auto()
    R = auto()


@dataclass
class Element:
    """
    Element dataclass to store connection information and value

    Args:
        name: Name of the element
        element_type: Enum denoting element type
        value:  Resistance/Source value
        node_1: First node connection
        node_2: Second node connection
    """

    name: str
    element_type: ElementType
    value: int
    node_1: str
    node_2: str


# Dictionary to store parsing formats for different elements
# Mapping of Element -> (Mapping of Parameter -> Token Index)
PARAMETER_ORDERING = {
    "R": {"name": 0, "value": 3, "node_1": 1, "node_2": 2},
    "V": {"name": 0, "value": 4, "node_1": 1, "node_2": 2, "source_type": 3},
    "I": {"name": 0, "value": 4, "node_1": 1, "node_2": 2, "source_type": 3},
}


class Circuit:
    """
    Circuit class to simulate a given circuit file

    Attributes:
        nodes_set (Set[str]): Set of all nodes
        nodes (Dict[str, int]): Dictionary mapping nodes to unique integer indexes

        voltage_sources (Dict[str, Tuple[Element, int]]): Dictionary mapping voltage source names
            to the Element object and unique integer index
        current_sources (Dict[str, Element]): Dictionary mapping current source names to Element object
        passive_elements (Dict[str, Element]): Dictionary mapping resistor names to Element object

        gnd_idx (int): Unique index for the GND node

        eqns (np.array): Matrix containing circuit equations
        voltage_solns (Dict[str, float]): Dictionary mapping nodes to their voltages
        current_solns (Dict[str, float]): Dictionary mapping voltage sources to their branch currents

        num_ac_sources (int): Number of AC sources present in the circuit
        num_dc_sources (int): Number of DC sources present in the circuit
    """

    def __init__(self) -> None:
        """Initialise matrix."""
        self.nodes_set: Set = set()
        self.nodes: Dict[str, int] = dict()

        self.voltage_sources: Dict[str, Tuple[Element, int]] = dict()
        self.current_sources: Dict[str, Element] = dict()
        self.passive_elements: Dict[str, Element] = dict()
        self.gnd_idx = -1

        self.eqns = np.zeros((0, 0))
        self.voltage_solns: Dict[str, float] = dict()
        self.current_solns: Dict[str, float] = dict()

        self.num_ac_sources: int = 0
        self.num_dc_sources: int = 0

    @property
    def num_voltage_sources(self) -> int:
        """Number of voltage sources"""
        return len(self.voltage_sources)

    @property
    def num_current_sources(self) -> int:
        """Number of current sources"""
        return len(self.current_sources)

    @property
    def num_resistors(self) -> int:
        """Number of passive elements"""
        return len(self.passive_elements)

    @property
    def num_nodes(self) -> int:
        """Number of nodes"""
        return len(self.nodes)

    @property
    def num_eqns(self) -> int:
        """Number of equations to write"""
        return self.num_nodes + self.num_voltage_sources

    def add_element(
        self,
        name: str,
        element_type: ElementType,
        value: str,
        node_1: str,
        node_2: str,
        source_type=None,
    ) -> None:
        """
        Add an element to the circuit.

        Args:
            name (str): Name of the element
            element_type (ElementType): Enum specifying the element type
            value (str): Raw (string) value for the element
            node_1 (str): Name of the first node to which a connection is to be made
            node_2 (str): Name of the second node to which a connection is to be made

        Raises:
            ValueError if the element does not have a numerical value
            ValueError if the element has a name that is already used
            ValueError if a 0 valued resistance is provided
        """
        try:
            float(value)
        except ValueError:
            # The element value cannot be parsed into a float
            raise ValueError("Malformed circuit file")

        if any(
            name in elements_dict
            for elements_dict in (
                self.passive_elements,
                self.voltage_sources,
                self.current_sources,
            )
        ):
            # Element name has been repeated
            raise ValueError("Malformed circuit file")

        self.nodes_set.add(node_1)
        self.nodes_set.add(node_2)
        element = Element(name, element_type, float(value), node_1, node_2)

        # Update the elements dicts
        if element_type == ElementType.R:
            if abs(element.value) <= TOL:
                raise ValueError("Circuit error: 0 valued resistance")
            else:
                self.passive_elements[name] = element
        elif element_type == ElementType.V:
            self.voltage_sources[name] = (element, self.num_voltage_sources)
        else:
            self.current_sources[name] = element

    def read_circuit(self, circuit_file: TextIOWrapper) -> None:
        """
        Parse the circuit file

        Args:
            circuit_file (TextIOWrapper): File object to read from

        Raises:
            ValueError if the circuit is not started with .circuit
            ValueError if the circuit is not ended with .end
            ValueError if an element other than V, I, R is provided
            ValueError if a GND node is not provided
            ValueError if an element does not have parameters provided in the correct format
            ValueError if a source is not of type ac or dc
            ValueError if the circuit contains both ac and dc sources
        """
        start_circuit = False

        for line in circuit_file:
            line = line.strip()

            if line == ".circuit":
                # Start reading circuit
                start_circuit = True

            elif line == ".end":
                if start_circuit:
                    break
                else:
                    # Circuit was never started
                    raise ValueError("Malformed circuit file")

            elif start_circuit and line:
                # Remove comments and generate tokens
                tokens = line.split("#")[0].strip().split()

                if tokens[0][0] not in PARAMETER_ORDERING:
                    # Invalid element
                    raise ValueError("Only V, I, R elements are permitted")

                # Parse tokens
                try:
                    params = {
                        key: tokens[idx]
                        for key, idx in PARAMETER_ORDERING[tokens[0][0]].items()
                    }
                except:
                    # Parameters are not provided correctly
                    raise ValueError("Malformed circuit file")

                if params["name"][0] in ("V", "I"):
                    if params["source_type"] not in ("ac", "dc"):
                        raise ValueError("Malformed circuit file")
                    elif params["source_type"] == "ac":
                        self.num_ac_sources += 1
                    else:
                        self.num_dc_sources += 1

                self.add_element(element_type=ElementType[params["name"][0]], **params)
        else:
            # Circuit was never ended
            raise ValueError("Malformed circuit file")

        if all([self.num_ac_sources, self.num_dc_sources]):
            raise ValueError("Circuit error: mixed AC and DC sources")

        # Read all nodes and generate unique indexes
        for idx, node in enumerate(self.nodes_set):
            self.nodes[node] = idx

        # Store the ground node index
        self.gnd_idx = self.nodes.get("GND", -1)
        if self.gnd_idx == -1:
            # There is no GND node
            raise ValueError("Malformed circuit file")

    def generate_eqns(self) -> None:
        """
        Generate the equations to solve in an augmented matrix.

         - For all resistors, a conductance matrix is generated.
         - The currents through the current sources are added into the last
           column of the augmented matrix.
         - The voltage sources are assumed to have an unknown current
           through them. This is factored into the equations at each node.
         - The voltage difference across the source is treated as another equation.
        """
        self.eqns = np.zeros((self.num_eqns, self.num_eqns + 1), dtype=np.float64)

        # Conductance matrix:
        # a_ij = -1/R_ij for i != j
        # a_ii = sum(1/R_ij) over all j
        for element in self.passive_elements.values():
            node_1_idx = self.nodes[element.node_1]
            node_2_idx = self.nodes[element.node_2]

            conductance = 1.0 / element.value

            self.eqns[node_1_idx][node_1_idx] += conductance
            self.eqns[node_1_idx][node_2_idx] -= conductance
            self.eqns[node_2_idx][node_1_idx] -= conductance
            self.eqns[node_2_idx][node_2_idx] += conductance

        # Current column in the augmented matrix:
        # Incoming current -> +ve
        # Outgoing current -> -ve
        # Current flows from node_1 to node_2
        for element in self.current_sources.values():
            node_1_idx = self.nodes[element.node_1]
            node_2_idx = self.nodes[element.node_2]

            self.eqns[node_1_idx][-1] -= element.value
            self.eqns[node_2_idx][-1] += element.value

        # Voltage source eqns in the matrix:
        # We take current through the branch to be another variable
        # and add it in the KCL eqns
        # For the equation corresponding to that unknown current in the matrix
        # We write the difference of voltages at the two nodes to be equal
        # to the voltage source's value
        for element, voltage_idx in self.voltage_sources.values():
            node_1_idx = self.nodes[element.node_1]
            node_2_idx = self.nodes[element.node_2]

            # V_n1 - V_n2 = element.value
            self.eqns[self.num_nodes + voltage_idx][node_1_idx] = 1.0
            self.eqns[self.num_nodes + voltage_idx][node_2_idx] = -1.0
            self.eqns[self.num_nodes + voltage_idx][-1] = element.value

            # Add current coefficient into the eqns
            # Current flows from node_2 to node_1
            self.eqns[node_1_idx][self.num_nodes + voltage_idx] = 1.0
            self.eqns[node_2_idx][self.num_nodes + voltage_idx] = -1.0

        # GND node equation:
        # 1 x V_GND = 0
        self.eqns[self.gnd_idx] = np.zeros((self.num_eqns + 1,))
        self.eqns[self.gnd_idx][self.gnd_idx] = 1

    def solve(self) -> None:
        """
        Solve the eqn matrix, and parse the solutions.
        Store them in the voltage_solns and current_solns.

        Raises:
            ValueError: If the circuit cannot be solved
        """
        A = self.eqns[:, :-1]
        B = self.eqns[:, -1]

        # If the determinant is 0, then the matrix is singular and can't be solved
        if abs(np.linalg.det(A)) <= TOL:
            raise ValueError("Circuit error: no solution")

        solns = np.linalg.inv(A) @ B

        self.voltage_solns = {node: solns[idx] for node, idx in self.nodes.items()}

        self.current_solns = {
            element.name: solns[self.num_nodes + idx]
            for element, idx in self.voltage_sources.values()
        }


def evalSpice(filename: str):
    """
    Given a circuit file, parse it and solve for the voltage at each node
    and the current in each branch.

    Args:
        filename (str): Circuit file

    Raises:
        FileNotFoundError if the circuit file does not exist
    """
    if not os.path.exists(filename):
        raise FileNotFoundError("Please give the name of a valid SPICE file as input")

    circuit = Circuit()

    with open(filename, "r") as circuit_file:
        circuit.read_circuit(circuit_file)

    circuit.generate_eqns()
    circuit.solve()

    return (circuit.voltage_solns, circuit.current_solns)


if __name__ == "__main__":
    print(evalSpice("testing.ckt"))
