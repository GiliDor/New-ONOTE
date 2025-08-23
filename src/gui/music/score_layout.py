"""
Score Layout Module

Handles the layout of musical scores, including proper spacing between staves,
part names, grand staff braces, and system barlines.
"""

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QFont, QColor, QTransform, QBrush
from PyQt6.QtWidgets import QGraphicsItem
import math

from src.gui.music.notation_constants import (
    STAFF_LINE_SPACING,
    STAFF_HEIGHT,
    STAFF_LINE_COUNT,
    MUSIC_FONTS,
    FONT_SIZES,
    SYMBOL_MAP,
    SYSTEM_CONSTANTS,
    DEFAULT_STAFF_SPACING,
    DEFAULT_PAGE_MARGINS,
)
from src.gui.music.staff_types import StaffType


class StaffGroupRenderer:
    """
    Handles rendering of staff grouping symbols like brackets and braces.
    """

    @staticmethod
    def render_grand_staff_brace(painter, x, y_top, y_bottom, staves_midpoint=None):
        """
        Render a curly brace for a grand staff.

        Args:
            painter: QPainter instance
            x: X-coordinate for the brace
            y_top: Top Y-coordinate of the brace (top line of treble staff)
            y_bottom: Bottom Y-coordinate of the brace (bottom line of bass staff)
            staves_midpoint: Optional Y-coordinate for the midpoint between staves
        """
        # Save current state
        painter.save()

        # Set font for the brace - explicitly use Bravura font
        brace_font = QFont("Bravura")

        # Calculate font size based on the height
        height = y_bottom - y_top

        # If we have a custom midpoint, we need to adjust the height and positioning
        if staves_midpoint is not None:
            # Calculate how far the midpoint is from the original center
            original_center = (y_top + y_bottom) / 2
            offset = staves_midpoint - original_center

            # Increase the height to compensate for the shift
            height_adjustment = abs(offset) * 2.0  # Reduced from 2.5
            height += height_adjustment

            # Adjust the vertical positioning based on the direction of the offset
            vertical_position = staves_midpoint
        else:
            vertical_position = (y_top + y_bottom) / 2

        # Adjust scaling factor - reduce it to make the brace less bold
        font_size = height * 0.85  # Reduced from 1.0
        brace_font.setPointSizeF(font_size)
        painter.setFont(brace_font)

        # Use the brace character directly - uniE000 from Bravura font
        brace_char = "\uE000"  # SMuFL code for curly brace

        # Position the brace
        painter.translate(x, vertical_position)

        # Set text alignment for proper positioning
        rect = QRectF(-font_size / 2, -height / 2, font_size, height)
        flags = Qt.AlignmentFlag.AlignCenter
        painter.drawText(rect, flags, brace_char)

        # Restore original state
        painter.restore()

    @staticmethod
    def render_section_bracket(painter, x, y_top, y_bottom):
        """
        Render a bracket for a section using the SMuFL bracket characters.

        Args:
            painter: QPainter instance
            x: X-coordinate for the bracket
            y_top: Top Y-coordinate of the bracket
            y_bottom: Bottom Y-coordinate of the bracket
        """
        # Print debug information
        print(f"SECTION_BRACKET: Original positions - top: {y_top}, bottom: {y_bottom}")
        print(f"SECTION_BRACKET: Height: {y_bottom - y_top}")

        try:
            # Try the multi-part SMuFL glyph approach first
            # Save current state
            painter.save()

            # Set font for the bracket
            bracket_font = QFont("Bravura")
            bracket_font_size = 24.0  # Base font size
            bracket_font.setPointSizeF(bracket_font_size)
            painter.setFont(bracket_font)

            # Define the correct SMuFL glyphs
            bracket_top = "\uE003"  # bracketTop
            bracket_middle = "\uE034"  # bracketMiddle
            bracket_bottom = "\uE004"  # bracketBottom

            # Get font metrics for measurements
            metrics = painter.fontMetrics()

            # Calculate bracket height
            bracket_height = y_bottom - y_top

            # Get the height of each component
            top_height = metrics.height()
            middle_height = metrics.height()
            bottom_height = metrics.height()

            # STEP 1: Position the top bracket glyph precisely at the first line of the top staff
            # Draw only the top part at this stage, exactly at y_top
            painter.drawText(QPointF(x, y_top), bracket_top)
            print(f"SECTION_BRACKET: Top bracket positioned at y={y_top}")

            # STEP 2: Draw the middle segments with appropriate spacing
            # Check if this is a small section (typically 2 staves)
            is_small_section = bracket_height < 150

            if is_small_section:
                # For small sections, use exactly 7 middle segments with substantial overlap
                num_middle_segments = 7

                # Get the exact height of middle glyph for positioning
                middle_glyph_height = metrics.boundingRect(bracket_middle).height()

                # Calculate starting position - move down by a small amount from top bracket
                start_y = y_top + metrics.boundingRect(bracket_top).height() * 0.6

                # Use higher overlap (40%) for smaller sections to ensure continuous line
                y_step = middle_glyph_height * 0.6  # 60% of height, 40% overlap

                # Draw middle segments with substantial overlap
                for i in range(num_middle_segments):
                    pos_y = start_y + (i * y_step)
                    painter.drawText(QPointF(x, pos_y), bracket_middle)

                print(
                    f"SECTION_BRACKET: Small section middle segments drawn, count={num_middle_segments}"
                )
            else:
                # Standard handling for larger sections
                # Calculate how many middle segments needed
                overlap = 4  # Pixels of overlap between segments

                # Calculate total height with overlaps
                usable_height = bracket_height - (top_height - overlap) - (bottom_height - overlap)

                # Calculate number of middle segments needed
                num_middle_segments = math.ceil(usable_height / (middle_height - overlap))

                # Ensure at least one middle segment
                num_middle_segments = max(1, num_middle_segments)

                # Draw middle segments
                current_y = y_top + top_height - overlap

                for i in range(num_middle_segments):
                    painter.drawText(QPointF(x, current_y), bracket_middle)
                    current_y += middle_height - overlap

                print(
                    f"SECTION_BRACKET: Standard section middle segments drawn, count={num_middle_segments}"
                )

            # STEP 3: Position the bottom bracket glyph precisely at the bottom line
            # Place bracket_bottom precisely at the bottom
            painter.drawText(QPointF(x, y_bottom), bracket_bottom)
            print(f"SECTION_BRACKET: Bottom bracket positioned at y={y_bottom}")

            # Print completion message
            print(
                f"SECTION_BRACKET: All segments rendered - top at y={y_top}, bottom at y={y_bottom}"
            )

            # Restore original state
            painter.restore()
            return

        except Exception as e:
            print(
                f"SECTION_BRACKET: SMuFL multi-part glyph failed: {e}, falling back to custom drawing"
            )

        # If we get here, try the custom drawing approach as a fallback
        try:
            StaffGroupRenderer.custom_render_section_bracket(painter, x, y_top, y_bottom)
            print(f"SECTION_BRACKET: Bracket rendered using custom direct drawing")
        except Exception as e:
            print(f"SECTION_BRACKET: Custom drawing failed: {e}, using simple bracket")

            # Final fallback to simple bracket
            height = y_bottom - y_top
            staff_height = STAFF_LINE_SPACING * (STAFF_LINE_COUNT - 1)
            scale_factor = height / (staff_height * 4)  # Scale to a 4-staff height
            print(
                f"SECTION_BRACKET: Bracket rendered using simple scaling (scale factor: {scale_factor})"
            )

            # Draw bracket using simple path
            StaffGroupRenderer.render_bracket(painter, x, y_top, y_bottom)

        # Restore original state if not already done
        try:
            painter.restore()
        except:
            pass

    @staticmethod
    def custom_render_section_bracket(painter, x, y_top, y_bottom):
        """
        Render a section bracket using direct drawing commands instead of SMuFL glyphs.
        This provides a more reliable fallback rendering method.

        Args:
            painter: QPainter instance
            x: X-coordinate for the bracket
            y_top: Top Y-coordinate of the bracket
            y_bottom: Bottom Y-coordinate of the bracket
        """
        # Save current state
        painter.save()

        # Set pen for drawing the bracket
        pen = QPen(Qt.GlobalColor.black)
        pen.setWidthF(2.0)  # Thicker pen for visibility
        painter.setPen(pen)

        # Bracket dimensions
        bracket_width = 10  # Width of horizontal parts
        curve_radius = 3  # Radius of the curved corners

        # Draw the vertical line
        vertical_x = x
        painter.drawLine(vertical_x, y_top + curve_radius, vertical_x, y_bottom - curve_radius)

        # Draw the top horizontal part - extending to the right
        painter.drawLine(
            vertical_x + curve_radius, y_top, vertical_x + bracket_width - curve_radius, y_top
        )

        # Draw the bottom horizontal part - extending to the right
        painter.drawLine(
            vertical_x + curve_radius, y_bottom, vertical_x + bracket_width - curve_radius, y_bottom
        )

        # Draw the curved corners
        # Top-left curved corner
        painter.drawArc(vertical_x, y_top, 2 * curve_radius, 2 * curve_radius, 180 * 16, 90 * 16)

        # Top-right curved corner
        painter.drawArc(
            vertical_x + bracket_width - 2 * curve_radius,
            y_top,
            2 * curve_radius,
            2 * curve_radius,
            270 * 16,
            90 * 16,
        )

        # Bottom-left curved corner
        painter.drawArc(
            vertical_x,
            y_bottom - 2 * curve_radius,
            2 * curve_radius,
            2 * curve_radius,
            90 * 16,
            90 * 16,
        )

        # Bottom-right curved corner
        painter.drawArc(
            vertical_x + bracket_width - 2 * curve_radius,
            y_bottom - 2 * curve_radius,
            2 * curve_radius,
            2 * curve_radius,
            0,
            90 * 16,
        )

        print(
            f"SECTION_BRACKET: Custom bracket drawn from y={y_top} to y={y_bottom} (opening to the right)"
        )

        # Restore original state
        painter.restore()

    @staticmethod
    def render_bracket(painter, x, y_top, y_bottom):
        """
        Render a straight bracket for a section or instrument group (legacy method).

        Args:
            painter: QPainter instance
            x: X-coordinate for the bracket
            y_top: Top Y-coordinate of the bracket
            y_bottom: Bottom Y-coordinate of the bracket
        """
        # Save current state
        painter.save()

        # Set pen for drawing the bracket
        pen = QPen(Qt.GlobalColor.black)
        pen.setWidthF(SYSTEM_CONSTANTS["bracketWidth"])
        painter.setPen(pen)

        # Calculate the bracket dimensions
        bracket_width = SYSTEM_CONSTANTS["bracketWidth"] * 3

        # Draw the vertical line
        painter.drawLine(x, y_top, x, y_bottom)

        # Draw the horizontal serifs at top and bottom - extending to the right
        painter.drawLine(x, y_top, x + bracket_width, y_top)
        painter.drawLine(x, y_bottom, x + bracket_width, y_bottom)

        # Restore original state
        painter.restore()


class SystemBarlineRenderer:
    """
    Handles rendering of system barlines that span multiple staves.
    """

    @staticmethod
    def render_score_barlines(painter, score_layout, x_pos, barline_type="normal"):
        """
        Render barlines across the entire score at the given x position.

        Args:
            painter: QPainter instance
            score_layout: Dictionary containing score layout information
            x_pos: X-coordinate for the barline
            barline_type: Type of barline ('normal', 'double', 'final', etc.)
        """
        # Get top of first staff and bottom of last staff
        if not score_layout or "sections" not in score_layout or not score_layout["sections"]:
            return

        first_section = score_layout["sections"][0]
        last_section = score_layout["sections"][-1]

        if not first_section.get("staves") or not last_section.get("staves"):
            return

        top_staff = first_section["staves"][0]
        bottom_staff = last_section["staves"][-1]

        y_top = top_staff["y"]
        y_bottom = bottom_staff["y"] + STAFF_HEIGHT

        # Render the full score barline
        SystemBarlineRenderer.render_system_barline(painter, x_pos, y_top, y_bottom, barline_type)

    @staticmethod
    def render_section_barlines(painter, section, x_pos, barline_type="normal"):
        """
        Render barlines across an entire section at the given x position.

        Args:
            painter: QPainter instance
            section: Dictionary containing section layout information
            x_pos: X-coordinate for the barline
            barline_type: Type of barline ('normal', 'double', 'final', etc.)
        """
        if not section or "staves" not in section or not section["staves"]:
            return

        top_staff = section["staves"][0]
        bottom_staff = section["staves"][-1]

        y_top = top_staff["y"]
        y_bottom = bottom_staff["y"] + STAFF_HEIGHT

        # Render the section barline
        SystemBarlineRenderer.render_system_barline(painter, x_pos, y_top, y_bottom, barline_type)

    @staticmethod
    def render_grand_staff_barlines(painter, staves, x_pos, barline_type="normal"):
        """
        Render barlines across a grand staff (connecting both staves).

        Args:
            painter: QPainter instance
            staves: List of staff layout dictionaries in the grand staff
            x_pos: X-coordinate for the barline
            barline_type: Type of barline ('normal', 'double', 'final', etc.)
        """
        if not staves or len(staves) < 2:
            return

        top_staff = staves[0]
        bottom_staff = staves[-1]

        y_top = top_staff["y"]
        y_bottom = bottom_staff["y"] + STAFF_HEIGHT

        # Render the grand staff barline
        SystemBarlineRenderer.render_system_barline(painter, x_pos, y_top, y_bottom, barline_type)

    @staticmethod
    def render_system_barline(painter, x, y_top, y_bottom, barline_type="normal", is_selected=False):
        """
        Render a barline that spans multiple staves in a system.

        Args:
            painter: QPainter instance
            x: X-coordinate for the barline
            y_top: Top Y-coordinate of the barline
            y_bottom: Bottom Y-coordinate of the barline
            barline_type: Type of barline ('normal', 'double', 'final', etc.)
            is_selected: Whether the barline is currently selected
        """
        # Save current state
        painter.save()

        # Convert coordinates to float to ensure consistent handling
        x = float(x)
        y_top = float(y_top)
        y_bottom = float(y_bottom)

        # Set selection color if barline is selected
        if is_selected:
            painter.setPen(QPen(QColor("#FFA500")))  # Orange for selection
        else:
            painter.setPen(QPen(Qt.GlobalColor.black))

        if barline_type == "normal" or barline_type == "single":
            # Single barline
            pen = painter.pen()
            pen.setWidthF(1.0)
            painter.setPen(pen)
            painter.drawLine(QPointF(x, y_top), QPointF(x, y_bottom))

        elif barline_type == "double":
            # Double barline
            pen = painter.pen()
            pen.setWidthF(1.0)
            painter.setPen(pen)
            painter.drawLine(QPointF(x, y_top), QPointF(x, y_bottom))
            painter.drawLine(QPointF(x + 3, y_top), QPointF(x + 3, y_bottom))

        elif barline_type == "final":
            # Final barline (thin-thick)
            pen = painter.pen()
            pen.setWidthF(1.0)
            painter.setPen(pen)
            painter.drawLine(QPointF(x, y_top), QPointF(x, y_bottom))

            pen.setWidthF(3.0)
            painter.setPen(pen)
            painter.drawLine(QPointF(x + 3, y_top), QPointF(x + 3, y_bottom))

        elif barline_type == "dotted":
            # Dotted barline
            pen = painter.pen()
            pen.setWidthF(1.0)
            pen.setStyle(Qt.PenStyle.DotLine)
            painter.setPen(pen)
            painter.drawLine(QPointF(x, y_top), QPointF(x, y_bottom))

        elif barline_type == "repeat_start":
            # Repeat start barline
            # Draw thick line
            pen = painter.pen()
            pen.setWidthF(3.0)
            painter.setPen(pen)
            painter.drawLine(QPointF(x, y_top), QPointF(x, y_bottom))

            # Draw thin line
            pen.setWidthF(1.0)
            painter.setPen(pen)
            painter.drawLine(QPointF(x + 4, y_top), QPointF(x + 4, y_bottom))

            # Draw dots with correct positioning
            painter.setBrush(painter.pen().color())
            dot_x = x + 8

            # Calculate dot positions based on staff spacing
            staff_height = STAFF_LINE_SPACING * (STAFF_LINE_COUNT - 1)
            y = y_top
            while y < y_bottom - staff_height:
                # Draw dots for each staff - positioned exactly between staff lines
                # Top dot: exactly in the middle of the space between 2nd and 3rd staff lines
                dot_y1 = y + STAFF_LINE_SPACING + (STAFF_LINE_SPACING // 2)
                # Bottom dot: exactly in the middle of the space between 3rd and 4th staff lines
                dot_y2 = y + (2 * STAFF_LINE_SPACING) + (STAFF_LINE_SPACING // 2)

                painter.drawEllipse(QPointF(dot_x, dot_y1), 2.0, 2.0)
                painter.drawEllipse(QPointF(dot_x, dot_y2), 2.0, 2.0)

                # Move to next staff position
                y += staff_height + DEFAULT_STAFF_SPACING

        elif barline_type == "repeat_end":
            # Repeat end barline
            # Draw dots with correct positioning
            painter.setBrush(painter.pen().color())
            dot_x = x - 4

            # Calculate dot positions based on staff spacing
            staff_height = STAFF_LINE_SPACING * (STAFF_LINE_COUNT - 1)
            y = y_top
            while y < y_bottom - staff_height:
                # Draw dots for each staff - positioned exactly between staff lines
                # Top dot: exactly in the middle of the space between 2nd and 3rd staff lines
                dot_y1 = y + STAFF_LINE_SPACING + (STAFF_LINE_SPACING // 2)
                # Bottom dot: exactly in the middle of the space between 3rd and 4th staff lines
                dot_y2 = y + (2 * STAFF_LINE_SPACING) + (STAFF_LINE_SPACING // 2)

                painter.drawEllipse(QPointF(dot_x, dot_y1), 2.0, 2.0)
                painter.drawEllipse(QPointF(dot_x, dot_y2), 2.0, 2.0)

                # Move to next staff position
                y += staff_height + DEFAULT_STAFF_SPACING

            # Draw thin line
            pen = painter.pen()
            pen.setWidthF(1.0)
            painter.setPen(pen)
            painter.drawLine(QPointF(x, y_top), QPointF(x, y_bottom))

            # Draw thick line
            pen.setWidthF(3.0)
            painter.setPen(pen)
            painter.drawLine(QPointF(x + 4, y_top), QPointF(x + 4, y_bottom))

        elif barline_type == "repeat_both":
            # Repeat both (end and start)
            # Draw dots on both sides with correct positioning
            painter.setBrush(painter.pen().color())
            dot_x_left = x - 6
            dot_x_right = x + 14

            # Calculate dot positions based on staff spacing
            staff_height = STAFF_LINE_SPACING * (STAFF_LINE_COUNT - 1)
            y = y_top
            while y < y_bottom - staff_height:
                # Draw dots for each staff - positioned exactly between staff lines
                # Top dot: exactly in the middle of the space between 2nd and 3rd staff lines
                dot_y1 = y + STAFF_LINE_SPACING + (STAFF_LINE_SPACING // 2)
                # Bottom dot: exactly in the middle of the space between 3rd and 4th staff lines
                dot_y2 = y + (2 * STAFF_LINE_SPACING) + (STAFF_LINE_SPACING // 2)

                # Left dots (end repeat)
                painter.drawEllipse(QPointF(dot_x_left, dot_y1), 2.0, 2.0)
                painter.drawEllipse(QPointF(dot_x_left, dot_y2), 2.0, 2.0)

                # Right dots (start repeat)
                painter.drawEllipse(QPointF(dot_x_right, dot_y1), 2.0, 2.0)
                painter.drawEllipse(QPointF(dot_x_right, dot_y2), 2.0, 2.0)

                # Move to next staff position
                y += staff_height + DEFAULT_STAFF_SPACING

            # Draw thin lines
            pen = painter.pen()
            pen.setWidthF(1.0)
            painter.setPen(pen)
            painter.drawLine(QPointF(x + 2, y_top), QPointF(x + 2, y_bottom))
            painter.drawLine(QPointF(x + 10, y_top), QPointF(x + 10, y_bottom))

            # Draw thick lines
            pen.setWidthF(3.0)
            painter.setPen(pen)
            painter.drawLine(QPointF(x - 2, y_top), QPointF(x - 2, y_bottom))
            painter.drawLine(QPointF(x + 6, y_top), QPointF(x + 6, y_bottom))

        # Restore original state
        painter.restore()


class PartNameRenderer:
    """
    Handles rendering of part names to the left of staves.
    """

    @staticmethod
    def render_part_name(painter, name, x, y_center, is_grand_staff=False):
        """
        Render a part name to the left of a staff.

        Args:
            painter: QPainter instance
            name: Name of the part to render
            x: X-coordinate for the name
            y_center: Y-coordinate for the center of the name
            is_grand_staff: Whether this is a grand staff name
        """
        if not name:
            return

        # Save current state
        painter.save()

        # Set font for the part name
        name_font = QFont(MUSIC_FONTS["text"])
        name_font.setPointSize(FONT_SIZES["staffName"])
        painter.setFont(name_font)

        # Calculate the width of the text to determine positioning
        text_width = painter.fontMetrics().horizontalAdvance(name)

        # Draw the text horizontally, right-aligned for proper positioning
        # Note: no longer rotated vertically
        rect = QRectF(x - text_width - 10, y_center - 10, text_width, 20)
        flags = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        painter.drawText(rect, flags, name)

        # Restore original state
        painter.restore()

    @staticmethod
    def get_max_part_name_width(painter, part_names):
        """
        Calculate the maximum width needed for part names.

        Args:
            painter: QPainter instance
            part_names: List of part names

        Returns:
            Maximum width needed for part names
        """
        max_width = 0

        # Set font for measuring
        name_font = QFont(MUSIC_FONTS["text"])
        name_font.setPointSize(FONT_SIZES["staffName"])
        painter.setFont(name_font)

        # Calculate maximum width
        for name in part_names:
            if name:
                width = painter.fontMetrics().horizontalAdvance(name)
                max_width = max(max_width, width)

        # Add padding
        return max_width + 20  # 20px padding


class ScoreLayoutManager:
    """
    Manages the layout of staves, sections, and part groups in a score.
    """

    @staticmethod
    def organize_staves_into_sections(staves):
        """
        Organize staves into sections and groups based on their properties.

        Args:
            staves: List of staff objects

        Returns:
            Dictionary with sections and staff grouping information
        """
        sections = []
        current_section = {"staves": [], "groups": []}

        # Group by section and identify grand staves
        for i, staff in enumerate(staves):
            # Check if this is the start of a new section
            if i > 0 and getattr(staff, "start_new_section", False):
                # Add the completed section and start a new one
                if current_section["staves"]:
                    sections.append(current_section)
                    current_section = {"staves": [], "groups": []}

            # Add staff to current section
            current_section["staves"].append(staff)

            # Check if this staff is part of a grand staff
            group_id = getattr(staff, "group_id", None)
            if group_id:
                # Look for other staves with the same group ID
                grouped_staves = [
                    s for s in current_section["staves"] if getattr(s, "group_id", None) == group_id
                ]

                # Only create a new group if it doesn't exist
                existing_group = next(
                    (g for g in current_section["groups"] if g["id"] == group_id), None
                )

                if not existing_group and len(grouped_staves) > 1:
                    current_section["groups"].append(
                        {"id": group_id, "type": "grand_staff", "staves": grouped_staves}
                    )

        # Add the last section if it has staves
        if current_section["staves"]:
            sections.append(current_section)

        return {"sections": sections}

    @staticmethod
    def calculate_staff_positions(
        score_layout, start_y, staff_spacing, grand_staff_spacing, part_names_width=0
    ):
        """
        Calculate vertical positions for all staves in the score.

        Args:
            score_layout: Layout information with sections and groups
            start_y: Y-coordinate to start positioning
            staff_spacing: Spacing between individual staves
            grand_staff_spacing: Spacing between staves in a grand staff
            part_names_width: Width to reserve for part names

        Returns:
            Updated score_layout with y positions and a leftmost_staff_x value
        """
        current_y = start_y
        leftmost_staff_x = DEFAULT_PAGE_MARGINS["left"] + part_names_width

        # Add margin between part names and staves
        if part_names_width > 0:
            leftmost_staff_x += 10  # 10px margin

        # Process each section
        for section in score_layout["sections"]:
            section_start_y = current_y
            section["leftmost_staff_x"] = leftmost_staff_x

            # Keep track of the previous staff for proper spacing
            prev_staff = None

            # Process staves in this section
            for i, staff in enumerate(section["staves"]):
                # Determine if this staff is part of a grand staff group
                is_in_group = False
                is_first_in_group = False

                for group in section["groups"]:
                    if staff in group["staves"]:
                        is_in_group = True
                        is_first_in_group = group["staves"].index(staff) == 0
                        break

                # Apply different spacing based on grouping
                if i > 0:
                    if is_in_group and not is_first_in_group:
                        # Smaller spacing for staves within a group
                        current_y += grand_staff_spacing
                    else:
                        # Check if previous staff was a GrandStaff
                        if (
                            prev_staff
                            and hasattr(prev_staff, "type")
                            and getattr(prev_staff, "type", None) == StaffType.GRAND
                        ):
                            # Already added grand staff height and spacing in previous iteration
                            # Add extra spacing between grand staff and next staff
                            current_y += (
                                staff_spacing * 1.5
                            )  # Add 50% more spacing after a grand staff
                        else:
                            # Standard spacing between separate staves
                            current_y += staff_spacing

                # Store the position
                staff.position_y = current_y
                staff.position_x = leftmost_staff_x

                # Move to next position - check if current staff is a GrandStaff
                if hasattr(staff, "type") and getattr(staff, "type", None) == StaffType.GRAND:
                    # For GrandStaff, use the actual grand staff height
                    # This includes both staves and the spacing between them
                    if hasattr(staff, "height"):
                        current_y += staff.height
                    else:
                        # Fallback to 2 * STAFF_HEIGHT if height not available
                        current_y += 2 * STAFF_HEIGHT + grand_staff_spacing
                else:
                    # For single staves, just add standard staff height
                    current_y += STAFF_HEIGHT

                # Remember this staff for next iteration
                prev_staff = staff

            section["y"] = section_start_y
            section["height"] = current_y - section_start_y

            # Add extra spacing after section
            current_y += staff_spacing

        score_layout["leftmost_staff_x"] = leftmost_staff_x
        return score_layout

    def render_measure(self, painter, measure, x, y, staff_height):
        """Render a single measure with its barline"""
        try:
            # Draw the barline
            self.render_system_barline(
                painter, 
                x + measure.end_x, 
                y, 
                y + staff_height,
                measure.barline_type,
                measure.selected
            )
            
            # Draw measure number if it's the first measure of a system
            if measure.measure_number % self.measures_per_system == 1:
                self.render_measure_number(painter, x, y, measure.measure_number)
            
            # Draw repeat dots if needed
            if measure.is_repeat_start or measure.is_repeat_end:
                self.render_repeat_dots(painter, x + measure.end_x, y, staff_height, measure)
            
            # Draw ending brackets if needed
            if measure.ending_type:
                self.render_ending_bracket(painter, x + measure.end_x, y, staff_height, measure)
            
            # Draw musical direction if needed
            if measure.musical_direction:
                self.render_musical_direction(painter, x + measure.end_x, y, staff_height, measure)
            
        except Exception as e:
            print(f"RENDER_ERROR: Exception in render_measure: {e}")
            import traceback
            traceback.print_exc()

    def render_repeat_dots(self, painter, x, y, staff_height, measure):
        """Render repeat dots for a measure"""
        try:
            # Set up the painter for dots
            painter.save()
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.setBrush(QBrush(Qt.GlobalColor.black))
            
            # Calculate dot positions
            dot_radius = 2.0
            
            # Draw dots for each staff in the system
            current_y = y
            while current_y < y + staff_height:
                # Draw dots positioned exactly between staff lines
                # Top dot: exactly in the middle of the space between 2nd and 3rd staff lines
                dot_y1 = current_y + STAFF_LINE_SPACING + (STAFF_LINE_SPACING // 2)
                # Bottom dot: exactly in the middle of the space between 3rd and 4th staff lines
                dot_y2 = current_y + (2 * STAFF_LINE_SPACING) + (STAFF_LINE_SPACING // 2)
                
                if measure.is_repeat_start:
                    # Draw dots after the barline
                    painter.drawEllipse(QPointF(x + 8, dot_y1), dot_radius, dot_radius)
                    painter.drawEllipse(QPointF(x + 8, dot_y2), dot_radius, dot_radius)
                
                if measure.is_repeat_end:
                    # Draw dots before the barline
                    painter.drawEllipse(QPointF(x - 4, dot_y1), dot_radius, dot_radius)
                    painter.drawEllipse(QPointF(x - 4, dot_y2), dot_radius, dot_radius)
                
                # Move to next staff
                current_y += STAFF_LINE_SPACING * 4 + DEFAULT_STAFF_SPACING
            
            painter.restore()
            
        except Exception as e:
            print(f"RENDER_ERROR: Exception in render_repeat_dots: {e}")
            import traceback
            traceback.print_exc()

    def render_ending_bracket(self, painter, x, y, staff_height, measure):
        """Render ending bracket for a measure"""
        try:
            # Set up the painter for the bracket
            painter.save()
            painter.setPen(QPen(Qt.GlobalColor.black))
            
            # Calculate bracket dimensions
            bracket_width = 8
            bracket_height = staff_height
            
            # Draw the bracket
            if measure.ending_type == "1st":
                # Draw a simple bracket for 1st ending
                painter.drawLine(QPointF(x + bracket_width, y), 
                               QPointF(x + bracket_width, y + bracket_height))
                painter.drawLine(QPointF(x + bracket_width, y), 
                               QPointF(x, y))
                painter.drawLine(QPointF(x + bracket_width, y + bracket_height), 
                               QPointF(x, y + bracket_height))
                
                # Draw the number
                painter.drawText(QRectF(x - 20, y, 20, 20), 
                               Qt.AlignmentFlag.AlignCenter, "1.")
            
            elif measure.ending_type == "2nd":
                # Draw a bracket for 2nd ending
                painter.drawLine(QPointF(x + bracket_width, y), 
                               QPointF(x + bracket_width, y + bracket_height))
                painter.drawLine(QPointF(x + bracket_width, y), 
                               QPointF(x, y))
                painter.drawLine(QPointF(x + bracket_width, y + bracket_height), 
                               QPointF(x, y + bracket_height))
                
                # Draw the number
                painter.drawText(QRectF(x - 20, y, 20, 20), 
                               Qt.AlignmentFlag.AlignCenter, "2.")
            
            elif measure.ending_type == "1st-2nd":
                # Draw a bracket spanning both endings
                painter.drawLine(QPointF(x + bracket_width, y), 
                               QPointF(x + bracket_width, y + bracket_height))
                painter.drawLine(QPointF(x + bracket_width, y), 
                               QPointF(x, y))
                painter.drawLine(QPointF(x + bracket_width, y + bracket_height), 
                               QPointF(x, y + bracket_height))
                
                # Draw the numbers
                painter.drawText(QRectF(x - 20, y, 20, 20), 
                               Qt.AlignmentFlag.AlignCenter, "1.")
                painter.drawText(QRectF(x - 20, y + bracket_height/2, 20, 20), 
                               Qt.AlignmentFlag.AlignCenter, "2.")
            
            painter.restore()
            
        except Exception as e:
            print(f"RENDER_ERROR: Exception in render_ending_bracket: {e}")
            import traceback
            traceback.print_exc()

    def render_musical_direction(self, painter, x, y, staff_height, measure):
        """Render musical direction for a measure"""
        try:
            # Set up the painter for the direction
            painter.save()
            painter.setPen(QPen(Qt.GlobalColor.black))
            
            # Get the direction symbol
            direction_symbol = measure.get_direction_symbol()
            if direction_symbol:
                # Draw the symbol
                painter.setFont(QFont(MUSIC_FONTS["primary"], FONT_SIZES["direction"]))
                painter.drawText(QRectF(x + 10, y - 20, 30, 20), 
                               Qt.AlignmentFlag.AlignCenter, direction_symbol)
            
            # Draw the direction text if any
            if measure.direction_text:
                painter.setFont(QFont("Arial", 10))
                painter.drawText(QRectF(x + 40, y - 20, 100, 20), 
                               Qt.AlignmentFlag.AlignLeft, measure.direction_text)
            
            painter.restore()
            
        except Exception as e:
            print(f"RENDER_ERROR: Exception in render_musical_direction: {e}")
            import traceback
            traceback.print_exc()
