#!/usr/bin/env python3
"""
Section Bracket Test

A simple, focused application to test section bracket rendering without relying on SMuFL fonts.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QVBoxLayout,
    QWidget, QPushButton, QHBoxLayout, QLabel, QGraphicsItem
)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
import math

# Define constants for the test
STAFF_LINE_SPACING = 8
STAFF_LINE_COUNT = 5
STAFF_HEIGHT = STAFF_LINE_SPACING * (STAFF_LINE_COUNT - 1)
STAFF_LINE_THICKNESS = 1.0

class Staff:
    """Simple staff class for testing."""
    def __init__(self, name, y_position=0, section_id=None):
        self.name = name
        self.y_position = y_position
        self.section_id = section_id

class Section:
    """Simple section class for testing."""
    def __init__(self, name, staves=None):
        self.name = name
        self.staves = staves or []

class ScoreRendererItem(QGraphicsItem):
    """A simple renderer that focuses on section bracket rendering."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sections = []
        self._page_width = 800
        self._page_height = 600
        self._left_margin = 50
        self._right_margin = 50
        self._render_methods = [
            "Direct Drawing",
            "Curved Corners",
            "Bold Lines",
            "SMuFL Glyphs"
        ]
        self._current_method = 0
    
    def boundingRect(self):
        return QRectF(0, 0, self._page_width, self._page_height)
    
    def set_sections(self, sections):
        self._sections = sections
        self.update()
    
    def cycle_render_method(self):
        self._current_method = (self._current_method + 1) % len(self._render_methods)
        print(f"Switched to bracket rendering method: {self._render_methods[self._current_method]}")
        self.update()
        return self._render_methods[self._current_method]
    
    def paint(self, painter, option, widget):
        # Set up painter
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw white background
        painter.fillRect(self.boundingRect(), Qt.GlobalColor.white)
        
        # Draw heading with current rendering method
        painter.save()
        font = QFont()
        font.setPointSize(14)
        painter.setFont(font)
        painter.drawText(
            QPointF(self._left_margin, 30), 
            f"Section Bracket Test - Method: {self._render_methods[self._current_method]}"
        )
        painter.restore()
        
        # Draw all staves
        for section in self._sections:
            for staff in section.staves:
                self._draw_staff(painter, staff)
            
            # Draw section bracket if section has multiple staves
            if len(section.staves) > 1:
                top_y = section.staves[0].y_position
                bottom_y = section.staves[-1].y_position + STAFF_HEIGHT
                
                # Choose rendering method based on current selection
                if self._current_method == 0:
                    self._draw_simple_bracket(painter, top_y, bottom_y)
                elif self._current_method == 1:
                    self._draw_curved_bracket(painter, top_y, bottom_y)
                elif self._current_method == 2:
                    self._draw_bold_bracket(painter, top_y, bottom_y)
                else:
                    self._draw_smufl_bracket(painter, top_y, bottom_y)
                
                # Draw section name
                painter.save()
                font = QFont()
                font.setPointSize(12)
                font.setBold(True)
                painter.setFont(font)
                mid_y = (top_y + bottom_y) / 2
                painter.drawText(
                    QPointF(self._left_margin - 40, mid_y + 5), 
                    section.name
                )
                painter.restore()
        
        # Draw information text
        painter.save()
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        line_y = self._page_height - 100
        for method in self._render_methods:
            is_current = method == self._render_methods[self._current_method]
            if is_current:
                painter.setPen(Qt.GlobalColor.blue)
                font.setBold(True)
            else:
                painter.setPen(Qt.GlobalColor.black)
                font.setBold(False)
            painter.setFont(font)
            painter.drawText(
                QPointF(self._page_width - 200, line_y), 
                f"• {method}"
            )
            line_y += 20
        
        painter.setPen(Qt.GlobalColor.black)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(
            QPointF(self._page_width - 200, line_y + 20), 
            "Click 'Change Method' to cycle"
        )
        painter.restore()
    
    def _draw_staff(self, painter, staff):
        """Draw a single staff with name."""
        # Draw staff lines
        pen = QPen(Qt.GlobalColor.black, STAFF_LINE_THICKNESS)
        painter.setPen(pen)
        
        for i in range(STAFF_LINE_COUNT):
            y = staff.y_position + i * STAFF_LINE_SPACING
            painter.drawLine(
                self._left_margin, y, 
                self._page_width - self._right_margin, y
            )
        
        # Draw staff name
        painter.save()
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(
            QPointF(self._left_margin + 10, staff.y_position - 5), 
            staff.name
        )
        painter.restore()
    
    def _draw_simple_bracket(self, painter, top_y, bottom_y):
        """Draw a simple bracket using straight lines."""
        painter.save()
        
        # Use a medium pen for the bracket
        pen = QPen(Qt.GlobalColor.black, 1.5)
        painter.setPen(pen)
        
        # Define bracket dimensions
        bracket_x = self._left_margin - 15
        bracket_width = 10
        
        # Draw the vertical line
        painter.drawLine(bracket_x, top_y, bracket_x, bottom_y)
        
        # Draw the top horizontal part - extending to the right
        painter.drawLine(bracket_x, top_y, bracket_x + bracket_width, top_y)
        
        # Draw the bottom horizontal part - extending to the right
        painter.drawLine(bracket_x, bottom_y, bracket_x + bracket_width, bottom_y)
        
        print(f"Drawing simple bracket from y={top_y} to y={bottom_y}")
        painter.restore()
    
    def _draw_curved_bracket(self, painter, top_y, bottom_y):
        """Draw a bracket with curved corners."""
        painter.save()
        
        # Use a medium pen for the bracket
        pen = QPen(Qt.GlobalColor.black, 1.5)
        painter.setPen(pen)
        
        # Define bracket dimensions
        bracket_x = self._left_margin - 15
        bracket_width = 10
        curve_radius = 4
        
        # Draw the vertical line (slightly offset for curves)
        vertical_x = bracket_x
        painter.drawLine(vertical_x, top_y + curve_radius, vertical_x, bottom_y - curve_radius)
        
        # Draw the top horizontal part - extending to the right
        painter.drawLine(vertical_x + curve_radius, top_y, vertical_x + bracket_width - curve_radius, top_y)
        
        # Draw the bottom horizontal part - extending to the right
        painter.drawLine(vertical_x + curve_radius, bottom_y, vertical_x + bracket_width - curve_radius, bottom_y)
        
        # Draw the curved corners
        # Top-left curved corner
        painter.drawArc(vertical_x, top_y, 2*curve_radius, 2*curve_radius, 180*16, 90*16)
        
        # Top-right curved corner
        painter.drawArc(vertical_x + bracket_width - 2*curve_radius, top_y, 2*curve_radius, 2*curve_radius, 270*16, 90*16)
        
        # Bottom-left curved corner
        painter.drawArc(vertical_x, bottom_y - 2*curve_radius, 2*curve_radius, 2*curve_radius, 90*16, 90*16)
        
        # Bottom-right curved corner
        painter.drawArc(vertical_x + bracket_width - 2*curve_radius, bottom_y - 2*curve_radius, 2*curve_radius, 2*curve_radius, 0, 90*16)
        
        print(f"Drawing curved bracket from y={top_y} to y={bottom_y}")
        painter.restore()
    
    def _draw_bold_bracket(self, painter, top_y, bottom_y):
        """Draw a bolder bracket with thicker lines."""
        painter.save()
        
        # Use a thick pen for the bracket
        pen = QPen(Qt.GlobalColor.black, 2.5)
        painter.setPen(pen)
        
        # Define bracket dimensions
        bracket_x = self._left_margin - 15
        bracket_width = 12
        
        # Draw the vertical line
        painter.drawLine(bracket_x, top_y, bracket_x, bottom_y)
        
        # Draw the top horizontal part - extending to the right
        painter.drawLine(bracket_x, top_y, bracket_x + bracket_width, top_y)
        
        # Draw the bottom horizontal part - extending to the right
        painter.drawLine(bracket_x, bottom_y, bracket_x + bracket_width, bottom_y)
        
        print(f"Drawing bold bracket from y={top_y} to y={bottom_y}")
        painter.restore()
    
    def _draw_smufl_bracket(self, painter, top_y, bottom_y):
        """Draw brackets using SMuFL glyphs."""
        painter.save()
        
        # Define bracket position
        bracket_x = self._left_margin - 15
        
        # Set font for the bracket
        bracket_font_size = 24.0
        bracket_font = QFont("Bravura")
        bracket_font.setPointSizeF(bracket_font_size)
        painter.setFont(bracket_font)
        
        # Get font metrics for measurements
        metrics = painter.fontMetrics()
        
        # Define the correct SMuFL glyphs
        bracket_top = '\uE002'      # bracketTop
        bracket_middle = '\uE034'   # bracketMiddle
        bracket_bottom = '\uE003'   # bracketBottom
        
        # Get the height of each component
        segment_height = metrics.height()
        
        # Calculate how many middle segments needed
        bracket_height = bottom_y - top_y
        
        # Add slight overlap between segments
        overlap = 4  # Pixels of overlap
        
        # Calculate usable height
        usable_height = bracket_height - (segment_height - overlap) * 2
        
        # Calculate number of middle segments
        num_middle_segments = max(1, math.ceil(usable_height / (segment_height - overlap)))
        
        # Draw top bracket segment
        painter.drawText(QPointF(bracket_x, top_y + segment_height), bracket_top)
        
        # Draw middle segments
        current_y = top_y + segment_height - overlap
        for i in range(num_middle_segments):
            painter.drawText(QPointF(bracket_x, current_y + segment_height), bracket_middle)
            current_y += segment_height - overlap
        
        # Draw bottom bracket segment
        painter.drawText(QPointF(bracket_x, bottom_y), bracket_bottom)
        
        print(f"Drawing SMuFL bracket from y={top_y} to y={bottom_y} with {num_middle_segments} middle segments")
        painter.restore()


class ScoreView(QGraphicsView):
    """A view to display the score."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.renderer = ScoreRendererItem()
        self.scene.addItem(self.renderer)
        
        # Initialize with test sections
        self.setup_test_sections()
    
    def setup_test_sections(self):
        """Create test sections for demonstration."""
        # Create sections with varying numbers of staves
        sections = []
        
        # Section 1: Two staves
        staves = [
            Staff("Section 1 - Staff 1", y_position=80, section_id="section1"),
            Staff("Section 1 - Staff 2", y_position=140, section_id="section1")
        ]
        sections.append(Section("Winds", staves))
        
        # Section 2: Three staves
        staves = [
            Staff("Section 2 - Staff 1", y_position=220, section_id="section2"),
            Staff("Section 2 - Staff 2", y_position=280, section_id="section2"),
            Staff("Section 2 - Staff 3", y_position=340, section_id="section2")
        ]
        sections.append(Section("Strings", staves))
        
        # Section 3: Four staves
        staves = [
            Staff("Section 3 - Staff 1", y_position=420, section_id="section3"),
            Staff("Section 3 - Staff 2", y_position=480, section_id="section3"),
            Staff("Section 3 - Staff 3", y_position=540, section_id="section3"),
            Staff("Section 3 - Staff 4", y_position=600, section_id="section3")
        ]
        sections.append(Section("Percussion", staves))
        
        # Set the sections in the renderer
        self.renderer.set_sections(sections)
    
    def cycle_render_method(self):
        """Cycle through different bracket rendering methods."""
        return self.renderer.cycle_render_method()
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        self.fitInView(self.renderer.boundingRect(), Qt.AspectRatioMode.KeepAspectRatio)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Section Bracket Test")
        self.setGeometry(100, 100, 800, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        main_layout.addLayout(controls_layout)
        
        # Change Method button
        self.method_button = QPushButton("Change Method")
        self.method_button.clicked.connect(self.change_method)
        controls_layout.addWidget(self.method_button)
        
        # Current method label
        self.method_label = QLabel("Method: Direct Drawing")
        controls_layout.addWidget(self.method_label)
        
        controls_layout.addStretch(1)
        
        # Score view
        self.score_view = ScoreView()
        main_layout.addWidget(self.score_view)
    
    def change_method(self):
        """Change the bracket rendering method."""
        method = self.score_view.cycle_render_method()
        self.method_label.setText(f"Method: {method}")


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 