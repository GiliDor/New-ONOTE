<!-- 7be6404f-f8d8-4d6b-96fc-11166eaec2ab cf73be7c-0595-4f04-a3fe-fde41f621c51 -->
# Uniform measure width reflow when staff-name width changes

## Changes

### 1) Share bar spacing per system

- File: `src/gui/music/score_renderer.py`
- In `render_score`, initialize `_unit_width_by_system = {}` and `_bar_positions_by_system = {}` per frame.
- In `_render_measures_impl`, compute `first_measure_barline_x` and `unit_width` for the given `system_idx`.
- Store: `_unit_width_by_system[system_idx] = unit_width` and `_bar_positions_by_system[system_idx] = [first_x + i*unit for i=1..mps]` only once (first staff of the system).

### 2) Consume shared bar positions everywhere

- File: `src/gui/music/score_renderer.py`
- In `_render_system_aware_barlines`, if `_bar_positions_by_system[system_idx]` exists, use those x positions instead of any model `end_x` when drawing, so all staves in the system stay uniform.
- Ensure staff end X (`staff_end_x`) is derived from `first_x + unit * num_measures_to_render` to match the shared spacing.

### 3) Invalidate on staff-name width changes

- File: `src/gui/music/score_renderer.py`
- In `_calculate_dynamic_staff_offsets`, after changing `barline_0_offset`, clear `_unit_width_by_system` and `_bar_positions_by_system` to force recomputation on the next frame.

### 4) Optional: notify temporal bridge (no-op safe)

- If `document.temporal_bridge` exposes refresh hooks, call them; otherwise, re-render is sufficient.

## Acceptance criteria

- Increasing Staff Names font size shifts barline 0 and re-computes a single unit width used for barlines 1..M across ALL staves in the system, yielding uniform sizes for measures 1..4 immediately.
- No clipping or drift; final barline stays anchored by the shared spacing.

### To-dos

- [ ] Center grand-staff name vertically and right-align via rect
- [ ] Include custom_name in dynamic width calculation with active font size
- [ ] Use barline_0_x as left bound for first-system measure layout if needed
- [ ] Add extra reserve for negative horizontal offset to avoid clipping