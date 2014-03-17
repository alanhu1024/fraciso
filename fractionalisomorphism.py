# Copyright 2014 Jeffrey Finkelstein.
#
# This file is part of fractionalisomorphism.
#
# fractionalisomorphism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# fractionalisomorphism is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# fractionalisomorphism.  If not, see <http://www.gnu.org/licenses/>.
"""Algorithms for determining if two graphs are fractionally isomorphic.

Example usage::

    from fractionalisomorphism import Graph
    from fractionalisomorphism import are_fractionally_isomorphic

    # Create a graph G.
    vertices = {1, 2, 3}
    edges = {frozenset(1, 2), frozenset(2, 3), frozenset(3, 1)}
    G = Graph(vertices, edges)

    # Create a graph H.
    #H = ...

    # Determine if they are fractionally isomorphic.
    if are_fractionally_isomorphic(G, H):
        print('Yes')
    else:
        print('No')

"""
from collections import namedtuple
from functools import reduce
from itertools import combinations
from itertools import groupby
from itertools import permutations
from itertools import product

__all__ = ['Graph', 'are_fractionally_isomorphic']


def peek(s):
    """Returns but does not remove an arbitrary element from the specified set.

    """
    return next(iter(s))


def union(*sets):
    """Returns the union of all sets given as positional arguments."""
    # The last argument to reduce is the initializer used in the case of an
    # empty sequence of sets.
    #
    # This is essentially the same as ``sets[0].union(*sets[1:])``, but it
    # works even if `sets` is not a list and if `sets` has only one element.
    return reduce(lambda S, T: S | T, sets, {})


def are_pairwise_disjoint(*sets):
    """Returns ``True`` if and only if each pair of sets is disjoint."""
    return all(S.isdisjoint(T) for S, T in combinations(sets, 2))


def is_valid_partition(graph, partition):
    """Returns ``True`` if and only if the specified partition is a valid
    partition of the vertices of `graph`.

    A partition is valid if the set of vertices of the graph equals the
    disjoint union of the blocks in the partition.

    """
    return are_pairwise_disjoint(*partition) and union(*partition) == graph.V \
        and all(len(block) > 0 for block in partition)


def neighbors(graph, v, block=None):
    """Returns the neighbors of vertex v in the specified graph.

    If `block` is a set of vertices in the given graph, this function returns
    only the neighbors of v in the specified block. Otherwise, it returns all
    neighbors of v in the specified graph.

    """
    if block is None:
        block = graph.V
    return {w for w in block if frozenset((v, w)) in graph.E}


def is_block_equitable(graph, partition, block):
    """Returns ``True`` if and only if the specified block of the given
    partition is equitable.

    `graph` must be an instance of :data:`Graph`.

    `partition` is a set of sets. Each inner set, a **block**, is a set of
    vertices in the graph.

    `block` must be an element of `partition`. This block will be checked for
    equitability.

    A block is **equitable** if for each two vertices v and w in the block, the
    number of neighbors of v in block B equals the number of neighbors of w in
    block B, for all blocks B.

    """
    return all(len(neighbors(graph, v, B)) == len(neighbors(graph, w, B))
               for v, w in product(block, block) for B in partition)


def is_partition_equitable(graph, partition):
    """Returns ``True`` if and only if the specified partition is an equitable
    partition of the graph.

    `graph` must be an instance of :data:`Graph`.

    `partition` is a set of sets. Each inner set, a **block**, is a set of
    vertices in the graph.

    A partition is **equitable** if for each block P1 and for each two vertices
    v and w in P1, the number of neighbors of v in block P2 equals the number
    of neighbors of w in block P2, for all blocks P2.

    """
    return all(is_block_equitable(graph, partition, block)
               for block in partition)


def _adapt(graph, partition):
    """Adapt the specified equitable partition into the coarsest equitable one.

    `graph` must be an instance of :data:`Graph`.

    `partition` is a set of blocks, each of which is a :class:`frozenset` of
    vertices from the graph.

    """
    # First, for each vertex, compute the number of neighbors of that vertex in
    # each block (including its own).
    block_neighbors = {v: {block: len(neighbors(graph, v, block))
                           for block in partition}
                       for v in graph.V}
    # Second, partition all vertices into new blocks consisting of vertices
    # that have the same dictionary of block neighbors as computed above.
    #
    # We do this by first sorting all the vertices according to their block
    # neighbors dictionary, then grouping together the vertices that have the
    # same block neighbors dictionary. However, since dictionaries cannot be
    # used as sort keys (because they are not comparable), we use the sorted
    # list of key/value pairs. Even more annoying, the keys in these key/value
    # pairs are themselves sets, which must be converted to sorted lists
    # (because the default comparison on sets in Python is the "is subset"
    # comparison).
    #
    # This is quite an inefficient algorithm for doing this, but the reward is
    # readability to match the mathematical description of the algorithm more
    # closely.
    key_func = lambda w: sorted((sorted(k), v)
                                for k, v in block_neighbors[w].items())
    vertices = sorted(block_neighbors, key=key_func)
    # Next, we simply group the vertices according to ones that have the same
    # block neighbors dictionary.
    new_partition = {frozenset(g) for k, g in groupby(vertices, key_func)}

    # Do a sanity check...
    #assert is_valid_partition(new_partition)

    # If this process produced exactly the same partition, then we have reached
    # the base case of the recursion.
    if new_partition == partition:
        return partition
    return _adapt(graph, new_partition)


def coarsest_equitable_partition(graph):
    """Returns the coarsest equitable partition of the specified graph.

    `graph` must be an instance of :data:`Graph`.

    A partition is a set of sets. Each of the inner sets is a
    :class:`frozenset` of vertices in the graph.

    A partition is **equitable** if for each block P1 and for each two vertices
    v and w in P1, the number of neighbors of v in block P2 equals the number
    of neighbors of w in block P2, for all blocks P2.

    A partition P1 is coarser than partition P2 if each block of P2 is a subset
    of a block of P1. A partition is a coarsest equitable partition if it is
    equitable and no coarser partition is equitable.

    """
    # Start with the partition that consists of a single block containing the
    # entire vertex set. Recursively adapt the partition until no further
    # adaptations are possible. This is guaranteed to be the coarsest equitable
    # partition.
    return _adapt(graph, {graph.V})


# def partition_parameters(graph, partition):
#     """Returns the parameters of the given partition.

#     `graph` must be an instance of :data:`Graph`.

#     `partition` must be a valid equitable partition of the specified graph.

#     The parameters of the graph are a list of size **p** and a matrix (a list
#     of lists) of size **p** by **p**, where **p** is the number of blocks in
#     the partition. The entry at index **i** in the list is the number of
#     vertices in the **i**th block of the partition. The entry at row **i**,
#     column **j** of the matrix is the number of neighbors in block **j** of
#     any fixed vertex in block **i** (since the partition is equitable, it
#     doesn't matter which particular vertex we consider).

#     """
#     # This ensures that every list comprehension iterates over the blocks in
#     # the same order.
#     partition_as_list = list(partition)
#     # pre-condition: each block is regular
#     vertices_per_block = [len(block) for block in partition_as_list]
#     # TODO this will raise an error if a block is empty
#     block_neighbors = [[len(neighbors(graph, block_i[0], block_j))
#                         for block_j in partition_as_list]
#                        for block_i in partition_as_list]
#     return vertices_per_block, block_neighbors


def partition_parameters(graph, partition):
    """Returns the parameters of the given partition.

    `graph` must be an instance of :data:`Graph`.

    `partition` must be a valid equitable partition of the specified graph.

    The parameters of the graph are two dictionaries. The first dictionary is a
    mapping from a block of the partition to the number of vertices in that
    block. The second dictionary is a two-dimensional dictionary. Both keys are
    blocks of the partition. The entry indexed by blocks **i** and **j** is the
    number of neighbors in block **j** of any fixed vertex in block **i** (the
    particular vertex doesn't matter, since the partition is equitable).

    """
    vertices_per_partition = {block: len(block) for block in partition}
    block_neighbors = {b_i: {b_j: len(neighbors(graph, peek(b_i), b_j))
                             for b_j in partition}
                       for b_i in partition}
    return vertices_per_partition, block_neighbors


def lexicographic_blocks(dictionary):
    """Sorts the key/value pairs of `dictionary` according to the lexicographic
    order of the keys.

    This is useful if your keys are instances of :class:`set` and you wish them
    to be ordered according to their list representation instead of ordered
    according to inclusion.

    """
    return sorted(dictionary.items(), key=lambda item: sorted(item[0]))


def _as_list(sizes):
    """Converts the given dictionary to a list.

    The dictionary `sizes` maps blocks of a partition to number of vertices in
    that partition. Each element of the returned list is the number of vertices
    in a block of the partition. The list is sorted according to the
    lexicographic ordering of the blocks.

    """
    return [size for block, size in lexicographic_blocks(sizes)]


def _as_matrix(block_neighbors):
    """Converts the given dictionary to a matrix.

    The two-dimensional dictionary `block_neighbors` is indexed in each
    dimension by blocks of a partition. The entry at row **i**, column **j** is
    an integer representing the number of neighbors in block **j** of any fixed
    vertex in block **i**. Each row and each column of the matrix is sorted
    according to lexicographic order of the blocks.

    """
    return Matrix([[num for block_j, num in lexicographic_blocks(d)]
                   for block_i, d in lexicographic_blocks(block_neighbors)])


def identity_matrix(n):
    """Returns the identity matrix of size n."""
    return Matrix([[1 if i == j else 0 for j in range(n)] for i in range(n)])


def permutation_matrices(n):
    """Returns an iterator over all possible permutation matrices of size n.

    """
    return (Matrix(P) for P in permutations(identity_matrix(n)))


def are_common_partitions(graph1, partition1, graph2, partition2):
    """Returns ``True`` if and only if the two partitions have the same
    parameters (or a permutation of the same parameters).

    `graph1` and `graph2` must be instances of :data:`Graph`.

    `partition1` and `partition2` must be valid equitable partitions of the
    corresponding graphs.

    The partition parameters are described in the documentation for
    :func:`partition_parameters`. The parameters include one vector and one
    matrix. This function returns ``True`` exactly when there is some
    permutation such that both the vector and the matrix of `partition1` equal
    the vector and the matrix of `partition2`.

    """
    sizes1, block_neighbors1 = partition_parameters(graph1, partition1)
    sizes2, block_neighbors2 = partition_parameters(graph2, partition2)
    # Convert `sizes` into a list of length p and `block_neighbors` into a
    # matrix of size p by p, where p is the number of blocks in the
    # partitions. The innermost entries of both should be integers.
    sizes1 = _as_list(sizes1)
    sizes2 = _as_list(sizes2)
    neighbors1 = _as_matrix(block_neighbors1)
    neighbors2 = _as_matrix(block_neighbors2)
    # Return true if there is any permutation that makes these two pairs equal.
    match = lambda P: sizes1 == P * sizes2 and neighbors1 == P * neighbors2
    return any(match(P) for P in permutation_matrices(len(sizes1)))


def are_fractionally_isomorphic(G, H):
    """Returns ``True`` if and only if the graphs are fractionally isomorphic.

    """
    partition1 = coarsest_equitable_partition(G)
    partition2 = coarsest_equitable_partition(H)
    return are_common_partitions(G, partition1, H, partition2)


#: A graph consisting of a set of vertices and a set of edges.
#:
#: The vertex and edge sets must be instances of :class:`frozenset`.
#: Each edge must be a :class:`frozenset` containing exactly two elements from
#: the set of vertices. For example, to create the circle graph on three
#: vertices::
#:
#:     fs = frozenset
#:     vertices = fs({1, 2, 3})
#:     edges = fs({fs({1, 2}), fs({2, 3}), fs({3, 1})})
#:     G = Graph(vertices, edges)
#:
Graph = namedtuple('Graph', ['V', 'E'])


def graph_from_file(filename):
    """Reads an adjacency matrix from a file and returns an instance of
    :data:`Graph`.

    The adjacency matrix must have entries separated by a space and rows
    separated by a newline.

    """
    with open(filename, 'r') as f:
        adjacency = [[int(b) for b in line.strip().split()]
                     for line in f.readlines()]
    # Convert the adjacency matrix to sets of vertices and edges.
    vertices = frozenset(range(len(adjacency)))
    # We can use combinations since we're considering only undirected graphs.
    edges = frozenset({frozenset((u, v)) for u, v in combinations(vertices, 2)
                       if adjacency[u][v] == 1})
    return Graph(vertices, edges)


class Matrix(object):

    def __init__(self, entries):
        self.entries = entries
        self.size = len(entries)

    def __getitem__(self, key):
        return self.entries[key]

    def __eq__(A, B):
        n = A.size
        return all(A[i][j] == B[i][j] for i, j in product(range(n), repeat=2))

    def __mul__(A, B):
        n = A.size
        if isinstance(B, Matrix):
            return Matrix([[sum(A[i][k] * B[k][j] for k in range(n))
                            for j in range(n)] for i in range(n)])
        if isinstance(B, list):
            return [sum(A[i][k] * B[k] for k in range(n)) for i in range(n)]
        raise TypeError('must multiply by Matrix or list')
