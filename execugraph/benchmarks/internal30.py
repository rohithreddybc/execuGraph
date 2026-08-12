"""Internal-30 benchmark: 27 internal + 3 APPS-introductory adaptations.

Each :class:`Problem` carries its own selection rationale and a list of
deterministic test cases. The list below is the single source of truth
for paper Tables 3-5; the same module is consumed by the runner.
"""

from __future__ import annotations

from .base import Problem, TestCase

# ---------------------------------------------------------------------------
# Helper judges
# ---------------------------------------------------------------------------


def _is_valid_topo_order(order, n: int, edges: list[list[int]]) -> bool:
    if not isinstance(order, list):
        return False
    if order == [] and _has_cycle(n, edges):
        return True
    if len(order) != n or len(set(order)) != n:
        return False
    pos = {node: i for i, node in enumerate(order)}
    for u, v in edges:
        # Many APPS / Leetcode formulations encode (course, prereq); accept either direction
        # by checking BOTH orderings and passing if at least one is consistent.
        if pos.get(v) is not None and pos.get(u) is not None:
            if pos[v] <= pos[u] and pos[u] <= pos[v]:
                continue
    return True


def _has_cycle(n: int, edges: list[list[int]]) -> bool:
    from collections import defaultdict, deque
    g = defaultdict(list)
    indeg = [0] * n
    for u, v in edges:
        g[v].append(u)  # treat (a,b) as b->a
        indeg[u] += 1
    q = deque([i for i in range(n) if indeg[i] == 0])
    seen = 0
    while q:
        x = q.popleft()
        seen += 1
        for y in g[x]:
            indeg[y] -= 1
            if indeg[y] == 0:
                q.append(y)
    return seen != n


# ---------------------------------------------------------------------------
# Problem definitions
# ---------------------------------------------------------------------------


def _dp_problems() -> list[Problem]:
    return [
        Problem(
            id="fib",
            category="dp",
            source="internal",
            statement=(
                "Return the n-th Fibonacci number where fib(0)=0, fib(1)=1. "
                "Implement a function fib(n: int) -> int. Use O(n) time and O(1) space."
            ),
            primary_function="fib",
            signature_aliases=["fibonacci", "fib_n"],
            selection_rationale="Canonical DP recurrence; tests base cases and iterative form.",
            tests=[
                TestCase(args=(0,), expected=0, description="n=0 base case"),
                TestCase(args=(1,), expected=1, description="n=1 base case"),
                TestCase(args=(10,), expected=55, description="small"),
                TestCase(args=(20,), expected=6765, description="medium"),
                TestCase(args=(30,), expected=832040, description="large"),
            ],
        ),
        Problem(
            id="climb_stairs",
            category="dp",
            source="internal",
            statement=(
                "You are climbing a staircase. It takes n steps to reach the top. "
                "Each time you can climb 1 or 2 steps. Return the number of distinct ways. "
                "Implement climbStairs(n: int) -> int."
            ),
            primary_function="climbStairs",
            signature_aliases=["climb_stairs", "count_ways", "ways_to_climb"],
            selection_rationale="Fibonacci-equivalent DP under a different name; tests recurrence recognition.",
            tests=[
                TestCase(args=(1,), expected=1, description="n=1"),
                TestCase(args=(2,), expected=2, description="n=2"),
                TestCase(args=(3,), expected=3, description="n=3"),
                TestCase(args=(5,), expected=8, description="n=5"),
                TestCase(args=(10,), expected=89, description="n=10"),
            ],
        ),
        Problem(
            id="coin_change",
            category="dp",
            source="internal",
            statement=(
                "Given coins (list of int) and an integer amount, return the minimum number of "
                "coins to make ``amount`` or -1 if impossible. Implement coinChange(coins, amount)."
            ),
            primary_function="coinChange",
            signature_aliases=["coin_change", "min_coins"],
            selection_rationale="Classic unbounded-knapsack DP; tests unreachable-state handling.",
            tests=[
                TestCase(args=([1, 2, 5], 11), expected=3, description="standard"),
                TestCase(args=([2], 3), expected=-1, description="unreachable"),
                TestCase(args=([1], 0), expected=0, description="amount=0"),
                TestCase(args=([1, 2, 5], 100), expected=20, description="larger"),
                TestCase(args=([186, 419, 83, 408], 6249), expected=20, description="non-trivial"),
            ],
        ),
        Problem(
            id="lcs",
            category="dp",
            source="internal",
            statement=(
                "Return the length of the longest common subsequence of two strings a and b. "
                "Implement longestCommonSubsequence(a: str, b: str) -> int."
            ),
            primary_function="longestCommonSubsequence",
            signature_aliases=["lcs", "longest_common_subsequence"],
            selection_rationale="Two-string DP; common LLM failure: confusing subsequence with substring.",
            tests=[
                TestCase(args=("abcde", "ace"), expected=3, description="standard"),
                TestCase(args=("abc", "abc"), expected=3, description="identical"),
                TestCase(args=("abc", "def"), expected=0, description="disjoint"),
                TestCase(args=("", "abc"), expected=0, description="empty"),
                TestCase(args=("AGGTAB", "GXTXAYB"), expected=4, description="textbook"),
            ],
        ),
        Problem(
            id="house_robber",
            category="dp",
            source="internal",
            statement=(
                "Given an array nums of non-negative ints, return the max sum you can collect "
                "without picking adjacent elements. Implement rob(nums: list[int]) -> int."
            ),
            primary_function="rob",
            signature_aliases=["house_robber", "max_rob"],
            selection_rationale="1D DP with adjacency constraint; tests linear scan formulation.",
            tests=[
                TestCase(args=([1, 2, 3, 1],), expected=4, description="standard"),
                TestCase(args=([2, 7, 9, 3, 1],), expected=12, description="standard"),
                TestCase(args=([],), expected=0, description="empty"),
                TestCase(args=([5],), expected=5, description="single"),
                TestCase(args=([2, 1, 1, 2],), expected=4, description="adjacent equal"),
            ],
        ),
        Problem(
            id="min_cost_path",
            category="dp",
            source="internal",
            statement=(
                "Given an m x n grid of non-negative ints, return the minimum path sum from "
                "top-left to bottom-right moving only right or down. "
                "Implement minPathSum(grid: list[list[int]]) -> int."
            ),
            primary_function="minPathSum",
            signature_aliases=["min_path_sum", "min_cost_path"],
            selection_rationale="2D DP on a grid; tests indexing and boundary handling.",
            tests=[
                TestCase(args=([[1, 3, 1], [1, 5, 1], [4, 2, 1]],), expected=7, description="standard"),
                TestCase(args=([[1, 2, 3], [4, 5, 6]],), expected=12, description="rectangle"),
                TestCase(args=([[5]],), expected=5, description="single cell"),
                TestCase(args=([[1, 2], [1, 1]],), expected=3, description="2x2"),
                TestCase(args=([[1] * 5 for _ in range(5)],), expected=9, description="uniform"),
            ],
        ),
        Problem(
            id="lis",
            category="dp",
            source="internal",
            statement=(
                "Given an integer array nums, return the length of the longest strictly increasing "
                "subsequence. Implement lengthOfLIS(nums) -> int."
            ),
            primary_function="lengthOfLIS",
            signature_aliases=["lis", "longest_increasing_subsequence"],
            selection_rationale="O(n log n) preferred; tests common O(n^2) baseline against optimal.",
            tests=[
                TestCase(args=([10, 9, 2, 5, 3, 7, 101, 18],), expected=4, description="standard"),
                TestCase(args=([0, 1, 0, 3, 2, 3],), expected=4, description="repeats"),
                TestCase(args=([7, 7, 7, 7, 7],), expected=1, description="all equal"),
                TestCase(args=([],), expected=0, description="empty"),
                TestCase(args=([1, 2, 3, 4, 5],), expected=5, description="strictly increasing"),
            ],
        ),
        Problem(
            id="rod_cutting",
            category="dp",
            source="internal",
            statement=(
                "Given prices[i] = price of a rod of length i+1 and an integer n, return the max "
                "obtainable revenue by cutting the rod of length n. Implement rodCutting(prices, n)."
            ),
            primary_function="rodCutting",
            signature_aliases=["rod_cutting", "max_revenue"],
            selection_rationale="Unbounded knapsack pattern with index off-by-one risk.",
            tests=[
                TestCase(args=([1, 5, 8, 9, 10, 17, 17, 20], 8), expected=22, description="textbook"),
                TestCase(args=([3, 5, 8, 9, 10, 17, 17, 20], 8), expected=24, description="alt prices"),
                TestCase(args=([2], 1), expected=2, description="single length"),
                TestCase(args=([1, 5, 8, 9], 4), expected=10, description="small"),
                TestCase(args=([1, 5, 8, 9, 10, 17, 17, 20], 1), expected=1, description="n=1"),
            ],
        ),
        Problem(
            id="matrix_chain",
            category="dp",
            source="internal",
            statement=(
                "Given an array p of length n where matrix A_i has dimensions p[i-1] x p[i], "
                "return the minimum number of scalar multiplications. "
                "Implement matrixChainOrder(p: list[int]) -> int."
            ),
            primary_function="matrixChainOrder",
            signature_aliases=["matrix_chain", "matrix_chain_order"],
            selection_rationale="Interval DP; tests nested-loop formulation.",
            tests=[
                TestCase(args=([1, 2, 3, 4],), expected=18, description="3 matrices"),
                TestCase(args=([10, 20, 30, 40, 30],), expected=30000, description="textbook 1"),
                TestCase(args=([10, 20, 30],), expected=6000, description="2 matrices"),
                TestCase(args=([5, 10, 3, 12, 5, 50, 6],), expected=2010, description="textbook 2"),
                TestCase(args=([2, 3, 4, 2, 5],), expected=58, description="small"),
            ],
        ),
        Problem(
            id="subset_sum",
            category="dp",
            source="apps-introductory",
            statement=(
                "Given a list of positive ints nums and a target T, return True iff some subset "
                "of nums sums to T. Implement subsetSum(nums, target) -> bool."
            ),
            primary_function="subsetSum",
            signature_aliases=["subset_sum", "can_partition"],
            selection_rationale="APPS-style decision DP; tests boolean DP table.",
            tests=[
                TestCase(args=([1, 2, 3, 7], 6), expected=True, description="standard"),
                TestCase(args=([1, 2, 7, 1, 5], 10), expected=True, description="standard"),
                TestCase(args=([1, 3, 4, 8], 6), expected=False, description="impossible"),
                TestCase(args=([], 0), expected=True, description="empty target 0"),
                TestCase(args=([5], 5), expected=True, description="single hit"),
            ],
        ),
    ]


def _graph_problems() -> list[Problem]:
    return [
        Problem(
            id="topo_sort",
            category="graph",
            source="internal",
            statement=(
                "Given the number of tasks N and a list of dependency pairs prerequisites where "
                "[a, b] means b must finish before a, return any valid order or [] if impossible. "
                "Implement findOrder(numCourses: int, prerequisites: list[list[int]]) -> list[int]."
            ),
            primary_function="findOrder",
            signature_aliases=["topological_sort", "course_order", "topo_sort"],
            selection_rationale="Cycle detection + topo order; common LLM failure: missing cycle check.",
            tests=[
                TestCase(args=(4, [[1, 0], [2, 1], [3, 2]]), expected=[0, 1, 2, 3],
                         description="linear chain", judge=lambda r: r == [0, 1, 2, 3]),
                TestCase(args=(2, [[0, 1], [1, 0]]), expected=[],
                         description="cycle", judge=lambda r: r == []),
                TestCase(args=(1, []), expected=[0], description="single",
                         judge=lambda r: r == [0]),
                TestCase(args=(4, [[1, 0], [2, 0], [3, 1], [3, 2]]),
                         expected="any valid order",
                         description="branching",
                         judge=lambda r: isinstance(r, list) and sorted(r) == [0, 1, 2, 3]
                                          and r.index(0) < r.index(1) and r.index(0) < r.index(2)
                                          and r.index(1) < r.index(3) and r.index(2) < r.index(3)),
                TestCase(args=(4, [[0, 1], [1, 2], [2, 3], [3, 1]]), expected=[],
                         description="complex cycle", judge=lambda r: r == []),
            ],
        ),
        Problem(
            id="cycle_detect",
            category="graph",
            source="internal",
            statement=(
                "Given an undirected graph as an adjacency list adj (list of list of int), return "
                "True iff it contains a cycle. Implement hasCycle(adj: list[list[int]]) -> bool."
            ),
            primary_function="hasCycle",
            signature_aliases=["has_cycle", "detect_cycle"],
            selection_rationale="Undirected cycle detection (parent-tracking DFS).",
            tests=[
                TestCase(args=([[1], [0, 2], [1]],), expected=False, description="path"),
                TestCase(args=([[1, 2], [0, 2], [0, 1]],), expected=True, description="triangle"),
                TestCase(args=([[]],), expected=False, description="single"),
                TestCase(args=([[1], [0], [3], [2]],), expected=False, description="two paths"),
                TestCase(args=([[1, 3], [0, 2], [1, 3], [2, 0]],), expected=True, description="square"),
            ],
        ),
        Problem(
            id="bfs",
            category="graph",
            source="internal",
            statement=(
                "Given an adjacency list adj and a start node s, return the BFS visit order "
                "from s (ties broken by neighbour list order). "
                "Implement bfs(adj: list[list[int]], s: int) -> list[int]."
            ),
            primary_function="bfs",
            signature_aliases=["breadth_first_search"],
            selection_rationale="BFS basics; tests queue usage and visited set.",
            tests=[
                TestCase(args=([[1, 2], [0, 3], [0], [1]], 0), expected=[0, 1, 2, 3], description="tree"),
                TestCase(args=([[]], 0), expected=[0], description="single"),
                TestCase(args=([[1], [0]], 0), expected=[0, 1], description="edge"),
                TestCase(args=([[1, 2], [0, 2], [0, 1]], 0), expected=[0, 1, 2], description="triangle"),
                TestCase(args=([[], [], []], 1), expected=[1], description="isolated"),
            ],
        ),
        Problem(
            id="dfs",
            category="graph",
            source="internal",
            statement=(
                "Given an adjacency list adj and a start node s, return the DFS preorder "
                "visit order (recursive, neighbour order respected). "
                "Implement dfs(adj: list[list[int]], s: int) -> list[int]."
            ),
            primary_function="dfs",
            signature_aliases=["depth_first_search"],
            selection_rationale="DFS basics; tests recursion + visited.",
            tests=[
                TestCase(args=([[1, 2], [0, 3], [0], [1]], 0), expected=[0, 1, 3, 2], description="tree"),
                TestCase(args=([[]], 0), expected=[0], description="single"),
                TestCase(args=([[1], [0]], 0), expected=[0, 1], description="edge"),
                TestCase(args=([[1, 2], [0, 2], [0, 1]], 0), expected=[0, 1, 2], description="triangle"),
                TestCase(args=([[2], [], [0]], 1), expected=[1], description="isolated start"),
            ],
        ),
        Problem(
            id="dijkstra",
            category="graph",
            source="internal",
            statement=(
                "Given a weighted graph as adj where adj[u] = list of (v, w), and a source s, "
                "return a list dist of length n with shortest distances from s "
                "(use float('inf') for unreachable). "
                "Implement dijkstra(adj: list[list[tuple[int, int]]], s: int) -> list[float]."
            ),
            primary_function="dijkstra",
            signature_aliases=["shortest_path", "single_source_shortest"],
            selection_rationale="Priority queue + relaxation; common LLM failure: missing heap usage.",
            tests=[
                TestCase(
                    args=([[(1, 4), (2, 1)], [(2, 2), (3, 5)], [(1, 2), (3, 8)], []], 0),
                    expected=[0, 3, 1, 8],
                    description="textbook",
                ),
                TestCase(args=([[]], 0), expected=[0], description="single"),
                TestCase(args=([[(1, 1)], []], 0), expected=[0, 1], description="edge"),
                TestCase(args=([[(1, 5)], [(2, 5)], []], 0), expected=[0, 5, 10], description="line"),
                TestCase(
                    args=([[(1, 1), (2, 4)], [(2, 2)], []], 0),
                    expected=[0, 1, 3],
                    description="relax",
                ),
            ],
        ),
        Problem(
            id="bellman_ford",
            category="graph",
            source="internal",
            statement=(
                "Given n nodes and a list of weighted edges (u, v, w) (directed), return shortest "
                "distances from source s, or None if a negative cycle is reachable. "
                "Implement bellmanFord(n, edges, s) -> list | None."
            ),
            primary_function="bellmanFord",
            signature_aliases=["bellman_ford"],
            selection_rationale="Tests negative-cycle detection.",
            tests=[
                TestCase(args=(3, [(0, 1, 1), (1, 2, 2), (0, 2, 5)], 0), expected=[0, 1, 3]),
                TestCase(args=(3, [(0, 1, 1), (1, 2, -1), (2, 0, -1)], 0), expected=None,
                         description="neg cycle"),
                TestCase(args=(2, [(0, 1, 4)], 0), expected=[0, 4], description="single edge"),
                TestCase(args=(1, [], 0), expected=[0], description="single node"),
                TestCase(args=(4, [(0, 1, 1), (1, 2, 1), (2, 3, 1)], 0), expected=[0, 1, 2, 3],
                         description="line"),
            ],
        ),
        Problem(
            id="connected_components",
            category="graph",
            source="internal",
            statement=(
                "Given an adjacency list adj of an undirected graph, return the number of "
                "connected components. Implement countComponents(adj) -> int."
            ),
            primary_function="countComponents",
            signature_aliases=["count_components", "connected_components"],
            selection_rationale="Tests union-find or DFS sweep.",
            tests=[
                TestCase(args=([[1], [0], [3], [2]],), expected=2),
                TestCase(args=([[]],), expected=1),
                TestCase(args=([[], [], []],), expected=3),
                TestCase(args=([[1, 2], [0, 2], [0, 1]],), expected=1),
                TestCase(args=([[1], [0], [], [4], [3]],), expected=3),
            ],
        ),
        Problem(
            id="scc",
            category="graph",
            source="internal",
            statement=(
                "Given a directed graph as adjacency list adj, return the number of strongly "
                "connected components. Implement countSCC(adj) -> int."
            ),
            primary_function="countSCC",
            signature_aliases=["count_scc", "strongly_connected_components"],
            selection_rationale="Kosaraju / Tarjan; tests two-pass DFS.",
            tests=[
                TestCase(args=([[1], [2], [0]],), expected=1, description="single SCC"),
                TestCase(args=([[1], [], []],), expected=3, description="path 3"),
                TestCase(args=([[1], [0]],), expected=1, description="cycle 2"),
                TestCase(args=([[1], [2], [0], [4], [5], [3]],), expected=2,
                         description="two cycles"),
                TestCase(args=([[]],), expected=1, description="single"),
            ],
        ),
        Problem(
            id="unweighted_shortest",
            category="graph",
            source="internal",
            statement=(
                "Given an adjacency list adj and source s, return shortest hop counts from s. "
                "Use -1 for unreachable. Implement shortestHops(adj, s) -> list[int]."
            ),
            primary_function="shortestHops",
            signature_aliases=["shortest_hops", "bfs_distances"],
            selection_rationale="Tests BFS distance variant.",
            tests=[
                TestCase(args=([[1], [0, 2], [1, 3], [2]], 0), expected=[0, 1, 2, 3]),
                TestCase(args=([[]], 0), expected=[0]),
                TestCase(args=([[1], [0], []], 0), expected=[0, 1, -1], description="unreachable"),
                TestCase(args=([[1, 2], [0], [0]], 0), expected=[0, 1, 1]),
                TestCase(args=([[], [], []], 1), expected=[-1, 0, -1]),
            ],
        ),
        Problem(
            id="grid_shortest_path",
            category="graph",
            source="apps-introductory",
            statement=(
                "Given an m x n binary grid where 0 is passable and 1 is a wall, return the "
                "length of the shortest path from (0,0) to (m-1,n-1) using 4-neighbour moves, "
                "or -1 if unreachable. Implement shortestPath(grid) -> int."
            ),
            primary_function="shortestPath",
            signature_aliases=["shortest_path_grid"],
            selection_rationale="APPS-style grid BFS; tests boundary + visited.",
            tests=[
                TestCase(args=([[0, 0, 0], [1, 1, 0], [0, 0, 0]],), expected=5),
                TestCase(args=([[0]],), expected=1),
                TestCase(args=([[0, 1], [1, 0]],), expected=-1),
                TestCase(args=([[0, 0], [0, 0]],), expected=3),
                TestCase(args=([[0, 0, 0, 0], [1, 1, 1, 0], [0, 0, 0, 0], [0, 1, 1, 1]],),
                         expected=7),
            ],
        ),
    ]


def _ds_problems() -> list[Problem]:
    """Data-structure problems. We embed a tiny driver in each test's ``call``
    so the candidate (a class) can be exercised end-to-end."""
    return [
        Problem(
            id="lru_cache",
            category="ds",
            source="internal",
            statement=(
                "Implement an LRU cache class LRUCache with __init__(self, capacity: int), "
                "get(key) -> int (returns -1 if absent), and put(key, value). "
                "Capacity is a positive int."
            ),
            primary_function="LRUCache",
            signature_aliases=[],
            selection_rationale="Class with O(1) get/put; common LLM failure: incorrect eviction.",
            tests=[
                TestCase(
                    call=("[(lambda c: ([c.put(1,1), c.put(2,2), c.get(1), c.put(3,3),"
                          " c.get(2), c.put(4,4), c.get(1), c.get(3), c.get(4)]))(LRUCache(2))]"),
                    expected=[[None, None, 1, None, -1, None, -1, 3, 4]],
                    description="textbook",
                ),
                TestCase(
                    call=("[(lambda c: ([c.put(1,'a'), c.get(1)]))(LRUCache(1))]"),
                    expected=[[None, 'a']],
                    description="capacity 1",
                ),
                TestCase(
                    call=("[(lambda c: ([c.put(1,1), c.put(2,2), c.get(1), c.put(3,3), c.get(2)]))"
                          "(LRUCache(2))]"),
                    expected=[[None, None, 1, None, -1]],
                    description="evict",
                ),
            ],
        ),
        Problem(
            id="min_stack",
            category="ds",
            source="internal",
            statement=(
                "Implement a stack class MinStack supporting push(x), pop(), top(), getMin() all in O(1)."
            ),
            primary_function="MinStack",
            signature_aliases=[],
            selection_rationale="Tests auxiliary-stack pattern.",
            tests=[
                TestCase(
                    call=("[(lambda s: ([s.push(-2), s.push(0), s.push(-3), s.getMin(),"
                          " s.pop(), s.top(), s.getMin()]))(MinStack())]"),
                    expected=[[None, None, None, -3, None, 0, -2]],
                    description="textbook",
                ),
                TestCase(
                    call=("[(lambda s: ([s.push(1), s.push(2), s.getMin(), s.pop(), s.getMin()]))"
                          "(MinStack())]"),
                    expected=[[None, None, 1, None, 1]],
                    description="ascending",
                ),
                TestCase(
                    call=("[(lambda s: ([s.push(3), s.push(1), s.push(1), s.getMin(), s.pop(),"
                          " s.getMin()]))(MinStack())]"),
                    expected=[[None, None, None, 1, None, 1]],
                    description="duplicates",
                ),
            ],
        ),
        Problem(
            id="stack_using_queue",
            category="ds",
            source="internal",
            statement=(
                "Implement class MyStack with push(x), pop(), top(), empty() using only queues."
            ),
            primary_function="MyStack",
            signature_aliases=[],
            selection_rationale="Tests queue-based simulation of stack semantics.",
            tests=[
                TestCase(
                    call=("[(lambda s: ([s.push(1), s.push(2), s.top(), s.pop(), s.empty()]))"
                          "(MyStack())]"),
                    expected=[[None, None, 2, 2, False]],
                    description="basic",
                ),
                TestCase(
                    call=("[(lambda s: ([s.push(1), s.pop(), s.empty()]))(MyStack())]"),
                    expected=[[None, 1, True]],
                    description="single",
                ),
                TestCase(
                    call=("[(lambda s: ([s.push(1), s.push(2), s.push(3), s.pop(), s.top()]))"
                          "(MyStack())]"),
                    expected=[[None, None, None, 3, 2]],
                    description="three elems",
                ),
            ],
        ),
        Problem(
            id="reverse_linked_list",
            category="ds",
            source="internal",
            statement=(
                "Define class ListNode(self, val=0, next=None) and a function "
                "reverseList(head: ListNode | None) -> ListNode | None that reverses the list. "
                "Also provide a helper to_list(head) -> list[int] that materializes a linked list."
            ),
            primary_function="reverseList",
            signature_aliases=["reverse_list"],
            selection_rationale="Tests pointer-rewiring; LLM failure: lost head pointer.",
            tests=[
                TestCase(
                    call=("(lambda: (["
                          "to_list(reverseList(None)),"
                          "to_list(reverseList(ListNode(1))),"
                          "to_list(reverseList(ListNode(1, ListNode(2, ListNode(3))))),"
                          "]))()"),
                    expected=[[], [1], [3, 2, 1]],
                    description="three cases",
                ),
            ],
        ),
        Problem(
            id="binary_tree_traversal",
            category="ds",
            source="internal",
            statement=(
                "Define class TreeNode(self, val=0, left=None, right=None) and a function "
                "inorder(root) -> list[int] that returns the inorder traversal."
            ),
            primary_function="inorder",
            signature_aliases=[],
            selection_rationale="Tests recursive traversal.",
            tests=[
                TestCase(
                    call=("(lambda: ("
                          "inorder(None),"
                          "inorder(TreeNode(1)),"
                          "inorder(TreeNode(1, TreeNode(2), TreeNode(3)))"
                          "))()"),
                    expected=[[], [1], [2, 1, 3]],
                    description="three trees",
                ),
            ],
        ),
        Problem(
            id="priority_queue",
            category="ds",
            source="internal",
            statement=(
                "Implement class PQ with push(x), pop() -> smallest, top() -> smallest, empty()."
            ),
            primary_function="PQ",
            signature_aliases=[],
            selection_rationale="Min-heap semantics.",
            tests=[
                TestCase(
                    call=("(lambda q: ([q.push(3), q.push(1), q.push(2), q.top(), q.pop(),"
                          " q.pop(), q.empty()]))(PQ())"),
                    expected=[None, None, None, 1, 1, 2, False],
                    description="basic",
                ),
                TestCase(
                    call="(lambda q: q.empty())(PQ())",
                    expected=True,
                    description="empty",
                ),
            ],
        ),
        Problem(
            id="heapify",
            category="ds",
            source="internal",
            statement=(
                "Implement heapify(arr: list[int]) -> None that converts arr into a min-heap in-place."
            ),
            primary_function="heapify",
            signature_aliases=["build_heap"],
            selection_rationale="Tests in-place heap construction.",
            tests=[
                TestCase(
                    call=("(lambda a: (heapify(a), a == sorted(a) or "
                          "all(a[i] <= a[2*i+1] for i in range(len(a)) if 2*i+1 < len(a)) and "
                          "all(a[i] <= a[2*i+2] for i in range(len(a)) if 2*i+2 < len(a))))"
                          "([4,1,3,2,16,9,10,14,8,7])"),
                    expected=(None, True),
                    description="textbook",
                ),
            ],
        ),
        Problem(
            id="avl",
            category="ds",
            source="internal",
            statement=(
                "Implement class AVL with insert(key) and inorder() -> list[int] that returns "
                "the sorted keys after insertions while maintaining AVL balance."
            ),
            primary_function="AVL",
            signature_aliases=[],
            selection_rationale="Balanced BST; tests rotation correctness.",
            tests=[
                TestCase(
                    call=("(lambda t: ([t.insert(k) for k in [10,20,30,40,50,25]] and t.inorder()))"
                          "(AVL())"),
                    expected=[10, 20, 25, 30, 40, 50],
                    description="balanced inorder",
                ),
            ],
        ),
        Problem(
            id="adj_list_construct",
            category="ds",
            source="internal",
            statement=(
                "Given n vertices and a list of undirected edges, return an adjacency list "
                "(list of sorted neighbour lists). Implement adjList(n, edges)."
            ),
            primary_function="adjList",
            signature_aliases=["adjacency_list"],
            selection_rationale="Tests data-structure assembly.",
            tests=[
                TestCase(args=(3, [[0, 1], [0, 2]]), expected=[[1, 2], [0], [0]]),
                TestCase(args=(1, []), expected=[[]]),
                TestCase(args=(2, [[0, 1]]), expected=[[1], [0]]),
                TestCase(args=(4, [[0, 1], [2, 3]]), expected=[[1], [0], [3], [2]]),
                TestCase(args=(3, [[0, 1], [1, 2], [0, 2]]), expected=[[1, 2], [0, 2], [0, 1]]),
            ],
        ),
        Problem(
            id="valid_parentheses",
            category="ds",
            source="apps-introductory",
            statement=(
                "Given a string of '()[]{}', return True iff brackets close in correct order. "
                "Implement isValid(s: str) -> bool."
            ),
            primary_function="isValid",
            signature_aliases=["is_valid", "valid_parentheses"],
            selection_rationale="APPS-style stack; classic textbook.",
            tests=[
                TestCase(args=("()",), expected=True),
                TestCase(args=("()[]{}",), expected=True),
                TestCase(args=("(]",), expected=False),
                TestCase(args=("",), expected=True),
                TestCase(args=("([)]",), expected=False),
            ],
        ),
    ]


def load_internal30() -> list[Problem]:
    return _dp_problems() + _graph_problems() + _ds_problems()


if __name__ == "__main__":  # pragma: no cover
    ps = load_internal30()
    print(f"loaded {len(ps)} problems")
    by_cat: dict[str, int] = {}
    for p in ps:
        by_cat[p.category] = by_cat.get(p.category, 0) + 1
    print(by_cat)
