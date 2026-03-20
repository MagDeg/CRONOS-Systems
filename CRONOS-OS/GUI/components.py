# ----------------------------
# Komponenten
# ----------------------------
from dash import html

from GUI.Wigets.speed_gauge import combinedSpeedGauge


def Header():
    return html.Div("C.R.O.N.O.S. | OS", className="header")

def Footer():
    return html.Div("Bottom Line", className="footer")

def SidebarPanel(text):
    return html.Div(text, className="sidebarPanel")

def LeftSidebar():
    return html.Div([
        SidebarPanel("Settings"),
        SidebarPanel("Light Control")
    ], className="sidebar")

def RightSidebar():
    return html.Div([
        SidebarPanel("State"),
        SidebarPanel("Buttons")
    ], className="sidebar")

def Panel(text):
    return html.Div(text, className="panel")

def MainContent():
    return html.Div([
        html.Div([
            Panel(combinedSpeedGauge(120, 80 , 50)),
            Panel("Panel 4"),
            Panel("Panel 3")
        ], className="panel-row"),
        html.Div([
            Panel("Panel 4"),
            Panel("Panel 5"),
            Panel("Panel 6")
        ], className="panel-row")
    ], className="main")
