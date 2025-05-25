from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, 
    QScrollArea, QPushButton, QApplication
)
from PySide6.QtCore import Qt, QMimeData, Signal
from PySide6.QtGui import QDrag, QPainter, QPixmap

class DraggableStudentCard(QFrame):
    """A draggable card representing a student."""
    
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
    """A drop zone for a group of students."""
    
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
