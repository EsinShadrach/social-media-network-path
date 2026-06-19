"""
Social Network Path Finding (Shortest Connection Path)

This script demonstrates how to find the shortest connection path between
two people in a social network. In graph terms:
- Each person is a node
- Each friendship is an undirected edge

We use Bi-Directional Breadth-First Search (Bi-BFS), which runs BFS from
both ends at once and meets in the middle. This is still shortest-path
correct for unweighted graphs, and is usually faster on large networks.
"""

def build_graph(friendships):
	"""
	Convert a list of friendship pairs into an adjacency-list graph.
	Name matching is case-insensitive, but we preserve the first seen casing
	for display/output.

	Example input:
	[
		("Precious", "Celine"),
		("Celine", "Goodness"),
	]

	Output:
	{
		"Precious": {"Celine"},
		"Celine": {"Precious", "Goodness"},
		"Goodness": {"Celine"},
	}
	"""
	graph = {}  # Dictionary where key=person, value=set of directly connected friends.
	name_lookup = {}  # Maps lowercase name -> canonical display name (first seen form).
     
	#for loop
	for person_a, person_b in friendships:
		# Normalize spaces while keeping original letter case for display.
		person_a = person_a.strip()
		person_b = person_b.strip()

		# Lowercase keys make matching case-insensitive.
		key_a = person_a.lower()
		key_b = person_b.lower()

		# Keep the first-seen style, e.g., "Precious" instead of later "precious".
		if key_a not in name_lookup:
			name_lookup[key_a] = person_a
		if key_b not in name_lookup:
			name_lookup[key_b] = person_b

		canonical_a = name_lookup[key_a]
		canonical_b = name_lookup[key_b]

		# Ensure both people exist in the graph before adding connections.
		if canonical_a not in graph:
			graph[canonical_a] = set()
		if canonical_b not in graph:
			graph[canonical_b] = set()

		# Skip self-links after normalization.
		if canonical_a == canonical_b:
			continue

		# Add links in both directions because friendship is mutual.
		graph[canonical_a].add(canonical_b)
		graph[canonical_b].add(canonical_a)

	return graph


def _resolve_name_case_insensitive(graph, typed_name):
	"""Return the canonical graph name that matches typed_name, or None."""
	normalized = typed_name.strip().lower()
	for existing_name in graph:
		if existing_name.lower() == normalized:
			return existing_name
	return None


def shortest_connection_path(graph, start_person, target_person):
	"""
	Find the shortest path between start_person and target_person using
	bi-directional BFS.

	Returns:
	- A list like ["Precious", "Celine", "Ozioma"] if a path exists
	- None if no path exists
	"""

	# Convert user-typed names to canonical graph names ignoring letter case.
	start_person = _resolve_name_case_insensitive(graph, start_person)
	target_person = _resolve_name_case_insensitive(graph, target_person)

	# If either person is missing from the graph, path search cannot proceed.
	if start_person is None or target_person is None:
		return None

	# If both names are the same, the shortest path is just that one person.
	if start_person == target_person:
		return [start_person]

	# Parent maps store how we reached each node from each side.
	# Example: parent_from_start[X] = Y means Y -> X in the BFS tree.
	parent_from_start = {start_person: None}
	parent_from_target = {target_person: None}

	# Frontiers hold the current "wave" of nodes from each side.
	frontier_start = {start_person}
	frontier_target = {target_person}

	# Expand level-by-level from both sides until they meet.
	while frontier_start and frontier_target:
		# Always expand the smaller frontier for better performance.
		if len(frontier_start) <= len(frontier_target):
			meeting_node = _expand_frontier(
				graph,
				frontier_start,
				parent_from_start,
				parent_from_target,
			)
		else:
			meeting_node = _expand_frontier(
				graph,
				frontier_target,
				parent_from_target,
				parent_from_start,
			)

		# If expansions touch, we can reconstruct the shortest path.
		if meeting_node is not None:
			return _reconstruct_path(meeting_node, parent_from_start, parent_from_target)

	# If both frontiers exhaust without meeting, there is no connection.
	return None


def _expand_frontier(graph, frontier, my_parent, other_parent):
	"""Expand one BFS level from one side; return meeting node if found."""
	next_frontier = set()

	for person in frontier:
		for friend in graph[person]:
			if friend in my_parent:
				continue  # Already visited on this side.

			my_parent[friend] = person  # Record tree edge for path reconstruction.

			# If other side has already visited this node, the searches have met.
			if friend in other_parent:
				frontier.clear()
				return friend

			next_frontier.add(friend)

	# Update the existing frontier object in place.
	frontier.clear()
	frontier.update(next_frontier)
	return None


def _reconstruct_path(meeting_node, parent_from_start, parent_from_target):
	"""Build full path from start -> meeting_node -> target."""
	# Walk back from meeting point to start using start-side parents.
	left_half = []
	current = meeting_node
	while current is not None:
		left_half.append(current)
		current = parent_from_start[current]
	left_half.reverse()  # Now ordered start -> meeting_node.

	# Walk from meeting point to target using target-side parents.
	# We skip meeting_node to avoid duplicating it in final path.
	right_half = []
	current = parent_from_target[meeting_node]
	while current is not None:
		right_half.append(current)
		current = parent_from_target[current]

	return left_half + right_half


def print_path(path):
	"""Print a path in a clean presentation format."""
	if path is None:
		print("No connection path found.")
	else:
		print(" -> ".join(path))
		print(f"Connection distance (number of hops): {len(path) - 1}")

if __name__ == "__main__":
	sample_friendships = [
		("Precious", "Celine"),
		("Celine", "Goodness"),
		("Goodness", "Chinaza"),
		("Precious", "Ozioma"),
		("Ozioma", "Stanley"),
		("Stanley", "Chinaza"),
		("Henry", "Franklin"),
	]

	social_graph = build_graph(sample_friendships)

	print("People in this network:")
	print(", ".join(sorted(social_graph.keys())))

	while True:
		start = input("\nEnter start person (or 'q' to quit): ").strip()
		if start.lower() in {"q", "quit", "exit"}:
			print("Goodbye.")
			break

		target = input("Enter target person (or 'q' to quit): ").strip()
		if target.lower() in {"q", "quit", "exit"}:
			print("Goodbye.")
			break

		shortest_path = shortest_connection_path(social_graph, start, target)

		print("\nShortest connection path:")
		print_path(shortest_path)