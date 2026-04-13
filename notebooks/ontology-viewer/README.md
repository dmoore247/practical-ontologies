# Pharma Domain Model — Ontology Viewer

An interactive RDF-driven ontology viewer for pharmaceutical pre-clinical domain models, built with **rdflib** and **PyVis**.

## Overview

This project visualizes a pharmaceutical domain model covering the Sample-Test-Result (STR) data lifecycle across 16 interconnected layers — from approved drugs and pipeline therapies down through molecular targets, lab workflows, assay types, and detection methods.

## Architecture

All styling is separated from domain data:

| File | Purpose |
| --- | --- |
| `pharma.ttl` | Domain model — classes, instances, and relationships (RDF Turtle) |
| `viz.ttl` | Style rules — maps each domain class and predicate to colors, sizes, and icons |
| `viewer.py` | Databricks notebook — loads TTL files with rdflib, builds PyVis network |
| `filter-panel.html` | Filter panel UI — layer checkboxes, show/hide controls |
| `filter.js` | Filter logic — vis.js DataSet API integration, null-safety shim |
| `domain_model.html` | Generated output — standalone interactive graph |

## Domain Layers

| # | Label | Color | Description |
| --- | --- | --- | --- |
| 1 | HUB | Gold | Pharmaceutical company (hub node) |
| 2 | APPROVED | Green | Approved drug products |
| 3 | PIPELINE | Yellow | Pipeline therapies |
| 4 | DISEASE | Steel Blue | Disease indications |
| 5 | TARGET | Teal | Molecular targets |
| 6 | MODALITY | Purple | Treatment modalities |
| 7 | LAB | Forest Green | Lab workflow entities |
| 7b | ADME | Dark Turquoise | ADME assays |
| 7c | TOX | Yellow | Toxicity assays and endpoints |
| 8 | COMP | Slate Gray | Computational methods |
| 9 | ONTOLOGY | Peru | Ontology sources (BAO, AFO, OBI, NCIT, etc.) |
| 10 | STYPE | Lime Green | Sample types |
| 10 | TTYPE | Dodger Blue | Test types |
| 10 | APPL | Yellow | Applicability matrix |
| 11 | DetMethod | Hot Pink | Detection methods |
| 12 | Readout | Slate Blue | Readout content and dimensions |

## How It Works

1. `viewer.py` loads `pharma.ttl` (domain) and `viz.ttl` (styles) with rdflib
2. Style rules are extracted from `viz.ttl` — node colors, sizes, and Font Awesome icons are all RDF-driven
3. A PyVis network is built from domain triples, with edge styles also from RDF
4. The generated HTML is patched to inject the filter panel, vis.js group configs, and a font-ready redraw callback
5. The filter panel auto-discovers layers at runtime from the vis.js node DataSet

## Dependencies

- Python 3.12+
- [rdflib](https://rdflib.readthedocs.io/) — RDF graph parsing
- [pyvis](https://pyvis.readthedocs.io/) — interactive network visualization

