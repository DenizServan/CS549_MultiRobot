"""Open the empty scene (room, walls, tables, two mobile Pandas) in the viewer. Runs from any folder."""
import os
import robotic as ry  # type: ignore

C = ry.Config()
C.addFile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_files", "search_area.g"))
C.view(True)
