TECHNIQUES = [
    {
        "name": "Array Traversal & State Simulation",
        "when_to_use": "Sequential processing, simulations, or replaying system state changes",
        "core_idea": "Iterate through elements while maintaining minimal state variables",
        "time": "O(n)",
        "space": "O(1)",
        "mistakes": "State leakage across iterations"
    },
    {
        "name": "String Normalization & Token Processing",
        "when_to_use": "Parsing logs, protocols, configs, or identifiers",
        "core_idea": "Process characters using scans, frequency counts, or token boundaries",
        "time": "O(n)",
        "space": "O(σ)",
        "mistakes": "Ignoring encoding and normalization rules"
    },
    {
        "name": "Stable Sorting & Ordering Guarantees",
        "when_to_use": "When relative order must be preserved (logs, events, timestamps)",
        "core_idea": "Sort elements while preserving original order for equal keys",
        "time": "O(n log n)",
        "space": "O(n)",
        "mistakes": "Assuming stability without guarantees"
    },
    {
        "name": "Binary Search on Sorted Data",
        "when_to_use": "Fast lookup in ordered datasets or indices",
        "core_idea": "Halve the search space iteratively",
        "time": "O(log n)",
        "space": "O(1)",
        "mistakes": "Boundary mismanagement"
    },
    {
        "name": "Binary Search on Answer Space",
        "when_to_use": "When feasibility is monotonic over answer range",
        "core_idea": "Search answers instead of data",
        "time": "O(log R × feasibility_check)",
        "space": "O(1)",
        "mistakes": "Incorrect monotonic assumption"
    },
    {
        "name": "Two Pointers (Converging)",
        "when_to_use": "Pairing, deduplication, or interval merging",
        "core_idea": "Move pointers toward each other based on conditions",
        "time": "O(n)",
        "space": "O(1)",
        "mistakes": "Advancing both pointers blindly"
    },
    {
        "name": "Sliding Window (Fixed & Dynamic)",
        "when_to_use": "Rate limiting, rolling metrics, subarray constraints",
        "core_idea": "Maintain a moving window with incremental updates",
        "time": "O(n)",
        "space": "O(1) or O(k)",
        "mistakes": "Invalid window shrink logic"
    },
    {
        "name": "Hash-Based Indexing",
        "when_to_use": "Fast lookups, deduplication, caching",
        "core_idea": "Map keys to values with average constant time",
        "time": "O(1) average",
        "space": "O(n)",
        "mistakes": "Ignoring collision behavior"
    },
    {
        "name": "Prefix Sum Aggregation",
        "when_to_use": "Time-series metrics, cumulative analytics",
        "core_idea": "Precompute cumulative values for constant-time queries",
        "time": "O(n)",
        "space": "O(n)",
        "mistakes": "Off-by-one indexing"
    },
    {
        "name": "Difference Arrays for Bulk Updates",
        "when_to_use": "Batch updates on ranges (counters, quotas)",
        "core_idea": "Apply updates lazily using boundary deltas",
        "time": "O(n)",
        "space": "O(n)",
        "mistakes": "Forgetting final prefix sum"
    },
    {
        "name": "Monotonic Stack Pattern",
        "when_to_use": "Next greater/smaller queries, histogram problems",
        "core_idea": "Maintain stack with monotonic order",
        "time": "O(n)",
        "space": "O(n)",
        "mistakes": "Wrong comparison direction"
    },
    {
        "name": "Queue & Deque Scheduling",
        "when_to_use": "Task scheduling, BFS, sliding window extrema",
        "core_idea": "FIFO or double-ended processing",
        "time": "O(n)",
        "space": "O(n)",
        "mistakes": "Incorrect pop direction"
    },
    {
        "name": "Recursion with Controlled Depth",
        "when_to_use": "Hierarchical data or divide-and-conquer",
        "core_idea": "Break problem into smaller identical subproblems",
        "time": "Varies",
        "space": "O(depth)",
        "mistakes": "Missing base cases"
    },
    {
        "name": "Backtracking with Pruning",
        "when_to_use": "Configuration search, constraint satisfaction",
        "core_idea": "Explore possibilities and undo decisions",
        "time": "Exponential",
        "space": "O(depth)",
        "mistakes": "Not restoring state"
    },
    {
        "name": "Greedy Decision Making",
        "when_to_use": "Scheduling, resource allocation",
        "core_idea": "Choose locally optimal decision",
        "time": "O(n)",
        "space": "O(1)",
        "mistakes": "Applying greediness without proof"
    },
    {
        "name": "Dynamic Programming – Memoization",
        "when_to_use": "Recursive problems with overlapping subproblems",
        "core_idea": "Cache results of subproblems",
        "time": "Varies",
        "space": "O(states)",
        "mistakes": "Large unnecessary state"
    },
    {
        "name": "Dynamic Programming – Tabulation",
        "when_to_use": "Bottom-up optimization problems",
        "core_idea": "Iteratively fill DP table",
        "time": "O(states × transitions)",
        "space": "O(states)",
        "mistakes": "Incorrect iteration order"
    },
    {
        "name": "State Compression DP",
        "when_to_use": "Small state spaces with combinations",
        "core_idea": "Represent states using bitmasks",
        "time": "O(2^n × n)",
        "space": "O(2^n)",
        "mistakes": "Memory explosion"
    },
    {
        "name": "Tree Traversal Algorithms",
        "when_to_use": "Hierarchical configs, dependency trees",
        "core_idea": "Visit nodes in DFS or BFS order",
        "time": "O(n)",
        "space": "O(h)",
        "mistakes": "Wrong traversal order"
    },
    {
        "name": "Binary Search Tree Invariants",
        "when_to_use": "Ordered dynamic data",
        "core_idea": "Left < root < right invariant",
        "time": "O(h)",
        "space": "O(h)",
        "mistakes": "Ignoring skewed worst-case"
    },
    {
        "name": "Lowest Common Ancestor (LCA)",
        "when_to_use": "Hierarchical dependency queries",
        "core_idea": "Find deepest shared ancestor",
        "time": "O(log n)",
        "space": "O(n)",
        "mistakes": "Incorrect ancestor jumps"
    },
    {
        "name": "Graph Breadth-First Search",
        "when_to_use": "Shortest paths in unweighted systems",
        "core_idea": "Layer-by-layer traversal",
        "time": "O(V + E)",
        "space": "O(V)",
        "mistakes": "Visited marking delays"
    },
    {
        "name": "Graph Depth-First Search",
        "when_to_use": "Cycle detection, reachability",
        "core_idea": "Explore depth-wise",
        "time": "O(V + E)",
        "space": "O(V)",
        "mistakes": "Stack overflow"
    },
    {
        "name": "Shortest Path Algorithms",
        "when_to_use": "Latency, routing, dependency resolution",
        "core_idea": "Edge relaxation to minimize cost",
        "time": "O(E log V)",
        "space": "O(V)",
        "mistakes": "Negative weights with Dijkstra"
    },
    {
        "name": "Union-Find (Disjoint Sets)",
        "when_to_use": "Component tracking, clustering",
        "core_idea": "Merge and find sets efficiently",
        "time": "O(α(n))",
        "space": "O(n)",
        "mistakes": "Incorrect parent assignment"
    },
    {
        "name": "Bit Manipulation & Masking",
        "when_to_use": "Flags, permissions, compact states",
        "core_idea": "Use bits to represent data",
        "time": "O(1)",
        "space": "O(1)",
        "mistakes": "Operator precedence"
    },
    {
        "name": "Mathematical Invariants & GCD",
        "when_to_use": "Consistency checks, modular logic",
        "core_idea": "Use mathematical properties",
        "time": "Varies",
        "space": "O(1)",
        "mistakes": "Overflow"
    },
    {
        "name": "Randomized Algorithms",
        "when_to_use": "Hashing, load balancing, sampling",
        "core_idea": "Introduce randomness for expected performance",
        "time": "Expected O(n)",
        "space": "O(1)",
        "mistakes": "Assuming determinism"
    },
    {
        "name": "Amortized Analysis",
        "when_to_use": "Dynamic arrays, stacks, queues",
        "core_idea": "Average cost over operations",
        "time": "Amortized O(1)",
        "space": "O(n)",
        "mistakes": "Confusing worst-case with amortized"
    },
    {
        "name": "Invariant-Based Reasoning",
        "when_to_use": "Reliability-critical backend logic",
        "core_idea": "Maintain conditions that must always hold",
        "time": "Problem-dependent",
        "space": "Problem-dependent",
        "mistakes": "Implicit assumptions"
    },
    {
        "name": "Trie (Prefix Tree)",
        "when_to_use": "String prefix matching, autocomplete, IP routing",
        "core_idea": "Tree structure where each node represents a character",
        "time": "O(m) for search/insert, m is string length",
        "space": "O(ALPHABET_SIZE * N * M)",
        "mistakes": "Not compressing paths, memory overhead"
    },
    {
        "name": "Segment Tree",
        "when_to_use": "Range queries and updates on arrays",
        "core_idea": "Binary tree storing segment information",
        "time": "O(log n) for query/update",
        "space": "O(n)",
        "mistakes": "Incorrect segment merging logic"
    },
    {
        "name": "Fenwick Tree (Binary Indexed Tree)",
        "when_to_use": "Prefix sum queries with point updates",
        "core_idea": "Use bit manipulation for efficient prefix sums",
        "time": "O(log n) for query/update",
        "space": "O(n)",
        "mistakes": "Wrong index calculation"
    },
    {
        "name": "Topological Sort",
        "when_to_use": "Dependency resolution, task scheduling",
        "core_idea": "Linear ordering respecting dependencies",
        "time": "O(V + E)",
        "space": "O(V)",
        "mistakes": "Not detecting cycles"
    },
    {
        "name": "Strongly Connected Components (SCC)",
        "when_to_use": "Graph analysis, dependency cycles",
        "core_idea": "Find maximal sets of mutually reachable nodes",
        "time": "O(V + E)",
        "space": "O(V)",
        "mistakes": "Incorrect DFS traversal"
    },
    {
        "name": "Minimum Spanning Tree (Kruskal/Prim)",
        "when_to_use": "Network design, clustering",
        "core_idea": "Connect all nodes with minimum total weight",
        "time": "O(E log E) or O(E log V)",
        "space": "O(V)",
        "mistakes": "Not handling disconnected graphs"
    },
    {
        "name": "Floyd-Warshall Algorithm",
        "when_to_use": "All-pairs shortest paths",
        "core_idea": "Dynamic programming on intermediate nodes",
        "time": "O(V³)",
        "space": "O(V²)",
        "mistakes": "Negative cycle detection"
    },
    {
        "name": "A* Search Algorithm",
        "when_to_use": "Pathfinding with heuristics",
        "core_idea": "Best-first search with cost + heuristic",
        "time": "O(b^d) where b is branching, d is depth",
        "space": "O(b^d)",
        "mistakes": "Inadmissible heuristic"
    },
    {
        "name": "KMP String Matching",
        "when_to_use": "Pattern matching in text",
        "core_idea": "Use failure function to skip comparisons",
        "time": "O(n + m)",
        "space": "O(m)",
        "mistakes": "Incorrect failure function"
    },
    {
        "name": "Rabin-Karp Algorithm",
        "when_to_use": "Multiple pattern matching, rolling hash",
        "core_idea": "Use hash function for pattern matching",
        "time": "O(n + m) average, O(nm) worst",
        "space": "O(1)",
        "mistakes": "Hash collision handling"
    },
    {
        "name": "Manacher's Algorithm",
        "when_to_use": "Finding longest palindromic substring",
        "core_idea": "Expand around centers with symmetry",
        "time": "O(n)",
        "space": "O(n)",
        "mistakes": "Boundary conditions"
    },
    {
        "name": "Suffix Array & LCP",
        "when_to_use": "String analysis, longest common substring",
        "core_idea": "Sort all suffixes, compute longest common prefix",
        "time": "O(n log n)",
        "space": "O(n)",
        "mistakes": "Incorrect suffix comparison"
    },
    {
        "name": "Eulerian Path/Circuit",
        "when_to_use": "Route optimization, graph traversal",
        "core_idea": "Visit every edge exactly once",
        "time": "O(E)",
        "space": "O(V + E)",
        "mistakes": "Not checking degree conditions"
    },
    {
        "name": "Network Flow (Ford-Fulkerson)",
        "when_to_use": "Maximum flow, bipartite matching",
        "core_idea": "Find augmenting paths to increase flow",
        "time": "O(E * max_flow)",
        "space": "O(V + E)",
        "mistakes": "Not finding optimal augmenting paths"
    },
    {
        "name": "Hungarian Algorithm",
        "when_to_use": "Assignment problems, bipartite matching",
        "core_idea": "Find minimum cost perfect matching",
        "time": "O(n³)",
        "space": "O(n²)",
        "mistakes": "Incorrect dual variable updates"
    },
    {
        "name": "Meet in the Middle",
        "when_to_use": "Split search space for exponential problems",
        "core_idea": "Solve two halves and combine results",
        "time": "O(2^(n/2))",
        "space": "O(2^(n/2))",
        "mistakes": "Incorrect combination logic"
    },
    {
        "name": "Mo's Algorithm",
        "when_to_use": "Range queries on static arrays",
        "core_idea": "Process queries in optimized order",
        "time": "O((n + q) * sqrt(n))",
        "space": "O(n)",
        "mistakes": "Wrong block size calculation"
    },
    {
        "name": "Heavy-Light Decomposition",
        "when_to_use": "Path queries on trees",
        "core_idea": "Decompose tree into chains",
        "time": "O(log² n) per query",
        "space": "O(n)",
        "mistakes": "Incorrect chain updates"
    },
    {
        "name": "Centroid Decomposition",
        "when_to_use": "Tree problems requiring divide-and-conquer",
        "core_idea": "Recursively decompose tree at centroids",
        "time": "O(n log n)",
        "space": "O(n)",
        "mistakes": "Incorrect centroid calculation"
    },
    {
        "name": "Sparse Table",
        "when_to_use": "Range minimum/maximum queries (RMQ)",
        "core_idea": "Precompute ranges of power-of-2 lengths",
        "time": "O(1) query, O(n log n) build",
        "space": "O(n log n)",
        "mistakes": "Overlapping range handling"
    },
    {
        "name": "Square Root Decomposition",
        "when_to_use": "Range queries and updates",
        "core_idea": "Divide array into sqrt(n) blocks",
        "time": "O(sqrt(n)) per query",
        "space": "O(n)",
        "mistakes": "Block boundary handling"
    },
    {
        "name": "Coordinate Compression",
        "when_to_use": "Large value ranges, discrete events",
        "core_idea": "Map large values to small indices",
        "time": "O(n log n)",
        "space": "O(n)",
        "mistakes": "Not handling duplicates"
    },
    {
        "name": "Sweep Line Algorithm",
        "when_to_use": "Geometric problems, interval overlaps",
        "core_idea": "Process events in sorted order",
        "time": "O(n log n)",
        "space": "O(n)",
        "mistakes": "Event ordering errors"
    },
    {
        "name": "Convex Hull (Graham Scan)",
        "when_to_use": "Geometric problems, optimization",
        "core_idea": "Find boundary of point set",
        "time": "O(n log n)",
        "space": "O(n)",
        "mistakes": "Collinear point handling"
    },
    {
        "name": "Line Sweep for Intersections",
        "when_to_use": "Finding line segment intersections",
        "core_idea": "Maintain active segments during sweep",
        "time": "O(n log n + k) where k is intersections",
        "space": "O(n)",
        "mistakes": "Event priority queue errors"
    },
    {
        "name": "Fast Fourier Transform (FFT)",
        "when_to_use": "Polynomial multiplication, signal processing",
        "core_idea": "Convert to frequency domain and back",
        "time": "O(n log n)",
        "space": "O(n)",
        "mistakes": "Complex number precision"
    },
    {
        "name": "Number Theoretic Transform (NTT)",
        "when_to_use": "Polynomial operations modulo prime",
        "core_idea": "FFT over finite fields",
        "time": "O(n log n)",
        "space": "O(n)",
        "mistakes": "Primitive root selection"
    },
    {
        "name": "Chinese Remainder Theorem",
        "when_to_use": "Modular arithmetic, system of congruences",
        "core_idea": "Combine solutions from coprime moduli",
        "time": "O(k) where k is number of equations",
        "space": "O(1)",
        "mistakes": "Non-coprime moduli"
    },
    {
        "name": "Extended Euclidean Algorithm",
        "when_to_use": "Modular inverse, GCD with coefficients",
        "core_idea": "Find GCD and Bézout coefficients",
        "time": "O(log min(a, b))",
        "space": "O(1)",
        "mistakes": "Sign handling in coefficients"
    },
    {
        "name": "Miller-Rabin Primality Test",
        "when_to_use": "Probabilistic prime checking",
        "core_idea": "Use Fermat's little theorem with witnesses",
        "time": "O(k log³ n) for k iterations",
        "space": "O(1)",
        "mistakes": "Insufficient witness iterations"
    },
    {
        "name": "Pollard's Rho Algorithm",
        "when_to_use": "Integer factorization",
        "core_idea": "Use cycle detection for factors",
        "time": "O(sqrt(p)) where p is smallest factor",
        "space": "O(1)",
        "mistakes": "Cycle detection failure"
    },
    {
        "name": "Simulated Annealing",
        "when_to_use": "Optimization problems, local search",
        "core_idea": "Accept worse solutions probabilistically",
        "time": "Problem-dependent",
        "space": "O(1)",
        "mistakes": "Cooling schedule too fast"
    },
    {
        "name": "Genetic Algorithm",
        "when_to_use": "Evolutionary optimization",
        "core_idea": "Evolve population through selection and mutation",
        "time": "Problem-dependent",
        "space": "O(population_size)",
        "mistakes": "Premature convergence"
    },
    {
        "name": "Monte Carlo Method",
        "when_to_use": "Probabilistic estimation, integration",
        "core_idea": "Use random sampling for approximation",
        "time": "O(n) for n samples",
        "space": "O(1)",
        "mistakes": "Insufficient samples"
    },
    {
        "name": "Boyer-Moore Voting Algorithm",
        "when_to_use": "Finding majority element",
        "core_idea": "Cancel out pairs of different elements",
        "time": "O(n)",
        "space": "O(1)",
        "mistakes": "Not verifying candidate"
    },
    {
        "name": "Reservoir Sampling",
        "when_to_use": "Random sampling from stream",
        "core_idea": "Maintain uniform sample as stream progresses",
        "time": "O(n)",
        "space": "O(k) for k samples",
        "mistakes": "Probability calculation errors"
    },
    {
        "name": "Floyd's Cycle Detection",
        "when_to_use": "Detecting cycles in sequences",
        "core_idea": "Use two pointers moving at different speeds",
        "time": "O(λ + μ) where λ is cycle length, μ is start",
        "space": "O(1)",
        "mistakes": "Not finding cycle start"
    },
    {
        "name": "Knuth-Morris-Pratt (KMP)",
        "when_to_use": "Pattern matching with failure function",
        "core_idea": "Precompute longest proper prefix-suffix",
        "time": "O(n + m)",
        "space": "O(m)",
        "mistakes": "Incorrect failure function"
    },
    {
        "name": "Z-Algorithm",
        "when_to_use": "Pattern matching, string analysis",
        "core_idea": "Compute Z-array for prefix matching",
        "time": "O(n + m)",
        "space": "O(n + m)",
        "mistakes": "Z-box boundary errors"
    }
]
