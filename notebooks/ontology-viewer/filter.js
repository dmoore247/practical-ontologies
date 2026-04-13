// ════════════════════════════════════════════════════════════════════════════
// filter.js — Injected into PyVis HTML by the Domain Ontology Viewer notebook
// ════════════════════════════════════════════════════════════════════════════
//
// Section 1: Null-safe getElementById shim  (runs immediately)
// Section 2: Layer filter panel logic       (polls for vis.js network)
//
// Both sections are wrapped in IIFEs for isolation. The entire file is
// injected into <head> as a single <script> block. Section 2 polls until
// the vis.js `network`, `nodes`, and `edges` globals exist (created later
// in <body> by PyVis).
// ════════════════════════════════════════════════════════════════════════════


// ── Section 1: Null-safe getElementById shim ─────────────────────────────
// PyVis's stabilization handlers call getElementById('bar'), ('text'),
// ('loadingBar'), ('border') which can return null in the Databricks
// displayHTML() iframe, causing:
//   "Cannot read properties of null (reading 'removeAttribute')"
// This shim returns a harmless dummy <div> for those IDs instead of null.
// ─────────────────────────────────────────────────────────────────────────

(function() {
    var _orig = document.getElementById.bind(document);
    var _safeIds = { loadingBar: 1, bar: 1, text: 1, border: 1 };
    var _dummy  = document.createElement('div');
    _dummy.style.cssText = 'display:none;width:0;height:0;opacity:0;';
    _dummy.innerHTML = '0%';
    document.getElementById = function(id) {
        return _orig(id) || (id in _safeIds ? _dummy : null);
    };
})();


// ── Section 2: Layer filter panel ────────────────────────────────────────
// Discovers layer groups from the vis.js node DataSet, builds checkbox
// rows with FontAwesome icon swatches, and toggles visibility by
// removing / re-adding nodes + edges then re-running physics.
// ─────────────────────────────────────────────────────────────────────────

(function() {
    function init() {
        if (typeof network === 'undefined' || typeof nodes === 'undefined'
            || typeof edges === 'undefined') {
            return setTimeout(init, 200);
        }

        // ── Master copies of all nodes and edges (immutable reference) ──
        var allNodes = nodes.get();
        var allEdges = edges.get();

        // ── Discover groups + pick representative icon/color per group ──
        var groups = {};
        allNodes.forEach(function(n) {
            var g = n.group || 'Unknown';
            if (!groups[g]) {
                groups[g] = {
                    count: 0,
                    color: (n.icon && n.icon.color) || (typeof n.color === 'string' ? n.color : null) || '#888',
                    iconCode: (n.icon && n.icon.code) ? n.icon.code : '',
                    iconFace: (n.icon && n.icon.face) ? n.icon.face : 'FA7Solid',
                    iconWeight: (n.icon && n.icon.weight) ? n.icon.weight : '900'
                };
            }
            groups[g].count++;
        });

        // Track visibility per group
        var visibleGroups = {};
        Object.keys(groups).forEach(function(g) { visibleGroups[g] = true; });

        // Sort: HUB first, then alphabetical
        var keys = Object.keys(groups).sort(function(a, b) {
            if (a === 'HUB') return -1;
            if (b === 'HUB') return  1;
            return a.localeCompare(b);
        });

        var container = document.getElementById('filterRows');
        if (!container) return;

        keys.forEach(function(g) {
            var info = groups[g];

            var row = document.createElement('div');
            row.style.cssText = 'display:flex;align-items:center;padding:3px 4px;'
                + 'border-radius:4px;cursor:pointer;transition:background 0.15s;';
            row.onmouseenter = function() { this.style.background = 'rgba(255,255,255,0.08)'; };
            row.onmouseleave = function() { this.style.background = 'none'; };

            var cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.checked = true;
            cb.dataset.group = g;
            cb.style.cssText = 'margin:0 6px 0 0;cursor:pointer;accent-color:' + info.color + ';';
            cb.onchange = function() {
                visibleGroups[this.dataset.group] = this.checked;
                applyFilters();
            };

            // FontAwesome icon swatch instead of colored dot
            var swatch = document.createElement('span');
            swatch.style.cssText = 'display:inline-block;width:16px;text-align:center;'
                + 'margin-right:6px;flex-shrink:0;font-size:13px;'
                + 'font-family:"' + info.iconFace + '";font-weight:' + info.iconWeight + ';'
                + 'color:' + info.color + ';';
            swatch.textContent = info.iconCode || '\uf111';  // fallback: fa-circle

            var lbl = document.createElement('span');
            lbl.style.cssText = 'color:#eee;font-size:12px;';
            lbl.textContent = g + ' (' + info.count + ')';

            row.appendChild(cb);
            row.appendChild(swatch);
            row.appendChild(lbl);
            container.appendChild(row);

            row.onclick = function(e) {
                if (e.target !== cb) { cb.checked = !cb.checked; cb.onchange(); }
            };
        });

        // ── Apply filters: clear DataSets, re-add visible, re-layout ──
        function applyFilters() {
            var visibleIds = new Set();
            allNodes.forEach(function(n) {
                if (visibleGroups[n.group || 'Unknown']) visibleIds.add(n.id);
            });

            var filteredNodes = allNodes.filter(function(n) {
                return visibleIds.has(n.id);
            });
            var filteredEdges = allEdges.filter(function(e) {
                return visibleIds.has(e.from) && visibleIds.has(e.to);
            });

            // Clear and rebuild DataSets — triggers physics re-layout
            nodes.clear();
            edges.clear();
            nodes.add(filteredNodes);
            edges.add(filteredEdges);

            // Re-run physics so remaining nodes settle into a clean layout
            network.stabilize(200);
        }

        // ── Button handlers ──
        document.getElementById('btnShowAll').onclick = function() {
            container.querySelectorAll('input[type=checkbox]').forEach(function(cb) {
                cb.checked = true;
                visibleGroups[cb.dataset.group] = true;
            });
            applyFilters();
        };
        document.getElementById('btnHideAll').onclick = function() {
            container.querySelectorAll('input[type=checkbox]').forEach(function(cb) {
                cb.checked = false;
                visibleGroups[cb.dataset.group] = false;
            });
            applyFilters();
        };
        document.getElementById('btnCenter').onclick = function() {
            network.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
        };
    }

    init();
})();
