"""One-off generator for docs/architecture-diagram.excalidraw.

Not part of the app; run manually if the diagram needs regenerating:
    python scripts/gen_excalidraw_architecture.py
"""
import json
import random

random.seed(42)
_id_counter = 0


def next_id(prefix: str) -> str:
    global _id_counter
    _id_counter += 1
    return f"{prefix}-{_id_counter}"


def seed() -> int:
    return random.randint(1, 2**31 - 1)


elements = []


def rect(x, y, w, h, stroke, bg, label=None, label_size=16, dashed=False):
    el_id = next_id("rect")
    elements.append({
        "id": el_id, "type": "rectangle", "x": x, "y": y, "width": w, "height": h,
        "angle": 0, "strokeColor": stroke, "backgroundColor": bg,
        "fillStyle": "solid", "strokeWidth": 2,
        "strokeStyle": "dashed" if dashed else "solid", "roughness": 1, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": {"type": 3}, "seed": seed(),
        "version": 1, "versionNonce": seed(), "isDeleted": False,
        "boundElements": [], "updated": 1, "link": None, "locked": False,
    })
    if label:
        text(x + w / 2, y + h / 2, label, size=label_size, align="center", vertical="middle")
    return el_id


def ellipse(x, y, w, h, stroke, bg, label=None, label_size=15):
    el_id = next_id("ellipse")
    elements.append({
        "id": el_id, "type": "ellipse", "x": x, "y": y, "width": w, "height": h,
        "angle": 0, "strokeColor": stroke, "backgroundColor": bg,
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": {"type": 2}, "seed": seed(), "version": 1, "versionNonce": seed(),
        "isDeleted": False, "boundElements": [], "updated": 1, "link": None, "locked": False,
    })
    if label:
        text(x + w / 2, y + h / 2, label, size=label_size, align="center", vertical="middle")
    return el_id


def text(cx, cy, content, size=16, color="#1e1e1e", align="left", vertical="top", bold=False):
    lines = content.split("\n")
    line_height = size * 1.25
    total_h = line_height * len(lines)
    width = max(len(line) for line in lines) * size * 0.6
    x = cx - width / 2 if align == "center" else cx
    y = cy - total_h / 2 if vertical == "middle" else cy
    el_id = next_id("text")
    elements.append({
        "id": el_id, "type": "text", "x": x, "y": y, "width": width, "height": total_h,
        "angle": 0, "strokeColor": color, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid", "roughness": 1,
        "opacity": 100, "groupIds": [], "frameId": None, "roundness": None,
        "seed": seed(), "version": 1, "versionNonce": seed(), "isDeleted": False,
        "boundElements": [], "updated": 1, "link": None, "locked": False,
        "text": content, "fontSize": size, "fontFamily": 1,
        "textAlign": align, "verticalAlign": vertical, "baseline": total_h * 0.8,
        "containerId": None, "originalText": content, "lineHeight": 1.25,
    })
    return el_id


def arrow(points, stroke="#495057", dashed=False):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, y0 = xs[0], ys[0]
    rel_points = [[px - x0, py - y0] for px, py in points]
    el_id = next_id("arrow")
    elements.append({
        "id": el_id, "type": "arrow", "x": x0, "y": y0,
        "width": max(xs) - min(xs), "height": max(ys) - min(ys),
        "angle": 0, "strokeColor": stroke, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 2,
        "strokeStyle": "dashed" if dashed else "solid", "roughness": 1, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": {"type": 2}, "seed": seed(),
        "version": 1, "versionNonce": seed(), "isDeleted": False, "boundElements": [],
        "updated": 1, "link": None, "locked": False,
        "points": rel_points, "lastCommittedPoint": None,
        "startBinding": None, "endBinding": None,
        "startArrowhead": None, "endArrowhead": "arrow",
    })
    return el_id


# Title
text(700, 30, "CampusWise AI - System Architecture", size=28, align="center", bold=True)

# Client group
rect(40, 100, 220, 140, "#1971c2", "#a5d8ff", None)
text(150, 118, "CLIENT", size=13, color="#1864ab", align="center")
rect(60, 145, 180, 65, "#1971c2", "#e7f5ff", "Next.js\nFrontend", label_size=15)

# API group
rect(340, 100, 480, 360, "#2f9e44", "#b2f2bb", None)
text(580, 118, "FASTAPI BACKEND", size=13, color="#2b8a3e", align="center")
rect(365, 150, 200, 65, "#2f9e44", "#ebfbee", "REST API\nLayer", label_size=15)
rect(595, 150, 200, 65, "#2f9e44", "#ebfbee", "LangGraph Agent\nOrchestration", label_size=14)
rect(365, 245, 430, 80, "#2f9e44", "#ebfbee",
     "Services\nranking - optimization - analytics - degree planning", label_size=14)
rect(365, 355, 430, 65, "#2f9e44", "#ebfbee", "Repositories", label_size=15)

# Data group
rect(900, 100, 460, 360, "#e03131", "#ffc9c9", None)
text(1130, 118, "DATA LAYER", size=13, color="#c92a2a", align="center")
ellipse(915, 155, 190, 90, "#e03131", "#fff5f5", "PostgreSQL\n(core schema)", label_size=14)
ellipse(1165, 155, 190, 90, "#e03131", "#fff5f5", "Redis Cache", label_size=15)
ellipse(985, 315, 280, 100, "#e03131", "#fff5f5", "pgvector\n(syllabus / semantic search)", label_size=14)

# Ingestion group
rect(340, 500, 580, 150, "#f08c00", "#ffec99", None)
text(630, 518, "INGESTION", size=13, color="#e8590c", align="center")
rect(365, 550, 230, 70, "#f08c00", "#fff9db", "Ingestion\nPipelines", label_size=15)
ellipse(690, 550, 190, 70, "#f08c00", "#fff9db", "Raw Storage", label_size=15)

# Guardrail note
rect(40, 500, 260, 150, "#7048e8", "#e5dbff", None)
text(60, 518, "GUARDRAIL", size=13, color="#5f3dc4")
text(60, 545,
     "LLM is confined to two jobs:\n"
     "1. NL -> structured constraints\n"
     "2. Verified facts -> explanation\n"
     "Everything else is\ndeterministic code.",
     size=13, color="#343a40")

# Arrows
arrow([(260, 178), (360, 178)])  # FE <-> REST
arrow([(360, 178), (260, 178)])
arrow([(565, 182), (595, 182)])  # REST -> Agents
arrow([(465, 215), (465, 245)])  # REST -> Services
arrow([(695, 215), (695, 245)])  # Agents -> Services
arrow([(580, 325), (580, 355)])  # Services -> Repositories
arrow([(797, 380), (900, 260), (995, 210)])  # Repositories -> Postgres
arrow([(797, 285), (1150, 260), (1220, 220)])  # Services -> Redis
arrow([(797, 210), (1050, 240), (1050, 300)], stroke="#1971c2")  # Agents -> pgvector
arrow([(595, 585), (690, 585)])  # Ingestion -> Raw Storage
arrow([(850, 555), (950, 430), (1000, 250)])  # Raw Storage -> Postgres
arrow([(880, 570), (990, 470), (1050, 400)], stroke="#1971c2")  # Ingestion -> pgvector

# Legend
rect(40, 690, 1320, 170, "#adb5bd", "#f8f9fa")
text(65, 705, "Legend", size=15, bold=True)
arrow([(65, 745), (110, 745)])
text(120, 738, "Deterministic call / data flow", size=13)
arrow([(430, 745), (475, 745)], stroke="#1971c2")
text(485, 738, "Vector / semantic retrieval path", size=13)
text(65, 775,
     "Client -> REST -> (Agents + Services) -> Repositories -> PostgreSQL / Redis / pgvector\n"
     "Ingestion pipelines write raw source data into PostgreSQL and embeddings into pgvector, independent of live request traffic.\n"
     "See docs/architecture-proposal.md for the full product, AI, database, and API architecture.",
     size=12, color="#495057")

document = {
    "type": "excalidraw",
    "version": 2,
    "source": "https://github.com/HARSHAVELU/campuswise-ai",
    "elements": elements,
    "appState": {
        "gridSize": 20,
        "viewBackgroundColor": "#ffffff",
    },
    "files": {},
}

with open("docs/architecture-diagram.excalidraw", "w", encoding="utf-8") as f:
    json.dump(document, f, indent=2)

print(f"Wrote {len(elements)} elements to docs/architecture-diagram.excalidraw")
