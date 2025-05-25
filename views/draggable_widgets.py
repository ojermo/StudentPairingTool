from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, 
    QScrollArea, QPushButton, QApplication, QTableWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QMimeData, Signal, QPoint
from PySide6.QtGui import QDrag, QPainter, QPixmap, QCursor

class StudentChip(QFrame):
    """A compact draggable chip representing a student."""
    
    def __init__(self, student_data, parent=None):
        super().__init__(parent)
        self.student_data = student_data
        
        # Let the chip size itself to content
        self.setMinimumHeight(25)
        self.setMaximumHeight(25)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.setStyleSheet("""
            StudentChip {
                background-color: #da532c;
                color: white;
                border-radius: 12px;
                border: none;
                font-size: 12px;
                font-weight: bold;
                padding: 2px 8px;
            }
            StudentChip:hover {
                background-color: #bc4626;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setSpacing(0)
        
        # Show name and track abbreviation
        name = student_data.get("name", "Unknown")
        track = student_data.get("track", "")
        
        # Extract track abbreviation (take first 3 letters before parentheses)
        track_abbr = ""
        if "(" in track:
            track_abbr = track.split("(")[0].strip()[:3]
        else:
            track_abbr = track[:3]
        
        display_text = f"{name} ({track_abbr})" if track_abbr else name
        
        name_label = QLabel(display_text)
        name_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        name_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(name_label)
        
        # Add drag threshold
        self.drag_threshold = 10
        self.drag_start_position = None
    
    def enterEvent(self, event):
        """Change cursor on hover."""
        self.setCursor(QCursor(Qt.OpenHandCursor))
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Reset cursor when leaving."""
        self.setCursor(QCursor(Qt.ArrowCursor))
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            self.setCursor(QCursor(Qt.ClosedHandCursor))
    
    def mouseReleaseEvent(self, event):
        """Reset cursor on release."""
        self.setCursor(QCursor(Qt.OpenHandCursor))
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if not self.drag_start_position:
            return
            
        # Check if we've moved beyond the threshold
        if ((event.pos() - self.drag_start_position).manhattanLength() < self.drag_threshold):
            return
        
        # Start drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.student_data["id"])  # Store student ID
        drag.setMimeData(mime_data)
        
        # Create drag pixmap - render directly to pixmap (simpler approach)
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        
        # Render widget directly to pixmap (QPaintDevice)
        self.render(pixmap)
        
        drag.setPixmap(pixmap)
        
        # Set cursor during drag
        self.setCursor(QCursor(Qt.ClosedHandCursor))
        
        # Execute drag
        result = drag.exec(Qt.MoveAction)
        
        # Reset cursor after drag
        self.setCursor(QCursor(Qt.OpenHandCursor))

class DroppableTableRow(QWidget):
    """A container for student chips that can accept drops."""
    
    studentMoved = Signal(str, int)  # Signal: student_id, new_row_index
    
    def __init__(self, row_index, parent=None):
        super().__init__(parent)
        self.row_index = row_index
        self.setAcceptDrops(True)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 2, 5, 2)
        self.layout.setSpacing(5)
        
        # List to track chips in this row
        self.student_chips = []
    
    def add_student_chip(self, student_data):
        """Add a student chip to this row."""
        chip = StudentChip(student_data, self)
        self.student_chips.append(chip)
        self.layout.addWidget(chip)
        return chip
    
    def remove_student_chip(self, student_id):
        """Remove a student chip from this row."""
        for i, chip in enumerate(self.student_chips):
            if chip.student_data["id"] == student_id:
                chip.deleteLater()
                self.student_chips.pop(i)
                break
    
    def get_student_ids(self):
        """Get list of student IDs in this row."""
        return [chip.student_data["id"] for chip in self.student_chips]
    
    def clear_chips(self):
        """Remove all chips from this row."""
        for chip in self.student_chips:
            chip.deleteLater()
        self.student_chips.clear()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            # Add visual feedback
            self.setStyleSheet("background-color: rgba(218, 83, 44, 0.1); border-radius: 3px;")
    
    def dragLeaveEvent(self, event):
        # Remove visual feedback
        self.setStyleSheet("")
    
    def dropEvent(self, event):
        student_id = event.mimeData().text()
        
        # Find the source chip and remove it from its current location
        source_chip = None
        old_parent = None
        
        # Look through all widgets to find the source chip
        for widget in QApplication.allWidgets():
            if (isinstance(widget, StudentChip) and 
                widget.student_data["id"] == student_id):
                source_chip = widget
                
                # Find the parent DroppableTableRow
                parent = widget.parent()
                while parent and not isinstance(parent, DroppableTableRow):
                    parent = parent.parent()
                old_parent = parent
                break
        
        if source_chip and old_parent != self:
            # Remove from old parent
            if old_parent:
                old_parent.remove_student_chip(student_id)
            
            # Add to this row
            self.add_student_chip(source_chip.student_data)
            
            # Emit signal that student moved
            self.studentMoved.emit(student_id, self.row_index)
        
        # Remove visual feedback
        self.setStyleSheet("")
        event.acceptProposedAction()

# Keep the old classes for backward compatibility, but they won't be used in the new implementation
class DraggableStudentCard(QFrame):
    """Legacy draggable card - kept for compatibility."""
    
    def __init__(self, student_data, parent=None):
        super().__init__(parent)
        self.student_data = student_data
        self.setFixedSize(150, 60)
        self.setStyleSheet("""
            DraggableStudentCard {
                background-color: white;
                border: 2px solid #da532c;
                border-radius: 5px;
                padding: 5px;
            }
            DraggableStudentCard:hover {
                background-color: #f0f0f0;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        name_label = QLabel(student_data.get("name", "Unknown"))
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        name_label.setAlignment(Qt.AlignCenter)
        
        track_label = QLabel(student_data.get("track", ""))
        track_label.setStyleSheet("font-size: 10px; color: #666;")
        track_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(name_label)
        layout.addWidget(track_label)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if not hasattr(self, 'drag_start_position'):
            return
            
        if ((event.pos() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
        
        # Start drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.student_data["id"])  # Store student ID
        drag.setMimeData(mime_data)
        
        # Create drag pixmap
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        
        # Execute drag
        drag.exec(Qt.MoveAction)

class PairGroupWidget(QFrame):
    """Legacy group widget - kept for compatibility."""
    
    pairingChanged = Signal()  # Signal when pairing changes
    
    def __init__(self, group_number, parent=None):
        super().__init__(parent)
        self.group_number = group_number
        self.student_cards = []
        
        self.setAcceptDrops(True)
        self.setMinimumSize(200, 150)
        self.setStyleSheet("""
            PairGroupWidget {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        
        # Group header
        self.header_label = QLabel(f"Group {group_number}")
        self.header_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        self.header_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.header_label)
        
        # Scrollable area for student cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(5)
        
        scroll_area.setWidget(self.cards_container)
        self.main_layout.addWidget(scroll_area)
    
    def add_student_card(self, student_data):
        """Add a student card to this group."""
        card = DraggableStudentCard(student_data, self)
        self.student_cards.append(card)
        self.cards_layout.addWidget(card)
        return card
    
    def remove_student_card(self, student_id):
        """Remove a student card from this group."""
        for i, card in enumerate(self.student_cards):
            if card.student_data["id"] == student_id:
                card.deleteLater()
                self.student_cards.pop(i)
                break
    
    def get_student_ids(self):
        """Get list of student IDs in this group."""
        return [card.student_data["id"] for card in self.student_cards]
    
    def update_header(self, warning_text=""):
        """Update the group header with warning information."""
        base_text = f"Group {self.group_number}"
        if warning_text:
            self.header_label.setText(f"{base_text}\n{warning_text}")
            self.header_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; padding: 5px; color: #cc0000;"
            )
        else:
            self.header_label.setText(base_text)
            self.header_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; padding: 5px; color: #000;"
            )
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("""
                PairGroupWidget {
                    border: 2px dashed #da532c;
                    border-radius: 10px;
                    background-color: #ffeaa7;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            PairGroupWidget {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
        """)
    
    def dropEvent(self, event):
        student_id = event.mimeData().text()
        
        # Find the source card and its current parent
        source_card = None
        old_parent = None
        
        for widget in QApplication.allWidgets():
            if (isinstance(widget, DraggableStudentCard) and 
                widget.student_data["id"] == student_id):
                source_card = widget
                # Walk up the parent hierarchy to find the PairGroupWidget
                parent = widget.parent()
                while parent and not isinstance(parent, PairGroupWidget):
                    parent = parent.parent()
                old_parent = parent
                break
        
        if source_card:
            # Remove from old parent
            if old_parent and old_parent != self:
                old_parent.remove_student_card(student_id)
            
            # Add to this group (only if not already here)
            if old_parent != self:
                new_card = self.add_student_card(source_card.student_data)
                
                # Emit signal that pairing changed
                self.pairingChanged.emit()
        
        # Reset style
        self.setStyleSheet("""
            PairGroupWidget {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
        """)
        event.acceptProposedAction()
