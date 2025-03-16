# utils/ui_helpers.py

from PySide6.QtWidgets import QHBoxLayout, QPushButton

def setup_navigation_bar(parent, current_tab="dashboard"):
    """
    Create a standardized navigation bar.
    
    Args:
        parent: Parent widget (view) that will contain the navigation bar
        current_tab: Current active tab name
        
    Returns:
        QHBoxLayout containing the navigation buttons
    """
    tabs_layout = QHBoxLayout()
    
    # Dashboard button
    dashboard_btn = QPushButton("Dashboard")
    dashboard_btn.setObjectName("navTab")
    dashboard_btn.clicked.connect(parent.main_window.show_dashboard)
    
    # Students button
    students_btn = QPushButton("Students")
    students_btn.setObjectName("navTab")
    # Use a method reference instead of a lambda
    students_btn.clicked.connect(lambda: parent.go_to_students())
    
    # Pairings button
    pairings_btn = QPushButton("Pairings")
    pairings_btn.setObjectName("navTab")
    # Use a method reference instead of a lambda
    pairings_btn.clicked.connect(lambda: parent.go_to_pairings())
    
    # History button
    history_btn = QPushButton("History")
    history_btn.setObjectName("navTab")
    # Use a method reference instead of a lambda
    history_btn.clicked.connect(lambda: parent.go_to_history())
    
    # Export button
    export_btn = QPushButton("Export")
    export_btn.setObjectName("navTab")
    # Use a method reference instead of a lambda
    export_btn.clicked.connect(lambda: parent.go_to_export())
    
    # Add buttons to layout
    tabs_layout.addWidget(dashboard_btn)
    tabs_layout.addWidget(students_btn)
    tabs_layout.addWidget(pairings_btn)
    tabs_layout.addWidget(history_btn)
    tabs_layout.addWidget(export_btn)
    tabs_layout.addStretch()
    
    # Highlight current tab
    if current_tab == "dashboard":
        dashboard_btn.setStyleSheet("font-weight: bold;")
    elif current_tab == "students":
        students_btn.setStyleSheet("font-weight: bold;")
    elif current_tab == "pairings":
        pairings_btn.setStyleSheet("font-weight: bold;")
    elif current_tab == "history":
        history_btn.setStyleSheet("font-weight: bold;")
    elif current_tab == "export":
        export_btn.setStyleSheet("font-weight: bold;")
    
    return tabs_layout