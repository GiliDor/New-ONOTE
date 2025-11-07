# ONOTE Structure Hierarchy & Terminology Reference

**Version:** Current Development  
**Date:** 2025  
**Purpose:** Common terminology and structure reference for ONOTE development

---

## 1. OVERALL ARCHITECTURE

```
ONOTE Application
├── Application Layer (main_multi_window.py)
│   ├── DocumentWindow (per-document window)
│   └── ApplicationManager (window management)
│
├── Document Layer (ScoreDocument)
│   ├── ScoreLayout (staff organization)
│   ├── Measures (temporal structure)
│   └── Settings (document-specific preferences)
│
├── Rendering Layer (ScoreRenderer)
│   ├── UniversalSystemManager (wrapping & pagination)
│   ├── PartNameRenderer (staff names)
│   └── MeasureNumberManager (measure numbering)
│
├── Temporal Layer (Temporal Grid System)
│   ├── TemporalGridSystem (timeline management)
│   ├── TemporalBridgeV2 (barline/measure bridge)
│   └── MeasureManager (layout & justification)
│
└── UI Layer (StaffView, Dialogs, Widgets)
    ├── StaffView (main score display)
    ├── ScoreSetupDialog (staff configuration)
    ├── FullScoreOptionsDialog (score-wide settings)
    └── FormWidget (barline/measure tools)
```

---

## 2. DOCUMENT STRUCTURE

### 2.1 ScoreDocument
**Location:** `src/gui/music/score_document.py`

**Purpose:** Top-level document container managing all score data

**Key Components:**
- `layout: ScoreLayout` - Staff organization and layout
- `measures: Dict[int, MeasureObject]` - All measures in the score (keyed by measure number)
- `settings: Dict` - Document-specific settings (override Preferences)
- `view_mode: str` - "page", "continuous", "page_across", "page_down"
- `filename: Optional[str]` - File path if saved
- `is_modified: bool` - Track unsaved changes

**Modes:**
- **Setup Mode:** Initial configuration (pink background)
- **Edit Mode:** Active notation editing (white background)

---

### 2.2 ScoreLayout
**Location:** `src/gui/music/staff_types.py`

**Purpose:** Organizes staves into logical groups

**Structure:**
```
ScoreLayout
├── ungrouped_staves: List[Staff]  # Single staves not in sections
└── sections: List[SectionGroup]     # Grouped staves (strings, woodwinds, etc.)
    └── staves: List[Staff]         # Staves within section
```

**Key Methods:**
- `set_setup_mode(bool)` - Switch between setup/edit modes
- `add_staff(staff)` - Add staff to layout
- `remove_staff(staff)` - Remove staff from layout

---

## 3. STAFF SYSTEM HIERARCHY

### 3.1 Staff Types

#### SingleStaff
**Purpose:** Individual instrument staff (flute, violin, voice, etc.)

**Attributes:**
- `instrument_name: str` - Full name (e.g., "Flute")
- `instrument_abbr: str` - Abbreviation (e.g., "Fl.")
- `clef: str` - "treble", "bass", "alto", "tenor", "percussion"
- `key: str` - Key signature
- `time_signature: str` - Time signature (e.g., "4/4")
- `y_position: float` - Vertical position on page
- `section: Optional[str]` - Section name if part of section

**Rendering:**
- Single 5-line staff
- Clef, key signature, time signature at start
- Staff name/abbreviation on left

---

#### GrandStaff
**Purpose:** Keyboard instruments (piano, organ, etc.)

**Structure:**
```
GrandStaff
├── top_staff: SingleStaff      # Treble clef (right hand)
├── bottom_staff: SingleStaff    # Bass clef (left hand)
├── brace_y_start: float        # Brace top position
├── brace_y_end: float          # Brace bottom position
└── instrument_name_y: float    # Name vertical position
```

**Attributes:**
- `instrument_name: str` - Full name (e.g., "Piano")
- `instrument_abbr: str` - Abbreviation (e.g., "Pn.")
- `key: str` - Shared key signature
- `time_signature: str` - Shared time signature
- `y_position: float` - Base vertical position (top staff)

**Rendering:**
- Two 5-line staves connected by brace
- Clefs on each staff
- Shared key signature and time signature
- Staff name centered between staves

---

#### SectionGroup
**Purpose:** Group of related instruments (strings, woodwinds, brass, etc.)

**Structure:**
```
SectionGroup
├── name: str                    # Section name (e.g., "Strings")
├── staves: List[Staff]          # Staves in section (can be SingleStaff or GrandStaff)
├── bracket_y_start: float      # Bracket top position
└── bracket_y_end: float       # Bracket bottom position
```

**Rendering:**
- Bracket connects all staves in section
- Section name displayed above bracket
- Individual staff names/abbreviations per staff

---

### 3.2 Staff System Terminology

**Staff System:** A single horizontal line of music notation
- **Single Staff System:** One staff (e.g., flute)
- **Grand Staff System:** Two staves braced together (e.g., piano)
- **Section System:** Multiple staves bracketed together (e.g., string quartet)

**Score System:** The complete vertical arrangement of all staff systems
- Contains all single staves, grand staves, and sections
- Wraps as a unit when measures exceed "measures per system"

**Wrapping:** When measures exceed the "measures per system" limit, the entire score system wraps to the next line
- Pattern repeats: System 1, System 2, System 3; System 1, System 2, System 3; etc.
- Spacing between wrapped systems controlled by "Wrapping Spacing" setting

---

## 4. TEMPORAL GRID SYSTEM

### 4.1 Temporal Structure

**Temporal Grid:** The underlying timeline for all musical content
- **PPQN (Pulses Per Quarter Note):** Resolution (96, 192, 480, or 960)
- **Tick:** Smallest time unit (1/PPQN of a quarter note)
- **Beat:** Musical beat (depends on time signature)
- **Measure:** Container bounded by barlines

**Measure:** Temporal container for notation
- **Measure Number:** Sequential identifier (1, 2, 3, ...)
- **Barline Type:** "single", "double", "final", "repeat", "dashed"
- **Time Signature:** Defines beats per measure
- **Content:** Notes, rests, chords, etc.

---

### 4.2 Barline System

**Barline 0:** The initial barline at the very left of all staff systems
- Connects all staves vertically (system-spanning)
- Always present (even in empty score)
- Position: `margins["left"] + barline_0_offset`
- Green number "0" displayed above (if enabled)

**Measure Barlines:** Barlines that divide measures
- Numbered sequentially (1, 2, 3, ...)
- Green numbers displayed above (if enabled)
- Position determined by measure justification

**Replicated Barline:** Barline at start of wrapped systems (system_idx > 0)
- **ONLY for multi-staff systems** (grand staff, sections)
- **NOT for single staff systems** (e.g., flute)
- Replicates the type of the last barline from previous system
- Position: `margins["left"] + max_offset` (aligned with barline 0)

**Final Barline:** Special barline marking end of score
- Thin line + thick line
- **ONLY on last measure of final system**
- **ONLY if measure has `barline_type == 'final'`**

---

### 4.3 Measure System

**MeasureObject:** Represents a single measure
- `measure_number: int` - Sequential number
- `barline_type: str` - Type of ending barline
- `start_x: float` - Left boundary
- `end_x: float` - Right boundary (barline position)
- `base_width: float` - Natural width based on content
- `justified_width: float` - Width after justification

**Measure Justification:** Automatic distribution of measures
- Measures distributed evenly across "Effective Notation Space"
- Effective Notation Space = page width - margins - clef/key/time space
- All measures in a system share the same unit width
- Wrapping occurs when "measures per system" limit reached

**Measures Per System (MPS):** Maximum measures per staff system
- Default: 4 measures per system
- When exceeded, entire score system wraps
- Controlled by Preferences or Full Score Options

---

## 5. RENDERING SYSTEM

### 5.1 ScoreRenderer
**Location:** `src/gui/music/score_renderer.py`

**Purpose:** Renders all musical notation elements

**Key Methods:**
- `render_score()` - Main rendering entry point
- `_render_single_staff()` - Render individual staff
- `_render_grand_staff()` - Render grand staff with wrapping
- `_render_system_aware_barlines()` - Render barlines with system awareness
- `_render_connecting_barlines()` - Render barline 0 (system-spanning)

**Rendering Order:**
1. Background (pink for setup, white for edit)
2. Staff lines
3. Clefs, key signatures, time signatures
4. Staff names/abbreviations
5. Measures and barlines
6. Measure numbers
7. Barline numbers
8. Notation elements (notes, rests, etc.)

---

### 5.2 UniversalSystemManager
**Location:** `src/gui/music/score_renderer.py` (nested class)

**Purpose:** Manages system layout, wrapping, and pagination

**Key Methods:**
- `calculate_system_info()` - Calculate systems per page, spacing, etc.
- `get_systems_to_render()` - Filter systems for current page
- `calculate_system_vertical_shift()` - Calculate Y position for system

**Pagination:**
- **Page-Down Mode:** One page at a time (default)
- **Page-Across Mode:** Multiple pages side-by-side
- **Continuous Mode:** All systems in one long scrollable view

**System Spacing:**
- **Staff Spacing:** Vertical spacing between staves in a section
- **Grand Staff Spacing:** Vertical spacing between treble and bass staves
- **System Spacing:** Vertical spacing between different staff systems
- **Wrapping Spacing:** Vertical spacing between wrapped score systems

---

### 5.3 PartNameRenderer
**Location:** `src/gui/music/score_layout.py`

**Purpose:** Renders staff names according to Preferences/Full Score Options

**Display Modes:**
- **Full Title:** Complete instrument name
- **Abbreviation:** Shortened name
- **None:** No name displayed

**System-Specific Behavior:**
- **First System (system_idx == 0):** Always shows full title (unless "None")
- **Wrapped Systems (system_idx > 0):** Shows abbreviation (if enabled)
- **Continuous View:** Respects display_mode setting directly

**Positioning:**
- Right-aligned to same position for all systems
- Position: `margins["left"] + max(name_offset, abbr_offset) - padding`
- Vertical: Centered on staff (or between staves for grand staff)

---

## 6. UI COMPONENTS

### 6.1 StaffView
**Location:** `src/gui/music/staff_view.py`

**Purpose:** Main widget displaying the score

**Key Features:**
- Page-based rendering with zoom support
- Mouse interaction (barline creation, selection)
- Element selection system
- View mode switching (page/continuous/page_across/page_down)

**Rendering Modes:**
- `_render_page_down_mode()` - Stacked pages (default)
- `_render_page_across_mode()` - Side-by-side pages
- `_render_continuous_mode()` - Single long scrollable view

---

### 6.2 ScoreSetupDialog
**Location:** `src/gui/music/score_setup_dialog.py`

**Purpose:** Configure staves before entering edit mode

**Features:**
- Add/remove staves
- Configure staff attributes (name, clef, key, time signature)
- Create grand staffs
- Create sections
- Reorder staves

**Mode:** Setup mode (pink background)

---

### 6.3 FullScoreOptionsDialog
**Location:** `src/gui/music/dialogs/full_score_options_dialog.py`

**Purpose:** Configure score-wide settings

**Tabs:**
- **Layout:** Staff names display, system spacing, wrapping spacing
- **Notation Setup:** Clef/key/time signature positions, offsets
- **Measure Numbers:** Display options, positioning
- **Fonts:** Font sizes and colors

**Settings Hierarchy:**
1. **Document Settings** (saved with document) - Highest priority
2. **Full Score Options** (current session) - Medium priority
3. **Preferences** (application-wide) - Lowest priority

**"Set as Defaults" Button:**
- Saves Full Score Options values to Preferences
- Affects all new documents

---

### 6.4 FormWidget
**Location:** `src/gui/music/widgets/form_widget.py`

**Purpose:** Tools for inserting barlines and measures

**Barline Types:**
- **Single Barline:** Standard barline (creates new measure)
- **Double Barline:** Visual separator
- **Final Barline:** End of score marker
- **Dashed Barline:** Visual separator (no measure division)
- **Repeat End:** Repeat sign at end
- **Repeat Both:** Repeat signs at start and end

**Operations:**
- **Insert Batch:** Create multiple measures at once
- **Apply Changes:** Modify existing barlines

---

## 7. KEY TERMINOLOGY

### 7.1 Spatial Terms

**Page:** Physical page dimensions (A4: 210mm × 297mm)

**Margins:** Space around page edges
- `top`, `bottom`, `left`, `right` (in pixels)

**Effective Notation Space:** Horizontal space available for measures
- `page_width - left_margin - right_margin - clef/key/time_space`

**Staff Lines:** The 5 horizontal lines of a staff
- **Top Line:** First line (highest)
- **Bottom Line:** Fifth line (lowest)
- **Middle Line:** Third line (center)

**Staff Height:** Vertical span of staff lines
- `(STAFF_LINE_COUNT - 1) × STAFF_LINE_SPACING`

---

### 7.2 Temporal Terms

**PPQN (Pulses Per Quarter Note):** Temporal resolution
- Standard values: 96, 192, 480, 960
- Higher = finer resolution

**Tick:** Smallest time unit
- `1 tick = 1/PPQN of a quarter note`
- Example: At PPQN=480, quarter note = 480 ticks

**Beat:** Musical beat (depends on time signature)
- In 4/4: 4 beats per measure, quarter note = 1 beat
- In 3/4: 3 beats per measure, quarter note = 1 beat

**Measure:** Container bounded by barlines
- Contains musical content (notes, rests, etc.)
- Duration determined by time signature

---

### 7.3 Layout Terms

**System:** A single horizontal line of music notation
- Can contain one staff (single staff system)
- Can contain multiple staves (grand staff or section system)

**Score System:** The complete vertical arrangement
- All single staves, grand staves, and sections
- Wraps as a unit when measures exceed MPS

**Wrapping:** When score system repeats on new line
- Pattern: 1, 2, 3; 1, 2, 3; 1, 2, 3; ...
- Spacing controlled by "Wrapping Spacing"

**Pagination:** Breaking score across multiple pages
- Systems per page calculated from page height and spacing
- Page breaks occur at system boundaries

**Justification:** Automatic distribution of measures
- Measures distributed evenly across available width
- All measures in system share same unit width

---

### 7.4 Barline Terms

**Barline 0:** Initial system-spanning barline
- Always present (even in empty score)
- Connects all staves vertically
- Position: `margins["left"] + barline_0_offset`

**Measure Barline:** Barline dividing measures
- Numbered sequentially (1, 2, 3, ...)
- Position determined by measure justification

**Replicated Barline:** Barline at start of wrapped systems
- **ONLY for multi-staff systems** (grand staff, sections)
- Replicates type of last barline from previous system
- Position: `margins["left"] + max_offset`

**Final Barline:** End-of-score marker
- Thin line + thick line
- **ONLY on last measure of final system**
- **ONLY if measure has `barline_type == 'final'`**

---

### 7.5 Staff Name Terms

**Full Title:** Complete instrument name
- Example: "Flute", "Piano", "Violin I"

**Abbreviation:** Shortened name
- Example: "Fl.", "Pn.", "Vln. I"
- Can be custom or auto-generated

**Display Mode:** When to show names
- **First System:** Always full title (unless "None")
- **Following Systems:** Abbreviation (if enabled)
- **Continuous View:** Respects display_mode setting

**Name Offset:** Horizontal space reserved for full title
- Used to calculate `barline_0_offset`

**Abbr Offset:** Horizontal space reserved for abbreviation
- Used for wrapped systems

**Max Offset:** Maximum of name_offset and abbr_offset
- Used to align all staff lines to same left position

---

## 8. SETTINGS HIERARCHY

### 8.1 Preferences (QSettings)
**Location:** Application-wide settings (persistent)

**Scope:** Affects all new documents

**Key Settings:**
- `layout/default_measures_per_system` - MPS default
- `layout/default_system_spacing` - System spacing
- `layout/default_wrapping_spacing` - Wrapping spacing
- `notation/staff_names_first_system` - First system display
- `notation/staff_names_following_systems` - Wrapped systems display
- `notation/continuous_staff_name_display` - Continuous view display

---

### 8.2 Document Settings
**Location:** `ScoreDocument.settings` (saved with document)

**Scope:** Document-specific overrides

**Priority:** Highest (overrides Preferences)

**Key Settings:**
- `layout/measures_per_system` - Document-specific MPS
- `notation/staff_names_first_system` - Document-specific display
- `notation/staff_names_following_systems` - Document-specific display
- `notation/continuous_staff_name_display` - Document-specific display

---

### 8.3 Full Score Options
**Location:** `FullScoreOptionsDialog` (current session)

**Scope:** Current editing session

**Priority:** Medium (overrides Preferences, can be saved to Document Settings)

**"Set as Defaults" Button:**
- Saves current values to Preferences
- Affects all new documents

---

## 9. COORDINATE SYSTEMS

### 9.1 Horizontal (X) Coordinates

**Page Left Edge:** `x = 0`

**Left Margin:** `x = margins["left"]`

**Barline 0 Position:**
- First system: `x = margins["left"] + barline_0_offset`
- Wrapped systems: `x = margins["left"] + abbr_offset`

**Staff Lines Start:**
- All systems: `x = margins["left"] + max_offset`
- Ensures alignment across all systems

**Clef Position:**
- `x = staff_left_x + clef_spacing_after_staff_start + clef_offset + effective_offset`
- `effective_offset` depends on view mode (page vs continuous)

**Right Margin:** `x = page_width - margins["right"]`

**Page Right Edge:** `x = page_width`

---

### 9.2 Vertical (Y) Coordinates

**Page Top Edge:** `y = 0`

**Top Margin:** `y = margins["top"]`

**Staff Y Position:** `y = staff.y_position`
- For grand staff: `y = grand_staff.y_position` (top staff)

**System Vertical Shift:**
- Page-down mode: `y = top_margin + (local_idx × system_advance)`
- Continuous mode: `y = system_idx × system_advance`

**Staff Lines:**
- Top line: `y = staff_y`
- Bottom line: `y = staff_y + (STAFF_LINE_COUNT - 1) × STAFF_LINE_SPACING`

**Bottom Margin:** `y = page_height - margins["bottom"]`

**Page Bottom Edge:** `y = page_height`

---

## 10. RENDERING FLOW

### 10.1 Main Rendering Path

```
StaffView.paintEvent()
  └─> StaffView._render_page_down_mode() [or _render_continuous_mode, _render_page_across_mode]
      └─> StaffView._render_single_page()
          └─> ScoreRenderer.render_score()
              ├─> ScoreRenderer._render_staff() [for each staff]
              │   ├─> ScoreRenderer._render_single_staff() [single staff]
              │   └─> ScoreRenderer._render_grand_staff() [grand staff]
              │       └─> ScoreRenderer._render_grand_staff_for_system() [per system]
              │
              ├─> ScoreRenderer._render_connecting_barlines() [barline 0]
              │
              ├─> MeasureNumberManager.render_measure_numbers() [measure numbers]
              │
              └─> ScoreRenderer._render_system_aware_barlines() [measure barlines]
```

---

### 10.2 System-Aware Rendering

**For Each System (system_idx):**
1. Calculate vertical shift for system
2. Update staff positions (for grand staff: top_staff.y_position, bottom_staff.y_position)
3. Render staff lines
4. Render clefs, key signatures, time signatures
5. Render staff names/abbreviations
6. Render measures and barlines
7. Render measure numbers
8. Render barline numbers

**Pagination Filtering:**
- `get_systems_to_render()` filters systems for current page
- Only systems on current page are rendered
- Vertical shift calculated relative to current page

---

## 11. KEY CONSTANTS

### 11.1 Staff Constants
- `STAFF_LINE_COUNT = 5` - Number of staff lines
- `STAFF_LINE_SPACING = 8.0` - Spacing between staff lines (pixels)
- `STAFF_HEIGHT = 32.0` - Total staff height (4 × 8.0)

### 11.2 Barline Constants
- `BARLINE_CONSTANTS["normal"]["thickness"] = 1` - Normal barline thickness
- `BARLINE_CONSTANTS["final"]["thickness"] = 4` - Final barline thickness

### 11.3 Default Spacing
- `default_system_spacing = 80` - Default spacing between systems
- `default_staff_spacing = 50` - Default spacing between staves in section
- `default_grand_staff_spacing = 32` - Default spacing between grand staff staves

---

## 12. COMMON PATTERNS

### 12.1 Detecting Staff Type
```python
# Grand staff
if hasattr(staff, 'is_grand_staff') and staff.is_grand_staff:
    # Handle grand staff

# Single staff
elif hasattr(staff, 'is_single_staff') and staff.is_single_staff:
    # Handle single staff

# Section staff
elif getattr(staff, 'section', None):
    # Handle section staff
```

### 12.2 Getting Staff Positions
```python
# Grand staff
top_y = grand_staff.top_staff.y_position
bottom_y = grand_staff.bottom_staff.y_position + STAFF_HEIGHT

# Single staff
staff_y = staff.y_position
```

### 12.3 Calculating Barline Span
```python
# Grand staff
top_y = grand_staff.top_staff.y_position
bottom_y = grand_staff.bottom_staff.y_position + STAFF_HEIGHT

# Section
top_y = section.staves[0].y_position
bottom_y = section.staves[-1].y_position + STAFF_HEIGHT

# Single staff
top_y = staff.y_position
bottom_y = staff.y_position + STAFF_HEIGHT
```

---

## 13. DEVELOPMENT NOTES

### 13.1 Mode Transitions
- **Setup → Edit:** User clicks "Apply" in Score Setup Dialog
- **Edit → Setup:** User clicks "Score Setup" button (reopens dialog)

### 13.2 Measure Creation
- **Initial State:** No measures (only barline 0)
- **First Measure:** Created when user inserts first barline
- **Subsequent Measures:** Created via Form Widget or barline insertion

### 13.3 Wrapping Behavior
- **Single Staff System:** Wraps independently
- **Grand Staff System:** Wraps as unit (both staves together)
- **Section System:** Wraps as unit (all staves together)
- **Full Score System:** All systems wrap together (1, 2, 3; 1, 2, 3; ...)

### 13.4 Pagination Behavior
- **Page-Down Mode:** One page at a time, scroll to see more
- **Page-Across Mode:** Multiple pages side-by-side
- **Continuous Mode:** All systems in one long scrollable view

---

## END OF DOCUMENT

**Last Updated:** 2025  
**Maintained By:** Development Team  
**For Questions:** Refer to codebase or development team

