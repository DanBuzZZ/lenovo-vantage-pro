"""
Lenovo Vantage Pro - Enterprise Luxury Stylesheet
Theme: Obsidian Titanium & Cyber Precision
Palette:
- Window Background: #080c14 / #0c1322
- Sidebar & Header: #0a0f1d (border #1a2638)
- Card Surface: #0f172a (radius 14px, border 1px solid #1e293b)
- Accents: #38bdf8 (Cyber Blue), #10b981 (Titanium Emerald), #ef4444 (Thermal Red)
- Typography: High Contrast WCAG AAA Compliant
"""

PRO_MAX_THEME = """
/* Global Window & Typography */
QMainWindow, QWidget {
    background-color: #080c14;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", Roboto, sans-serif;
    font-size: 13px;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
}

/* Sidebar Navigation */
#sidebar {
    background-color: #0a0f1d;
    border-right: 1px solid #1a2638;
    min-width: 230px;
    max-width: 230px;
}

#brandTitle {
    color: #38bdf8;
    font-size: 18px;
    font-weight: 900;
    letter-spacing: 2.2px;
}

#brandSubtitle {
    color: #64748b;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
}

#navBtn {
    background-color: transparent;
    color: #94a3b8;
    text-align: left;
    padding: 12px 18px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    border: none;
    margin: 3px 10px;
}

#navBtn:hover {
    background-color: #121c2e;
    color: #f8fafc;
}

#navBtn:checked {
    background-color: #16243d;
    color: #38bdf8;
    font-weight: 700;
    border-left: 3px solid #38bdf8;
}

/* Header Bar */
#header {
    background-color: #0a0f1d;
    border-bottom: 1px solid #1a2638;
    padding: 14px 28px;
}

#headerTitle {
    color: #f8fafc;
    font-size: 17px;
    font-weight: 800;
    letter-spacing: 0.5px;
}

#headerMeta {
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
}

/* Hero Machine Identity Banner */
#heroBanner {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0c1322, stop:1 #0f172a);
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 20px 24px;
}

#heroTitle {
    color: #ffffff;
    font-size: 21px;
    font-weight: 800;
    letter-spacing: 0.3px;
}

#heroSubtitle {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 500;
}

/* Status Pill */
.StatusPill {
    background-color: #121a29;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 700;
    color: #cbd5e1;
    letter-spacing: 0.3px;
}

/* Card Surface */
.ProCard {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 18px 20px;
}

.ProCard:hover {
    border-color: #334155;
}

.CardHeader {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Metric / Telemetry Stat Box */
.StatBox {
    background-color: #0b111e;
    border: 1px solid #1a2333;
    border-radius: 10px;
    padding: 12px 14px;
}

.StatLabel {
    color: #64748b;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

.StatValue {
    color: #f8fafc;
    font-size: 15px;
    font-weight: 800;
}

.StatSub {
    color: #38bdf8;
    font-size: 11px;
    font-weight: 600;
}

/* Buttons */
QPushButton.PresetBtn {
    background-color: #162032;
    color: #94a3b8;
    border: 1px solid #233148;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton.PresetBtn:hover {
    background-color: #1e293b;
    color: #f8fafc;
    border-color: #38bdf8;
}

QPushButton.PresetBtn:checked {
    background-color: #0284c7;
    color: #ffffff;
    border-color: #38bdf8;
}

/* Progress bar */
QProgressBar {
    background-color: #162032;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #38bdf8;
    border-radius: 4px;
}

/* Scroll area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #080c14;
    width: 6px;
    border-radius: 3px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #1e293b;
    min-height: 30px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #38bdf8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Context Menus & Tooltips */
QMenu {
    background-color: #0a0f1d;
    color: #f8fafc;
    border: 1px solid #1a2638;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 7px 22px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
}

QMenu::item:selected {
    background-color: #16243d;
    color: #38bdf8;
}

QMenu::separator {
    height: 1px;
    background-color: #1a2638;
    margin: 4px 8px;
}

QToolTip {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 11px;
}

/* Maintenance Purge Cockpit */
QFrame#maintenancePurgeCockpit, .MaintenancePurgeCockpit {
    background-color: #0b111e;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 18px 20px;
}

QFrame#maintenancePurgeCockpit:hover, .MaintenancePurgeCockpit:hover {
    border-color: #2a3b53;
}

/* Purge Square Wave & Countdown Bar */
QProgressBar#purgeCountdownBar {
    background-color: #162032;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}

QProgressBar#purgeCountdownBar::chunk {
    background-color: #38bdf8;
    border-radius: 4px;
}

/* Purge Action Button */
QPushButton#purgeActionBtn {
    background-color: #0284c7;
    color: #ffffff;
    border: 1px solid #38bdf8;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.5px;
}

QPushButton#purgeActionBtn:hover {
    background-color: #0369a1;
    border-color: #7dd3fc;
}

QPushButton#purgeActionBtn:pressed {
    background-color: #0c4a6e;
}

/* Esports Display Suite */
QFrame#esportsDisplaySuiteCard, .EsportsDisplaySuiteCard {
    background-color: #0b111e;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 18px 20px;
}

QFrame#esportsDisplaySuiteCard:hover, .EsportsDisplaySuiteCard:hover {
    border-color: #2a3b53;
}

/* Segmented Buttons */
.SegmentContainer {
    background-color: #080d16;
    border: 1px solid #1a2333;
    border-radius: 8px;
    padding: 4px;
}

QPushButton.SegmentBtn {
    background-color: transparent;
    color: #94a3b8;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 700;
}

QPushButton.SegmentBtn:hover {
    background-color: #121c2e;
    color: #f8fafc;
}

QPushButton.SegmentBtn[active="true"] {
    background-color: #0284c7;
    color: #ffffff;
    border: 1px solid #38bdf8;
}

QPushButton.SegmentBtn[variant="power"][active="true"] {
    background-color: #065f46;
    color: #ecfdf5;
    border: 1px solid #10b981;
}

QPushButton.SegmentBtn[variant="extreme"][active="true"] {
    background-color: #991b1b;
    color: #fef2f2;
    border: 1px solid #f43f5e;
}

QPushButton.SegmentBtn[variant="muted"][active="true"] {
    background-color: #334155;
    color: #f8fafc;
    border: 1px solid #64748b;
}

/* Intel Alder Lake Core Scheduler & Optimizer */
QFrame#gamingCoreSchedulerCard, .GamingCoreSchedulerCard {
    background-color: #0b111e;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 18px 20px;
}

QFrame#gamingCoreSchedulerCard:hover, .GamingCoreSchedulerCard:hover {
    border-color: #2a3b53;
}

/* Floating Luxury On-Screen Display HUD */
QFrame#floatingLuxuryOsd, .FloatingLuxuryOSD {
    background-color: #090d16;
    border-radius: 16px;
    border: 1.5px solid #38bdf8;
}
"""


