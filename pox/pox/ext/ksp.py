# Based on https://gist.github.com/ALenfant/5491853

import networkx as nx
import Queue


def path_cost(graph, path, weight=None):
    return len(path) - 1


def ksp(graph, source, target, num_k, weight):
    # Shortest path from the source to the target
    A = [nx.shortest_path(graph, source, target, weight=weight)]
    A_costs = [path_cost(graph, A[0], weight)]

    # Initialize the heap to store the potential kth shortest path
    B = Queue.PriorityQueue()

    for k in range(1, num_k):
        # The spur node ranges from the first node to the next to last node in the shortest path
        try:
            for i in range(len(A[k-1])-1):
                # Spur node is retrieved from the previous k-shortest path, k - 1
                spurNode = A[k-1][i]
                # The sequence of nodes from the source to the spur node of the previous k-shortest path
                rootPath = A[k-1][:i]

                # We store the removed edges
                removed_edges = []

                for path in A:
                    if len(path) - 1 > i and rootPath == path[:i]:
                        # Remove the links that are part of the previous shortest paths which share the same root path
                        edge = (path[i], path[i+1])
                        if not graph.has_edge(*edge):
                            continue
                        removed_edges.append((edge, graph.get_edge_data(*edge)))
                        graph.remove_edge(*edge)

                # Calculate the spur path from the spur node to the sink
                try:
                    spurPath = nx.shortest_path(graph, spurNode, target, weight=weight)

                    # Entire path is made up of the root path and spur path
                    totalPath = rootPath + spurPath
                    totalPathCost = path_cost(graph, totalPath, weight)
                    # Add the potential k-shortest path to the heap
                    B.put((totalPathCost, totalPath))

                except nx.NetworkXNoPath:
                    pass

                #Add back the edges that were removed from the graph
                for removed_edge in removed_edges:
                    graph.add_edge(
                        *removed_edge[0],
                        **removed_edge[1]
                    )

            # Sort the potential k-shortest paths by cost
            # B is already sorted
            # Add the lowest cost path becomes the k-shortest path.
            while True:
                try:
                    cost_, path_ = B.get(False)
                    if path_ not in A:
                        A.append(path_)
                        A_costs.append(cost_)
                        break
                except Queue.Empty:
                    break
        except IndexError:
            pass

    return A
