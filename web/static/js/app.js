/**
 * Fix8 Web — main frontend controller.
 * Wires every UI element to REST endpoints and keeps visualization in sync.
 */

const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", () => {
    const state = { has_data: false, has_suggestions: false, can_undo: false, view: {} };

    // --- Visualizer ---
    const viz = new Fix8Visualizer();
    viz.onFixationUpdate = (index, x, y) => {
        postJSON("/api/action/update_fixation", { index, x, y })
            .then(handleResponse)
            .catch((e) => setStatus("Update failed", "#ef4444"));
    };

    // ============ Helpers ============
    const showLoader = () => $("loader").classList.add("active");
    const hideLoader = () => $("loader").classList.remove("active");

    const setStatus = (msg, color = "#22c55e") => {
        $("status-text").innerText = msg;
        const dot = $("status-dot");
        dot.style.background = color;
        dot.style.boxShadow = `0 0 8px ${color}`;
    };

    const postJSON = (url, body) =>
        fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: body ? JSON.stringify(body) : undefined,
        }).then((r) => r.json().then((j) => ({ status: r.status, data: j })));

    const postForm = (url, formData) =>
        fetch(url, { method: "POST", body: formData })
            .then((r) => r.json().then((j) => ({ status: r.status, data: j })));

    const handleResponse = ({ status, data }) => {
        hideLoader();
        if (status >= 400 || data.error) {
            setStatus(data.error || "Error", "#ef4444");
            return false;
        }
        if (data.state) applyState(data.state);
        setStatus(data.message || "OK");
        return true;
    };

    const getViewFlags = () => ({
        show_aois: $("view-aois").checked ? 1 : 0,
        show_saccades: $("view-saccades").checked ? 1 : 0,
        show_suggestions: $("view-suggestions").checked ? 1 : 0,
        show_numbers: $("view-numbers").checked ? 1 : 0,
    });

    const refreshRender = () => {
        const q = new URLSearchParams({ ...getViewFlags(), t: Date.now() });
        $("engine-render").src = `/api/render?${q.toString()}`;
    };

    const applyState = (s) => {
        state.has_data = !!s.has_data;
        state.has_suggestions = !!s.has_suggestions;
        state.can_undo = !!s.can_undo;

        $("fix-count").innerText = (s.fixations && s.fixations.length) || 0;

        // Statistics panel
        const stats = s.stats || {};
        $("stat-fix-count").innerText = stats.fixation_count ?? 0;
        $("stat-total-dur").innerText = stats.trial_duration_ms
            ? `${(stats.trial_duration_ms / 1000).toFixed(2)}s` : "—";
        $("stat-max-dur").innerText = stats.max_duration_ms
            ? `${stats.max_duration_ms.toFixed(0)}ms` : "—";
        $("stat-min-dur").innerText = stats.min_duration_ms
            ? `${stats.min_duration_ms.toFixed(0)}ms` : "—";
        $("stat-aoi-count").innerText = stats.aoi_count ?? 0;

        // Progress label
        if (s.has_data && s.fixations) {
            const total = s.fixations.length;
            const cur = s.current_fixation >= 0 ? s.current_fixation + 1 : 0;
            $("progress-label").innerText = `${cur} / ${total}`;
        } else {
            $("progress-label").innerText = "—";
        }

        // Empty state vs canvas
        $("empty-state").style.display = s.has_data ? "none" : "flex";
        $("interactive-grid").style.display = s.has_data ? "inline-block" : "none";

        // Button states
        $("btn-accept-all").disabled = !state.has_suggestions;
        $("btn-undo").disabled = !state.can_undo;

        // Visualizer data (for hover + drag math)
        viz.setData(s.fixations || []);
        if (s.has_data) refreshRender();
    };

    // ============ Initial state fetch ============
    fetch("/api/state").then(r => r.json()).then(applyState).catch(console.error);

    // ============ Data source ============
    $("btn-load-demo").addEventListener("click", () => {
        showLoader();
        setStatus("Loading demo…", "#fbbf24");
        postJSON("/api/load_demo").then(handleResponse);
    });

    $("upload-trial-input").addEventListener("change", (e) => {
        const f = e.target.files[0];
        if (!f) return;
        const fd = new FormData();
        fd.append("file", f);
        showLoader();
        setStatus("Uploading trial…", "#fbbf24");
        postForm("/api/upload/trial", fd).then(handleResponse);
        e.target.value = "";
    });

    $("upload-image-input").addEventListener("change", (e) => {
        const f = e.target.files[0];
        if (!f) return;
        const fd = new FormData();
        fd.append("file", f);
        showLoader();
        setStatus("Uploading image…", "#fbbf24");
        postForm("/api/upload/image", fd).then(handleResponse);
        e.target.value = "";
    });

    // ============ Navigation ============
    $("btn-prev").addEventListener("click", () => move("previous"));
    $("btn-next").addEventListener("click", () => move("next"));

    const move = (direction) =>
        postJSON("/api/action/move", { direction }).then(handleResponse);

    // ============ Undo ============
    $("btn-undo").addEventListener("click", () => {
        showLoader();
        postJSON("/api/action/undo").then(handleResponse);
    });

    // ============ Correction algorithms ============
    $("btn-detect-aoi").addEventListener("click", () => {
        showLoader();
        setStatus("Detecting AOIs…", "#fbbf24");
        postJSON("/api/aoi/detect", { level: "sub-line" }).then(handleResponse);
    });

    $("btn-run-algo").addEventListener("click", () => {
        const name = $("algo-select").value;
        const mode = document.querySelector('input[name="algo-mode"]:checked').value;
        showLoader();
        setStatus(`Running ${name} (${mode})…`, "#fbbf24");
        postJSON("/api/algorithm/run", { name, mode }).then(handleResponse);
    });

    $("btn-accept-all").addEventListener("click", () => {
        showLoader();
        postJSON("/api/action/accept_all_suggestions").then(handleResponse);
    });

    // ============ Filters ============
    $("btn-filter-lowpass").addEventListener("click", () => {
        const threshold = parseFloat($("filter-duration").value) || 80;
        showLoader();
        postJSON("/api/filter/lowpass", { threshold }).then(handleResponse);
    });

    $("btn-filter-highpass").addEventListener("click", () => {
        const threshold = parseFloat($("filter-duration").value) || 800;
        showLoader();
        postJSON("/api/filter/highpass", { threshold }).then(handleResponse);
    });

    $("btn-filter-outlier").addEventListener("click", () => {
        const threshold = parseFloat($("filter-outlier-std").value) || 2.5;
        showLoader();
        postJSON("/api/filter/outlier", { threshold }).then(handleResponse);
    });

    $("btn-filter-merge").addEventListener("click", () => {
        const duration_threshold = parseFloat($("merge-dur").value) || 50;
        const dispersion_threshold = parseFloat($("merge-disp").value) || 20;
        showLoader();
        postJSON("/api/filter/merge", { duration_threshold, dispersion_threshold }).then(handleResponse);
    });

    $("btn-filter-outside").addEventListener("click", () => {
        showLoader();
        postJSON("/api/filter/outside_screen").then(handleResponse);
    });

    // ============ Distortions ============
    const wireDistortion = (key, endpoint) => {
        const slider = $(`dist-${key}`);
        const valLabel = $(`dist-${key}-val`);
        slider.addEventListener("input", (e) => (valLabel.innerText = e.target.value));
        $(`btn-dist-${key}`).addEventListener("click", () => {
            const threshold = parseFloat(slider.value);
            showLoader();
            postJSON(endpoint, { threshold }).then(handleResponse);
        });
    };
    wireDistortion("noise", "/api/distort/noise");
    wireDistortion("slope", "/api/distort/slope");
    wireDistortion("offset", "/api/distort/offset");
    wireDistortion("shift", "/api/distort/shift");

    // ============ View toggles ============
    ["view-aois", "view-saccades", "view-suggestions", "view-numbers"].forEach((id) => {
        $(id).addEventListener("change", () => {
            if (state.has_data) refreshRender();
        });
    });

    // ============ Keyboard shortcuts ============
    document.addEventListener("keydown", (e) => {
        const tgt = e.target;
        if (tgt && (tgt.tagName === "INPUT" || tgt.tagName === "TEXTAREA" || tgt.tagName === "SELECT")) return;
        if (!state.has_data) return;

        // Ctrl+Z — undo
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
            e.preventDefault();
            $("btn-undo").click();
            return;
        }

        if (e.key === "ArrowLeft") { e.preventDefault(); move("previous"); return; }
        if (e.key === "ArrowRight") { e.preventDefault(); move("next"); return; }

        const k = e.key.toLowerCase();
        if (k === "a") {
            e.preventDefault();
            postJSON("/api/action/assign_line", { mode: "above" }).then(handleResponse);
            return;
        }
        if (k === "z") {
            e.preventDefault();
            postJSON("/api/action/assign_line", { mode: "below" }).then(handleResponse);
            return;
        }
        if (e.key === " " && state.has_suggestions) {
            e.preventDefault();
            postJSON("/api/action/accept_suggestion").then(handleResponse);
            return;
        }
        if (e.key === "Backspace" || e.key === "Delete") {
            e.preventDefault();
            const idx = viz.hoveredIndex >= 0 ? viz.hoveredIndex : null;
            if (idx !== null) {
                postJSON("/api/action/delete_fixation", { index: idx }).then(handleResponse);
            }
            return;
        }
        if (/^[1-9]$/.test(e.key)) {
            e.preventDefault();
            postJSON("/api/action/assign_line", { mode: "number", line: parseInt(e.key, 10) })
                .then(handleResponse);
        }
    });
});
