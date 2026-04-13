# Databricks notebook source
# MAGIC %pip install pyvis rdflib -q

# COMMAND ----------

# DBTITLE 0,Restart Python for pyvis
# MAGIC %restart_python

# COMMAND ----------

# DBTITLE 1,Domain Model Overview
# MAGIC %md
# MAGIC ## PhramaCorp Domain Model — RDF-Driven Ontology Viewer
# MAGIC
# MAGIC This notebook reads two RDF Turtle files with **rdflib**, merges them, and renders an interactive **PyVis** visualization.
# MAGIC
# MAGIC | Input File | Purpose |
# MAGIC | --- | --- |
# MAGIC | `pharma.ttl` | Domain model — classes, instances, and relationships across 16 layers |
# MAGIC | `viz.ttl` | Style rules — maps each domain class and predicate to colors, sizes, and shapes |
# MAGIC
# MAGIC ### Domain Layers
# MAGIC
# MAGIC | # | Label | Color | Domain Class | Description |
# MAGIC | --- | --- | --- | --- | --- |
# MAGIC | 1 | **HUB** | Gold | `owl:NamedIndividual` | Pharmaceutical Company (hub node) |
# MAGIC | 2 | **APPROVED** | Crimson | `ent:ApprovedTreatment` | Trikafta, Kalydeco, Orkambi, Symdeko, Alyftrek, Casgevy, Journavx |
# MAGIC | 3 | **PIPELINE** | Orange-Red | `ent:PipelineTherapy` | VX-880, Inaxaplin, mRNA CF, AAT programs |
# MAGIC | 4 | **DISEASE** | Steel Blue | `ent:DiseaseTarget` | CF, SCD, β-Thalassemia, Pain, T1D, Kidney Disease, AAT Deficiency |
# MAGIC | 5 | **TARGET** | Teal | `ent:MolecularTarget` | CFTR, NaV1.8, NaV1.7, APOL1, BCL11A, SERPINA1 |
# MAGIC | 6 | **MODALITY** | Purple | `ent:TreatmentModality` | Small molecule, Gene therapy, CRISPR, mRNA/LNP, Cell therapy |
# MAGIC | 7 | **LAB** | Forest Green | `ent:LabEntity` | Sample → Well → Plate → Assay → Result → Formulation |
# MAGIC | 7b | **ADME** | Dark Turquoise | `ent:ADMEAssay` | Absorption, Distribution, Metabolism, Excretion, Safety, PK |
# MAGIC | 7c | **TOX** | Orange-Red | `ent:ToxicityAssay` | Genotoxicity, Cytotoxicity, Organ Tox, In Vivo Tox |
# MAGIC | 7c | **TOX_ENDPOINT** | Tomato | `ent:ToxicityEndpoint` | CC50, % Viability, % Cytotoxicity, LD50 |
# MAGIC | 8 | **COMP** | Slate Gray | `ent:ComputationalMethod` | Docking, MD, Cheminformatics, Virtual Screening |
# MAGIC | 9 | **ONTOLOGY** | Peru | `ent:OntologySource` | BAO, AFO, OBI, NCIT, ChEBI, MeSH, EDAM, DRON, MONDO |
# MAGIC | 10 | **STYPE** | Lime Green | `ent:SampleType` | Compound, Formulation, Biologic, Cell Line, Tissue, Blood, LNP |
# MAGIC | 10 | **TTYPE** | Dodger Blue | `ent:TestType` | Assay Format, Campaign Stage, Bioassay Type |
# MAGIC | 10 | **APPL** | Yellow | `ent:ApplicabilityGovernance` | Test Applicability Matrix |
# MAGIC | 11 | **DetMethod** | Hot Pink | `ent:DetectionMethod` | Fluorescence, Luminescence, Mass Spec, Imaging, Label-Free |
# MAGIC | 12 | **Readout** | Slate Blue | `ent:ReadoutDimension` | Content, Throughput, Measurement Type, Readout Type |
# MAGIC
# MAGIC **Ontology Sources**: BAO, AFO, OBI, NCIT, ChEBI, MeSH, EDAM, DRON, MONDO, SCDO, ECO, PR, HGNC

# COMMAND ----------

# DBTITLE 1,Interactive Filter Controls
# MAGIC %md
# MAGIC ## Interactive Filter Controls
# MAGIC
# MAGIC The visualization includes a **dynamic filter control panel** that auto-discovers layer groups at runtime from the vis.js node DataSet:
# MAGIC
# MAGIC * **Layer checkboxes** — one per group, color-coded swatch with node count, click row or checkbox to toggle
# MAGIC * **Show All / Hide All** — bulk toggle every dimension in one click
# MAGIC * **Center** — fit the viewport to visible nodes with smooth animation
# MAGIC * **vis.js DataSet API** — toggling sets `hidden: true/false` on all nodes in that group; vis.js automatically hides connected edges
# MAGIC
# MAGIC The panel is **fully data-driven** — if you add a new class to `pharma.ttl` and a matching `viz:StyleRule` to `viz.ttl`, it appears in the filter panel automatically. The null-safe stabilization fix prevents the `TypeError` that occurs in Databricks `displayHTML()` iframe context.

# COMMAND ----------

# MAGIC %md
# MAGIC ## RDF driven styling
# MAGIC The viz.ttl drives the styling of each layer.

# COMMAND ----------

# DBTITLE 1,Render interactive PyVis graph
from html import escape
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD

# ════════════════════════════════════════════════════════════════════════════
# 1. LOAD & PARSE — pharma.ttl (domain) + viz.ttl (styles)
# ════════════════════════════════════════════════════════════════════════════

BASE = "."

g_domain = Graph()
g_domain.parse(f"{BASE}/pharma.ttl", format="turtle")

g_viz = Graph()
g_viz.parse(f"{BASE}/viz.ttl", format="turtle")

# Namespaces
VIZ = Namespace("http://example.com/pharma/viz#")
ENT = Namespace("http://example.com/pharma/entities#")

# ════════════════════════════════════════════════════════════════════════════
# 2. EXTRACT STYLE RULES from viz.ttl
#    All styling comes from RDF — no hardcoded shapes or colors in Python.
# ════════════════════════════════════════════════════════════════════════════

# ── Node styles: viz:appliesTo → ent:Class → style dict ───────────────────
node_styles = {}   # {URIRef → {label, color, childSize, parentSize, iconCode, iconFace, iconWeight}}
hub_style = None

for rule in g_viz.subjects(RDF.type, VIZ.StyleRule):
    applies_to = g_viz.value(rule, VIZ.appliesTo)
    label = str(g_viz.value(rule, RDFS.label) or "")
    color = str(g_viz.value(rule, VIZ.color) or "#888888")
    child_sz_v = g_viz.value(rule, VIZ.childSize)
    parent_sz_v = g_viz.value(rule, VIZ.parentSize)
    child_sz = int(child_sz_v.toPython()) if child_sz_v else 22
    parent_sz = int(parent_sz_v.toPython()) if parent_sz_v else 22
    icon_code = str(g_viz.value(rule, VIZ.iconCode) or "")
    icon_face = str(g_viz.value(rule, VIZ.iconFace) or "Font Awesome 7 Free")
    icon_weight = str(g_viz.value(rule, VIZ.iconWeight) or "900")

    # Skip rules that are edge styles (no iconCode) or the meta-class itself
    if not icon_code and not applies_to and label != "HUB":
        continue

    style = dict(label=label, color=color, childSize=child_sz,
                 parentSize=parent_sz, iconCode=icon_code, iconFace=icon_face,
                 iconWeight=icon_weight)

    if applies_to:
        node_styles[applies_to] = style
    elif label == "HUB":
        hub_style = style

# ── Edge styles: viz:appliesToPredicate → predicate → style dict ─────────
edge_styles = {}   # {URIRef → {color, width, dashed}}
edge_default = dict(color="#555555", width=1.5, dashed=False)

for rule in g_viz.subjects(RDF.type, VIZ.StyleRule):
    pred = g_viz.value(rule, VIZ.appliesToPredicate)
    if pred:
        color = str(g_viz.value(rule, VIZ.color) or "#555555")
        w = g_viz.value(rule, VIZ.width)
        width = float(w.toPython()) if w else 1.5
        d = g_viz.value(rule, VIZ.dashed)
        dashed = bool(d.toPython()) if d else False
        edge_styles[pred] = dict(color=color, width=width, dashed=dashed)
    elif not g_viz.value(rule, VIZ.appliesTo):
        lbl = g_viz.value(rule, RDFS.label)
        if lbl and str(lbl) == "Default edge style":
            c = str(g_viz.value(rule, VIZ.color) or "#555555")
            wv = g_viz.value(rule, VIZ.width)
            edge_default = dict(color=c, width=float(wv.toPython()) if wv else 1.5, dashed=False)

print(f"✓ Domain model : {len(g_domain):,} triples")
print(f"✓ Viz rules    : {len(g_viz):,} triples")
print(f"  Node styles  : {len(node_styles)} class rules + HUB")
print(f"  Edge styles  : {len(edge_styles)} predicate rules + default")
print()
for cls, sty in sorted(node_styles.items(), key=lambda x: x[1]['label']):
    print(f"  {sty['label']:18s} iconCode={sty['iconCode']!r}  color={sty['color']}  weight={sty['iconWeight']}")
if hub_style:
    print(f"  {'HUB':18s} iconCode={hub_style['iconCode']!r}  color={hub_style['color']}  weight={hub_style['iconWeight']}")


# COMMAND ----------

# DBTITLE 1,Build PyVis network from domain model
from pyvis.network import Network
from collections import Counter
import json

# ════════════════════════════════════════════════════════════════════════════
# 3. BUILD PYVIS NETWORK from domain model + viz styles
#    All nodes use shape="icon" with Font Awesome 7 Free glyphs from viz.ttl.
# ════════════════════════════════════════════════════════════════════════════

net = Network(
    height="900px", width="100%", directed=True,
    bgcolor="#1a1a2e", font_color="white", notebook=False,
)
net.barnes_hut(
    gravity=-8000, central_gravity=0.35,
    spring_length=180, spring_strength=0.04,
    damping=0.09, overlap=0,
)
net.toggle_physics(True)

# ── Collect typed nodes from domain model ─────────────────────────────
domain_classes = set(node_styles.keys())
node_map = {}  # URI string → style/metadata dict

for s, _, o in g_domain.triples((None, RDF.type, None)):
    if o in domain_classes:
        nid = str(s)
        if nid in node_map:
            continue  # take first type for multi-typed nodes
        label = escape(str(g_domain.value(s, RDFS.label) or nid.split("#")[-1].split("/")[-1]))
        comment = escape(str(g_domain.value(s, RDFS.comment) or label))
        sty = node_styles[o]
        node_map[nid] = dict(
            label=label, comment=comment,
            group=sty["label"], color=sty["color"],
            size=sty["childSize"], parentSize=sty["parentSize"],
            iconCode=sty["iconCode"], iconFace=sty["iconFace"],
            iconWeight=sty["iconWeight"],
        )

# ── Handle HUB node (owl:NamedIndividual not typed as a domain class) ───
if hub_style:
    for s in g_domain.subjects(RDF.type, OWL.NamedIndividual):
        nid = str(s)
        if nid not in node_map:
            label = escape(str(g_domain.value(s, RDFS.label) or "Hub"))
            comment = escape(str(g_domain.value(s, RDFS.comment) or label))
            node_map[nid] = dict(
                label=label, comment=comment,
                group=hub_style["label"], color=hub_style["color"],
                size=hub_style["parentSize"], parentSize=hub_style["parentSize"],
                iconCode=hub_style["iconCode"], iconFace=hub_style["iconFace"],
                iconWeight=hub_style["iconWeight"],
            )

# ── Collect edges between domain nodes ────────────────────────────────
edge_list = []
pred_label_cache = {}
SKIP_PREDS = {RDF.type, RDFS.label, RDFS.comment, OWL.equivalentClass}

def get_pred_label(p):
    """Get a short edge label from the predicate URI."""
    if p not in pred_label_cache:
        lbl = g_domain.value(p, RDFS.label)
        if lbl:
            pred_label_cache[p] = escape(str(lbl))
        else:
            s = str(p)
            pred_label_cache[p] = escape(s.split("#")[-1].split("/")[-1])
    return pred_label_cache[p]

for s, p, o in g_domain:
    if p in SKIP_PREDS or isinstance(o, Literal):
        continue
    src, dst = str(s), str(o)
    if src in node_map and dst in node_map:
        es = edge_styles.get(p, edge_default)
        # Reverse subClassOf so arrow points parent → child
        # (RDF triple is child subClassOf parent; we flip for
        #  a top-down tree visual: parent ──▶ child)
        if p == RDFS.subClassOf:
            src, dst = dst, src
        edge_list.append(dict(
            src=src, dst=dst, label=get_pred_label(p),
            color=es["color"], width=es["width"], dashed=es["dashed"],
        ))

# ── Promote parent nodes (>=3 same-group outgoing edges → parentSize) ──
same_grp_out = Counter()
for e in edge_list:
    sg = node_map.get(e["src"], {}).get("group")
    dg = node_map.get(e["dst"], {}).get("group")
    if sg and sg == dg:
        same_grp_out[e["src"]] += 1

for nid, cnt in same_grp_out.items():
    if cnt >= 3:
        node_map[nid]["size"] = node_map[nid]["parentSize"]

# ── Add nodes to PyVis (all use shape="icon" with FA 7 glyphs) ──────────
for nid, n in node_map.items():
    net.add_node(
        nid, label=n["label"], group=n["group"], color=n["color"],
        size=n["size"], shape="icon", title=n["comment"],
        icon={"face": n["iconFace"], "code": n["iconCode"],
              "size": n["size"], "color": n["color"],
              "weight": n["iconWeight"]},
        font={"size": 12, "color": "white"},
    )

# ── Patch per-node color: PyVis drops node-level color for icon shapes ──
node_id_to_color = {nid: n["color"] for nid, n in node_map.items()}
for node in net.nodes:
    rdf_color = node_id_to_color.get(node["id"])
    if rdf_color:
        node["color"] = rdf_color

# ── Build explicit vis.js groups config (injected into HTML in cell 8) ──
# Includes BOTH color AND icon properties so vis.js uses RDF colors for
# icon-shaped nodes instead of its default palette.
groups_config = {}
for cls, sty in node_styles.items():
    groups_config[sty["label"]] = {
        "color": {"background": sty["color"], "border": sty["color"],
                  "highlight": {"background": sty["color"], "border": sty["color"]},
                  "hover": {"background": sty["color"], "border": sty["color"]}},
        "font": {"color": "white"},
        "icon": {"color": sty["color"]},
    }
if hub_style:
    groups_config[hub_style["label"]] = {
        "color": {"background": hub_style["color"], "border": hub_style["color"],
                  "highlight": {"background": hub_style["color"], "border": hub_style["color"]},
                  "hover": {"background": hub_style["color"], "border": hub_style["color"]}},
        "font": {"color": "white"},
        "icon": {"color": hub_style["color"]},
    }

# ── Add edges to PyVis ───────────────────────────────────────────
for e in edge_list:
    net.add_edge(
        e["src"], e["dst"], label=e["label"], color=e["color"],
        width=e["width"], arrows="to", dashes=e["dashed"],
        font={"size": 8, "color": "#aaa", "strokeWidth": 0,
              "face": "Helvetica Neue, Helvetica, Arial, sans-serif"},
    )

# ── Summary ──────────────────────────────────────────────────────
print(f"✓ Network: {len(net.nodes)} nodes, {len(net.edges)} edges")
print(f"✓ Groups config: {len(groups_config)} (will be injected into HTML options)")
groups = Counter(n["group"] for n in node_map.values())
for g, c in sorted(groups.items(), key=lambda x: -x[1]):
    print(f"  {g:18s} {c:3d} nodes")

# COMMAND ----------

# DBTITLE 1,Render interactive PyVis graph with filter panel
import os
import re

user_dir = "."
out_path = os.path.join(user_dir, "domain_model.html")

# ════════════════════════════════════════════════════════════════════════════
# 1. READ EXTERNAL ASSETS — filter-panel.html + filter.js
# ════════════════════════════════════════════════════════════════════════════

with open(f"{BASE}/filter-panel.html", "r") as f:
    panel_html = f.read()

with open(f"{BASE}/filter.js", "r") as f:
    filter_js = f.read()

# Split panel HTML at the body-injection comment:
#   head_html  = FA CSS link + loading-bar CSS (injected into <head>)
#   body_html  = filter panel div              (injected into <body>)
SPLIT_MARKER = "<!-- ── Body Injection"
marker_pos = panel_html.index(SPLIT_MARKER)
head_html = panel_html[:marker_pos].strip()
body_html = panel_html[marker_pos:].strip()
body_html = body_html[body_html.index("<div"):]   # keep only the div

# Split filter.js at the Section 2 comment:
#   shim_js    = getElementById null-safety shim (must run BEFORE PyVis)
#   filter_body_js = filter-panel logic          (must run AFTER  PyVis)
JS_SPLIT = "// ── Section 2:"
js_split_pos = filter_js.index(JS_SPLIT)
shim_js = filter_js[:js_split_pos].strip()
filter_body_js = filter_js[js_split_pos:].strip()

# ════════════════════════════════════════════════════════════════════════════
# 2. SAVE PYVIS → PATCH → DISPLAY
#
#    IMPORTANT: replacement order matters! The shim_js comment block
#    contains the literal string "<body>" in a JS comment. We must
#    replace the real <body> tag FIRST, before injecting shim_js.
#
#    Injection points:
#      <body>   ← body_html (filter panel div)           [Step 1]
#      </head>  ← head_html (FA CSS) + shim_js            [Step 2]
#      options  ← merge groups_config into vis.js options [Step 3]
#      </body>  ← filter_body_js (filter rows logic)      [Step 4]
#      </body>  ← font-ready redraw (canvas fix)          [Step 5]
# ════════════════════════════════════════════════════════════════════════════

net.save_graph(out_path)

with open(out_path, "r") as f:
    html = f.read()

# Step 1: Inject filter panel div into <body> FIRST
#         (must happen before shim_js is added, because shim_js
#          contains '<body>' in a JS comment that would match)
html = html.replace("<body>", f"<body>\n{body_html}")

# Step 2: Inject head assets (FA CSS, @font-face) + getElementById shim
html = html.replace("</head>",
    f"{head_html}\n<script>\n{shim_js}\n</script>\n</head>")

# Step 3: Merge groups_config into the vis.js options JSON.
#         This preserves PyVis-generated physics/edges/interaction config
#         while adding explicit group styles (color + icon) so vis.js
#         doesn't fall back to its default palette for grouped icon nodes.
options_match = re.search(r'var options = (\{.*?\});', html, re.DOTALL)
if options_match:
    existing_options = json.loads(options_match.group(1))
    existing_options["groups"] = groups_config
    patched_options_str = json.dumps(existing_options)
    html = (html[:options_match.start(1)]
            + patched_options_str
            + html[options_match.end(1):])
    print(f"✓ Injected {len(groups_config)} groups into vis.js options")
    print(f"  Options keys: {list(existing_options.keys())}")
else:
    print("⚠ Could not find vis.js options block — groups not injected")

# Step 4: Inject filter-panel JS (runs AFTER PyVis creates network/nodes/edges)
# Step 5: Add font-ready callback to force vis-network canvas redraw
#         (webfonts load async; canvas doesn't auto-repaint like DOM)
font_ready_js = """
// ── Font-ready redraw: force vis-network to repaint after webfont loads ──
(function() {
    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(function() {
            if (typeof network !== 'undefined') {
                network.redraw();
            }
        });
    }
})();
"""

html = html.replace("</body>",
    f"<script>\n{filter_body_js}\n{font_ready_js}\n</script>\n</body>")

with open(out_path, "w") as f:
    f.write(html)

print(f"✓ Graph saved: {out_path}")
print(f"  Nodes: {len(net.nodes)}  |  Edges: {len(net.edges)}")
print(f"  Injected: filter-panel.html + filter.js (shim in head, logic in body)")
print(f"  Font alias: FA7Solid → fa-solid-900.woff2 (canvas-friendly)")
print(f"  Font-ready: document.fonts.ready → network.redraw()")

#with open(out_path, "r") as f:
#    displayHTML(f.read())
