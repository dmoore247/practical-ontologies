# Summary:
1. Build a notebook to display an ontology. Styling will be driven by viz.ttl
2. The business case is for a pharmaceutical pre-clinical phase and managing STR (Sample-Test-Result) data.

## Tech stack
1. Python 3.12
2. rdflib
3. pyvis
4. Font Awesome
5. Turtle syntax for RDFs
6. Must use mcp/api for Biological/Medical ontology references https://www.ebi.ac.uk/ols4/api/mcp or https://www.ebi.ac.uk/ols4/api-docs

## Rules:
1. Plan first
2. Research APIs before coding to them
3. Separate assets (.ttl, .py, .js, .html)
4. Keep the solution simple.
5. Update local memory with lessons learned.
6. viz.ttl represents visualization style information.
7. Do not mix style with domain with code. Don't embed rendering assumptions into python code.
8. Run linters before committing code.
9. Must run security review before committing code.
