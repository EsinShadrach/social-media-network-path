"""
Visual animation for social-network shortest path finding.

This uses Tkinter (built into Python) to animate bi-directional BFS:
- Blue wave expands from the start person
- Orange wave expands from the target person
- Green shows the final shortest path when the waves meet
"""

import math
import tkinter as tk
from tkinter import messagebox, ttk

from defence import build_graph, shortest_connection_path


# ── Colour palette ────────────────────────────────────────────────────────────
BG_APP        = "#1A1D2E"   # app background (dark navy)
BG_PANEL      = "#22263A"   # control panel
BG_CANVAS     = "#12151F"   # graph canvas background
BG_STATUS     = "#1E2235"   # status bar background

ACCENT_BLUE   = "#4E9BFF"   # start-wave fill
ACCENT_ORANGE = "#FFA54D"   # target-wave fill
ACCENT_GREEN  = "#4ADE80"   # final path / meeting node

NODE_DEFAULT_FILL    = "#2A2F4A"
NODE_DEFAULT_OUTLINE = "#4A5180"
EDGE_DEFAULT         = "#2E3455"

TEXT_PRIMARY   = "#E8EAF6"
TEXT_SECONDARY = "#7B82A8"
TEXT_ACCENT    = "#A5B4FC"

FONT_TITLE  = ("Segoe UI", 13, "bold")
FONT_LABEL  = ("Segoe UI", 10)
FONT_ENTRY  = ("Segoe UI", 10)
FONT_BTN    = ("Segoe UI", 10, "bold")
FONT_STATUS = ("Segoe UI", 9)
FONT_NODE   = ("Segoe UI", 8, "bold")


def bidirectional_bfs_states(graph, start_person, target_person):
    """
    Generate animation states for bi-directional BFS.

    Each yielded state is a dictionary with:
    - frontier_start, frontier_target
    - visited_start, visited_target
    - expanded_side, expanded_nodes, expanded_edges
    - step
    - meeting_node
    - done
    """
    if start_person not in graph or target_person not in graph:
        yield {
            "frontier_start": set(),
            "frontier_target": set(),
            "visited_start": set(),
            "visited_target": set(),
            "expanded_side": "none",
            "expanded_nodes": set(),
            "expanded_edges": [],
            "step": 0,
            "meeting_node": None,
            "done": True,
        }
        return

    if start_person == target_person:
        yield {
            "frontier_start": {start_person},
            "frontier_target": {target_person},
            "visited_start": {start_person},
            "visited_target": {target_person},
            "expanded_side": "both",
            "expanded_nodes": {start_person},
            "expanded_edges": [],
            "step": 0,
            "meeting_node": start_person,
            "done": True,
        }
        return

    visited_start = {start_person}
    visited_target = {target_person}
    frontier_start = {start_person}
    frontier_target = {target_person}

    yield {
        "frontier_start": set(frontier_start),
        "frontier_target": set(frontier_target),
        "visited_start": set(visited_start),
        "visited_target": set(visited_target),
        "expanded_side": "none",
        "expanded_nodes": set(),
        "expanded_edges": [],
        "step": 0,
        "meeting_node": None,
        "done": False,
    }

    meeting_node = None
    step = 0

    while frontier_start and frontier_target and meeting_node is None:
        if len(frontier_start) <= len(frontier_target):
            expanded_side = "start"
            expanded_nodes = set(frontier_start)
            expanded_edges = []
            next_frontier = set()
            for person in frontier_start:
                for friend in graph[person]:
                    if friend in visited_start:
                        continue
                    expanded_edges.append((person, friend))
                    visited_start.add(friend)
                    next_frontier.add(friend)
                    if friend in visited_target:
                        meeting_node = friend
                        break
                if meeting_node is not None:
                    break
            frontier_start = next_frontier
        else:
            expanded_side = "target"
            expanded_nodes = set(frontier_target)
            expanded_edges = []
            next_frontier = set()
            for person in frontier_target:
                for friend in graph[person]:
                    if friend in visited_target:
                        continue
                    expanded_edges.append((person, friend))
                    visited_target.add(friend)
                    next_frontier.add(friend)
                    if friend in visited_start:
                        meeting_node = friend
                        break
                if meeting_node is not None:
                    break
            frontier_target = next_frontier

        step += 1

        yield {
            "frontier_start": set(frontier_start),
            "frontier_target": set(frontier_target),
            "visited_start": set(visited_start),
            "visited_target": set(visited_target),
            "expanded_side": expanded_side,
            "expanded_nodes": expanded_nodes,
            "expanded_edges": expanded_edges,
            "step": step,
            "meeting_node": meeting_node,
            "done": meeting_node is not None,
        }

    if meeting_node is None:
        yield {
            "frontier_start": set(),
            "frontier_target": set(),
            "visited_start": set(visited_start),
            "visited_target": set(visited_target),
            "expanded_side": "none",
            "expanded_nodes": set(),
            "expanded_edges": [],
            "step": step + 1,
            "meeting_node": None,
            "done": True,
        }


class SocialPathAnimator:
    def __init__(self, root):
        self.root = root
        self.root.title("Social Network — Bi-Directional BFS")
        self.root.configure(bg=BG_APP)
        self.root.resizable(False, False)

        self.friendships = [
            ("Precious", "Celine"),
            ("Celine", "Goodness"),
            ("Goodness", "Ozioma"),
            ("Ozioma", "Stanley"),
            ("Stanley", "Henry"),
            ("Henry", "Franklin"),
            ("Franklin", "Miracle"),
            ("Miracle", "Daniel"),
            ("Daniel", "Promise"),
            ("Precious", "Ozioma"),
            ("Celine", "Stanley"),
            ("Goodness", "Henry"),
            ("Ozioma", "Franklin"),
            ("Stanley", "Miracle"),
            ("Henry", "Daniel"),
            ("Franklin", "Promise"),
            ("Precious", "Henry"),
            ("Goodness", "Miracle"),
        ]

        self.graph = build_graph(self.friendships)
        self.positions = self._compute_circle_positions(
            list(self.graph.keys()), 420, 290, 230)

        self.node_radius = 26
        self.animation_delay_ms = 1200
        self.state_iterator = None
        self.final_path = None
        self.step_count = 0
        self._after_id = None          # track pending .after() call
        self._paused = False

        self.node_ovals = {}           # name -> canvas oval item ID
        self.node_texts = {}           # name -> canvas text item ID
        self.edge_lines = {}           # sorted(nameA,nameB) tuple -> line ID

        self._build_ui()
        self._draw_base_graph()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Title bar ──────────────────────────────────────────────────────
        title_frame = tk.Frame(self.root, bg=BG_APP)
        title_frame.pack(fill="x", padx=20, pady=(16, 0))

        tk.Label(
            title_frame,
            text="Social Network Path Finder",
            font=FONT_TITLE,
            fg=TEXT_ACCENT,
            bg=BG_APP,
        ).pack(side="left")

        tk.Label(
            title_frame,
            text="Bi-Directional BFS",
            font=("Segoe UI", 9),
            fg=TEXT_SECONDARY,
            bg=BG_APP,
        ).pack(side="left", padx=(10, 0), pady=(4, 0))

        # ── Control panel ──────────────────────────────────────────────────
        panel = tk.Frame(self.root, bg=BG_PANEL, bd=0)
        panel.pack(fill="x", padx=20, pady=12)

        # inner padding frame
        inner = tk.Frame(panel, bg=BG_PANEL)
        inner.pack(fill="x", padx=14, pady=10)

        # Start field
        self._make_field(inner, "Start", "Precious").pack(side="left")

        tk.Label(inner, text="→", font=("Segoe UI", 14),
                 fg=TEXT_SECONDARY, bg=BG_PANEL).pack(side="left", padx=8)

        # Target field
        self._make_field(inner, "Target", "Promise").pack(side="left")

        # Spacer
        tk.Frame(inner, bg=BG_PANEL, width=16).pack(side="left")

        # Buttons
        self.animate_button = self._make_button(
            inner, "▶  Animate", self.start_animation, ACCENT_BLUE)
        self.animate_button.pack(side="left", padx=(0, 6))

        self.pause_button = self._make_button(
            inner, "⏸  Pause", self._toggle_pause, "#6C7293")
        self.pause_button.pack(side="left", padx=(0, 6))
        self.pause_button.config(state="disabled")

        self.step_button = self._make_button(
            inner, "⏭  Step", self._manual_step, "#6C7293")
        self.step_button.pack(side="left", padx=(0, 6))
        self.step_button.config(state="disabled")

        self.reset_button = self._make_button(
            inner, "↺  Reset", self.reset_graph, "#4A5180")
        self.reset_button.pack(side="left")

        # Speed slider (right side)
        speed_frame = tk.Frame(inner, bg=BG_PANEL)
        speed_frame.pack(side="right")

        tk.Label(speed_frame, text="Speed", font=FONT_LABEL,
                 fg=TEXT_SECONDARY, bg=BG_PANEL).pack(side="left", padx=(0, 6))

        self.speed_var = tk.IntVar(value=1200)
        speed_slider = tk.Scale(
            speed_frame,
            from_=3000, to=200,
            orient="horizontal",
            variable=self.speed_var,
            command=self._on_speed_change,
            showvalue=False,
            bg=BG_PANEL, fg=TEXT_SECONDARY,
            troughcolor="#3A3F60",
            activebackground=ACCENT_BLUE,
            highlightthickness=0,
            bd=0,
            length=110,
            resolution=100,
        )
        # left=slow (3000ms delay), right=fast (200ms delay)
        tk.Label(speed_frame, text="Slow", font=("Segoe UI", 8),
                 fg=TEXT_SECONDARY, bg=BG_PANEL).pack(side="left", padx=(0, 4))
        speed_slider.pack(side="left")
        tk.Label(speed_frame, text="Fast", font=("Segoe UI", 8),
                 fg=TEXT_SECONDARY, bg=BG_PANEL).pack(side="left", padx=(4, 0))

        # ── Legend strip ───────────────────────────────────────────────────
        legend = tk.Frame(self.root, bg=BG_APP)
        legend.pack(fill="x", padx=20, pady=(0, 6))

        for color, label in [
            (ACCENT_BLUE,   "Start wave"),
            (ACCENT_ORANGE, "Target wave"),
            (ACCENT_GREEN,  "Shortest path"),
            ("#79E48B",     "Meeting point"),
        ]:
            dot = tk.Canvas(legend, width=12, height=12,
                            bg=BG_APP, highlightthickness=0)
            dot.create_oval(1, 1, 11, 11, fill=color, outline="")
            dot.pack(side="left", padx=(0, 4))
            tk.Label(legend, text=label, font=("Segoe UI", 8),
                     fg=TEXT_SECONDARY, bg=BG_APP).pack(side="left", padx=(0, 16))

        # ── Graph canvas ───────────────────────────────────────────────────
        canvas_frame = tk.Frame(self.root, bg="#0D1017",
                                highlightbackground="#2E3455", highlightthickness=1)
        canvas_frame.pack(padx=20, pady=(0, 10))

        self.canvas = tk.Canvas(
            canvas_frame, width=840, height=580,
            bg=BG_CANVAS, highlightthickness=0)
        self.canvas.pack()

        # ── Status bar ─────────────────────────────────────────────────────
        status_bar = tk.Frame(self.root, bg=BG_STATUS)
        status_bar.pack(fill="x", padx=20, pady=(0, 14))

        self.status_var = tk.StringVar(value="Ready  —  enter two names and click Animate")
        tk.Label(
            status_bar,
            textvariable=self.status_var,
            font=FONT_STATUS,
            fg=TEXT_PRIMARY,
            bg=BG_STATUS,
            anchor="w",
        ).pack(side="left", padx=10, pady=5)

        self.step_label_var = tk.StringVar(value="")
        tk.Label(
            status_bar,
            textvariable=self.step_label_var,
            font=FONT_STATUS,
            fg=TEXT_SECONDARY,
            bg=BG_STATUS,
            anchor="e",
        ).pack(side="right", padx=10, pady=5)

    def _make_field(self, parent, label_text, default_value):
        """Return a frame containing a label + styled entry."""
        frame = tk.Frame(parent, bg=BG_PANEL)
        tk.Label(frame, text=label_text, font=FONT_LABEL,
                 fg=TEXT_SECONDARY, bg=BG_PANEL).pack(anchor="w")
        entry_var = tk.StringVar(value=default_value)
        entry = tk.Entry(
            frame,
            textvariable=entry_var,
            font=FONT_ENTRY,
            width=13,
            bg="#2E3455",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            bd=4,
        )
        entry.pack()
        if label_text == "Start":
            self.start_var = entry_var
        else:
            self.target_var = entry_var
        return frame

    def _make_button(self, parent, text, command, bg_color):
        """
        Label-based button — fully respects bg/fg on macOS unlike tk.Button.
        Supports .config(state='disabled'/'normal') like a real button.
        """
        hover_color  = self._lighten(bg_color)
        dim_color    = self._darken(bg_color)

        btn = tk.Label(
            parent,
            text=text,
            font=FONT_BTN,
            bg=bg_color,
            fg=TEXT_PRIMARY,
            padx=14,
            pady=7,
            cursor="hand2",
        )
        # Store metadata on the widget itself
        btn._bg_normal   = bg_color     # type: ignore[attr-defined]
        btn._bg_hover    = hover_color  # type: ignore[attr-defined]
        btn._bg_dim      = dim_color    # type: ignore[attr-defined]
        btn._command     = command      # type: ignore[attr-defined]
        btn._enabled     = True         # type: ignore[attr-defined]

        def on_enter(_e):
            if btn._enabled:            # type: ignore[attr-defined]
                btn.config(bg=btn._bg_hover)  # type: ignore[attr-defined]

        def on_leave(_e):
            if btn._enabled:            # type: ignore[attr-defined]
                btn.config(bg=btn._bg_normal)  # type: ignore[attr-defined]

        def on_click(_e):
            if btn._enabled:            # type: ignore[attr-defined]
                btn._command()          # type: ignore[attr-defined]

        btn.bind("<Enter>",   on_enter)
        btn.bind("<Leave>",   on_leave)
        btn.bind("<Button-1>", on_click)

        # Patch .config() to intercept state=disabled/normal
        _orig_config = btn.config

        def patched_config(**kwargs):
            state = kwargs.pop("state", None)
            if state == "disabled":
                btn._enabled = False    # type: ignore[attr-defined]
                _orig_config(
                    bg=btn._bg_dim,     # type: ignore[attr-defined]
                    fg=TEXT_SECONDARY,
                    cursor="arrow",
                    **kwargs,
                )
            elif state == "normal":
                btn._enabled = True     # type: ignore[attr-defined]
                _orig_config(
                    bg=btn._bg_normal,  # type: ignore[attr-defined]
                    fg=TEXT_PRIMARY,
                    cursor="hand2",
                    **kwargs,
                )
            else:
                _orig_config(**kwargs)

        btn.config = patched_config     # type: ignore[method-assign]
        return btn

    @staticmethod
    def _lighten(hex_color):
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"#{min(255,r+35):02X}{min(255,g+35):02X}{min(255,b+35):02X}"

    @staticmethod
    def _darken(hex_color):
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"#{max(0,r-30):02X}{max(0,g-30):02X}{max(0,b-30):02X}"

    # ── Graph drawing ─────────────────────────────────────────────────────────

    def _compute_circle_positions(self, names, center_x, center_y, radius):
        positions = {}
        total = len(names)
        for i, name in enumerate(sorted(names)):
            angle = (2 * math.pi * i / total) - (math.pi / 2)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            positions[name] = (x, y)
        return positions

    def _resolve_name_case_insensitive(self, typed_name):
        normalized = typed_name.strip().lower()
        for existing_name in self.graph:
            if existing_name.lower() == normalized:
                return existing_name
        return None

    def _draw_base_graph(self):
        """Draw graph once; store item IDs for O(1) re-colouring."""
        self.canvas.delete("all")
        self.node_ovals.clear()
        self.node_texts.clear()
        self.edge_lines.clear()

        # Subtle grid dots in background
        for x in range(30, 841, 40):
            for y in range(30, 581, 40):
                self.canvas.create_oval(x-1, y-1, x+1, y+1,
                                        fill="#1E2235", outline="")

        # Edges
        drawn = set()
        for person in self.graph:
            for friend in self.graph[person]:
                edge_key = tuple(sorted((person, friend)))
                if edge_key in drawn:
                    continue
                drawn.add(edge_key)
                x1, y1 = self.positions[person]
                x2, y2 = self.positions[friend]
                line_id = self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=EDGE_DEFAULT, width=2,
                    smooth=True,
                )
                self.edge_lines[edge_key] = line_id

        # Nodes
        for name, (x, y) in self.positions.items():
            # Shadow
            self.canvas.create_oval(
                x - self.node_radius + 3,
                y - self.node_radius + 3,
                x + self.node_radius + 3,
                y + self.node_radius + 3,
                fill="#0A0C14", outline="",
            )
            oval_id = self.canvas.create_oval(
                x - self.node_radius,
                y - self.node_radius,
                x + self.node_radius,
                y + self.node_radius,
                fill=NODE_DEFAULT_FILL,
                outline=NODE_DEFAULT_OUTLINE,
                width=2,
            )
            text_id = self.canvas.create_text(
                x, y, text=name,
                font=FONT_NODE,
                fill=TEXT_PRIMARY,
            )
            self.node_ovals[name] = oval_id
            self.node_texts[name] = text_id

    def _reset_all_colors(self):
        for oval_id in self.node_ovals.values():
            self.canvas.itemconfigure(
                oval_id,
                fill=NODE_DEFAULT_FILL,
                outline=NODE_DEFAULT_OUTLINE,
                width=2,
            )
        for text_id in self.node_texts.values():
            self.canvas.itemconfigure(text_id, fill=TEXT_PRIMARY)
        for line_id in self.edge_lines.values():
            self.canvas.itemconfigure(line_id, fill=EDGE_DEFAULT, width=2)

    def _color_node(self, name, fill, outline=NODE_DEFAULT_OUTLINE,
                    width=2, text_color=TEXT_PRIMARY):
        if name in self.node_ovals:
            self.canvas.itemconfigure(
                self.node_ovals[name],
                fill=fill, outline=outline, width=width,
            )
        if name in self.node_texts:
            self.canvas.itemconfigure(self.node_texts[name], fill=text_color)

    def _color_edge(self, name_a, name_b, fill, width=3):
        edge_key = tuple(sorted((name_a, name_b)))
        if edge_key in self.edge_lines:
            self.canvas.itemconfigure(
                self.edge_lines[edge_key],
                fill=fill, width=width,
            )

    # ── Controls ──────────────────────────────────────────────────────────────

    def _on_speed_change(self, _value):
        # slider goes 200–3000; map so left=fast(200ms), right=slow(3000ms)
        self.animation_delay_ms = int(self.speed_var.get())

    def _toggle_pause(self):
        if not self.state_iterator:
            return
        self._paused = not self._paused
        if self._paused:
            if self._after_id:
                self.root.after_cancel(self._after_id)
                self._after_id = None
            self.pause_button.config(text="▶  Resume")
            self.step_button.config(state="normal")
            self.status_var.set("Paused  —  click Step to advance or Resume to continue")
        else:
            self.pause_button.config(text="⏸  Pause")
            self.step_button.config(state="disabled")
            self._animate_next_state()

    def _manual_step(self):
        """Advance one frame while paused."""
        if self._paused and self.state_iterator:
            self._animate_next_state(schedule_next=False)

    def reset_graph(self):
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self.state_iterator = None
        self.final_path = None
        self.step_count = 0
        self._paused = False
        self.pause_button.config(text="⏸  Pause", state="disabled")
        self.step_button.config(state="disabled")
        self._reset_all_colors()
        self.status_var.set("Reset complete  —  ready for another animation")
        self.step_label_var.set("")

    def start_animation(self):
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self._paused = False
        self.pause_button.config(text="⏸  Pause", state="normal")
        self.step_button.config(state="disabled")
        self._reset_all_colors()

        start_raw  = self.start_var.get()
        target_raw = self.target_var.get()

        start  = self._resolve_name_case_insensitive(start_raw)
        target = self._resolve_name_case_insensitive(target_raw)

        if start is None or target is None:
            messagebox.showerror(
                "Unknown name",
                "One or both names are not in the network.\n\n"
                f"Available: {', '.join(sorted(self.graph.keys()))}",
            )
            self.status_var.set("Error: unknown name(s)  —  check spelling")
            self.pause_button.config(state="disabled")
            return

        self.final_path = shortest_connection_path(self.graph, start, target)
        self.state_iterator = iter(
            bidirectional_bfs_states(self.graph, start, target))
        self.step_count = 0
        self.status_var.set(f"Searching  {start}  →  {target} ...")
        self.step_label_var.set("Step 0")
        self._animate_next_state()

    # ── Animation engine ──────────────────────────────────────────────────────

    def _animate_next_state(self, schedule_next=True):
        if self.state_iterator is None:
            return
        try:
            state = next(self.state_iterator)
        except StopIteration:
            self._finish_animation()
            return

        self._reset_all_colors()

        # Visited nodes — muted fill
        for person in state["visited_start"]:
            self._color_node(person, "#1A3A6A", outline="#2A5A9A")
        for person in state["visited_target"]:
            self._color_node(person, "#5A3000", outline="#8A5000")

        # Active frontier — vivid fill + thick outline
        for person in state["frontier_start"]:
            self._color_node(person, ACCENT_BLUE,
                             outline="#0D4EA6", width=3,
                             text_color="#000D2E")
        for person in state["frontier_target"]:
            self._color_node(person, ACCENT_ORANGE,
                             outline="#A65600", width=3,
                             text_color="#2E1500")

        # Active edges
        side = state["expanded_side"]
        edge_color = {"start": "#1D74D6", "target": "#D6781D"}.get(side)
        if edge_color:
            for a, b in state["expanded_edges"]:
                self._color_edge(a, b, edge_color, width=4)

        # Meeting node — bright green
        if state["meeting_node"] is not None:
            self._color_node(
                state["meeting_node"],
                "#79E48B", outline=ACCENT_GREEN, width=4,
                text_color="#002810",
            )

        self.step_count = state["step"]
        side_label = {
            "start":  "expanding from START  (blue wave)",
            "target": "expanding from TARGET  (orange wave)",
            "none":   "initial frontiers placed",
            "both":   "start = target",
        }.get(side, side)

        fs = sorted(state["frontier_start"])
        ft = sorted(state["frontier_target"])
        meet = state["meeting_node"] or "—"
        self.status_var.set(
            f"Step {self.step_count}  |  {side_label}  |  meeting: {meet}"
        )
        self.step_label_var.set(
            f"blue frontier: {fs}   orange frontier: {ft}"
        )

        if state["done"]:
            self.root.after(300, self._finish_animation)
            return

        if schedule_next and not self._paused:
            self._after_id = self.root.after(
                self.animation_delay_ms, self._animate_next_state)

    def _finish_animation(self):
        self.pause_button.config(state="disabled")
        self.step_button.config(state="disabled")
        self.state_iterator = None

        if self.final_path:
            self._reset_all_colors()
            # Draw path edges
            for i in range(len(self.final_path) - 1):
                self._color_edge(
                    self.final_path[i], self.final_path[i + 1],
                    ACCENT_GREEN, width=4,
                )
            # Draw path nodes
            for person in self.final_path:
                self._color_node(
                    person, "#16532D",
                    outline=ACCENT_GREEN, width=3,
                    text_color=ACCENT_GREEN,
                )
            hops = len(self.final_path) - 1
            path_str = "  →  ".join(self.final_path)
            self.status_var.set(
                f"Shortest path ({hops} hop{'s' if hops != 1 else ''}):  {path_str}"
            )
            self.step_label_var.set("")
        else:
            self.status_var.set("No connection path found between the two people.")
            self.step_label_var.set("")


if __name__ == "__main__":
    root = tk.Tk()
    app = SocialPathAnimator(root)
    root.mainloop()
