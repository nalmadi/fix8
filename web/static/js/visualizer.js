/**
 * Fix8Visualizer — client-side overlay for hover + drag on the SSR canvas.
 * The actual image is rendered by the backend. This class handles:
 *   - mapping mouse coords to image-space
 *   - detecting which fixation is being hovered
 *   - tooltip display
 *   - drag-and-drop to send updates via onFixationUpdate
 * Rendering refresh is owned by app.js.
 */
class Fix8Visualizer {
    constructor() {
        this.img = document.getElementById("engine-render");
        this.grid = document.getElementById("interactive-grid");
        this.tooltip = document.getElementById("tooltip");

        this.fixations = [];
        this.hoveredIndex = -1;
        this.isDragging = false;
        this.draggedIndex = -1;
        this.onFixationUpdate = null;

        this._setupEvents();
    }

    setData(fixations) {
        this.fixations = (fixations || []).map((f) => ({
            x_cord: Number(f.x_cord),
            y_cord: Number(f.y_cord),
            duration: Number(f.duration),
        }));
        this.hoveredIndex = -1;
        this.tooltip.style.opacity = "0";
    }

    _mousePos(e) {
        const rect = this.img.getBoundingClientRect();
        const nx = this.img.naturalWidth && rect.width ? this.img.naturalWidth / rect.width : 1;
        const ny = this.img.naturalHeight && rect.height ? this.img.naturalHeight / rect.height : 1;
        return {
            x: (e.clientX - rect.left) * nx,
            y: (e.clientY - rect.top) * ny,
            rawX: e.clientX,
            rawY: e.clientY,
        };
    }

    _setupEvents() {
        this.grid.addEventListener("mousedown", () => {
            if (this.hoveredIndex !== -1) {
                this.isDragging = true;
                this.draggedIndex = this.hoveredIndex;
            }
        });

        this.grid.addEventListener("mousemove", (e) => {
            if (!this.fixations.length) return;
            const pos = this._mousePos(e);

            if (this.isDragging && this.draggedIndex !== -1) {
                this.fixations[this.draggedIndex].x_cord = pos.x;
                this.fixations[this.draggedIndex].y_cord = pos.y;
                this.tooltip.style.opacity = "0";
                this.grid.style.cursor = "grabbing";
                return;
            }

            let found = -1;
            for (let i = this.fixations.length - 1; i >= 0; i--) {
                const f = this.fixations[i];
                const r = Math.min(Math.max(f.duration / 25, 6), 35) + 8;
                const dx = pos.x - f.x_cord;
                const dy = pos.y - f.y_cord;
                if (dx * dx + dy * dy <= r * r) {
                    found = i;
                    break;
                }
            }

            if (found !== this.hoveredIndex) {
                this.hoveredIndex = found;
                this.grid.style.cursor = found !== -1 ? "grab" : "crosshair";
                if (found === -1) this.tooltip.style.opacity = "0";
            }

            if (this.hoveredIndex !== -1 && !this.isDragging) {
                const f = this.fixations[this.hoveredIndex];
                this.tooltip.style.opacity = "1";
                this.tooltip.style.left = pos.rawX + 15 + "px";
                this.tooltip.style.top = pos.rawY + 15 + "px";
                this.tooltip.innerHTML = `
                    <div class="tip-title">Fixation ${this.hoveredIndex + 1}</div>
                    <div>X: <span>${f.x_cord.toFixed(1)}</span></div>
                    <div>Y: <span>${f.y_cord.toFixed(1)}</span></div>
                    <div>Duration: <span>${f.duration.toFixed(0)} ms</span></div>
                    <div class="tip-hint">Drag to reposition · Del to remove</div>
                `;
            }
        });

        const commit = () => {
            if (this.isDragging && this.draggedIndex !== -1 && this.onFixationUpdate) {
                const f = this.fixations[this.draggedIndex];
                this.onFixationUpdate(this.draggedIndex, f.x_cord, f.y_cord);
            }
            this.isDragging = false;
            this.draggedIndex = -1;
            this.grid.style.cursor = "crosshair";
        };

        this.grid.addEventListener("mouseup", commit);
        this.grid.addEventListener("mouseleave", () => {
            commit();
            this.hoveredIndex = -1;
            this.tooltip.style.opacity = "0";
        });
    }
}
