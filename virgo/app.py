from tkinter import ttk
import tkinter as tk
from tkinter.filedialog import askopenfilename

import matplotlib
from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)

import numpy as np
import xarray as xr
import os

from virgo import utils, graph
from virgo.nodes import base_nodes, graphical, functional

DEBUG = os.getenv('DEBUG') == "True"


class App:
    def __init__(self, root: tk.Tk):
        """Initializes a new NAME app

        Args:
            root (tkinter.Tk): root tkinter instance
        """
        self.root = root
        self.root.geometry("1200x900")
        # TODO: conn
        # style = ttk.Style()
        # style.configure('TFrame', background="#0c0",borderwidth="2")
        # style.configure('TLabel', background="#0c0",foreground="green")
        self.root.title("Panopoly who?")

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_propagate(False)
        self.page1 = None
        self.page2 = None
        self.curPage = None
        self.selectedNodeVar = None

        self.filePath = ""
        self.data = None
        # self._drag_data = {}

        self.sources = []

        self.create_canvas_page()
        self.create_data_view_page()
        self.set_main_menu()
        self.set_active_page(self.page1)

        if DEBUG:
            self.filePath = "/Users/grhuber/Downloads/2018_High_Vertical.geosgcm_gwd.20180201.nc4"
            self.load_data()

    def set_main_menu(self):
        """Configures highest level menu bar for the app.
        """
        self.menuBar = tk.Menu(self.root)
        self.fileMenu = tk.Menu(self.menuBar, tearoff=0)
        self.fileMenu.add_command(label="New", command=None)
        self.fileMenu.add_command(label="Open", command=self.select_file)
        self.fileMenu.add_command(label="Save", command=None)
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Quit", command=self.root.quit)
        self.menuBar.add_cascade(label="File", menu=self.fileMenu)

        self.windowMenu = tk.Menu(self.menuBar, tearoff=0)
        self.windowMenu.add_command(label="Canvas", command=lambda: self.set_active_page(self.page1))
        self.windowMenu.add_command(label="Data", command=lambda: self.set_active_page(self.page2))
        self.menuBar.add_cascade(label="Window", menu=self.windowMenu)
        self.root.config(menu=self.menuBar)

    def create_canvas_page(self):
        self.page1 = ttk.Frame(self.root)
        self.page1.grid(column=0, row=0,sticky ="nsew")
        
        self.page1.grid_columnconfigure(0, weight=1,uniform="page1")
        self.page1.grid_columnconfigure(1, weight=3,uniform="page1")
        self.page1.grid_rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(self.page1, highlightbackground="black", highlightthickness=1)
        self.canvas.grid(column=1, row=0, sticky="nsew")

        self.canvas.bind('<Motion>', self.canvas_motion_handler)
        self.canvas.bind('<ButtonPress-1>', self.canvas_click_handler)

        self.widgetMenu = ttk.Frame(self.page1, style="TFrame")
        self.widgetMenu.grid(column=0, row=0, sticky="nsew")
        ttk.Label(self.canvas, text="Panopoly The Sequel", padding=10).grid()
        ttk.Label(self.canvas, text="Use the top menu to open a file to get started").grid()
        
        #List of different widgets to add to the canvas
        ttk.Label(self.widgetMenu, text="Data:").grid()
        ttk.Button(self.widgetMenu, text="Add a Data Source", command=lambda x=base_nodes.DataSourceNode: self.add_source_node_to_canvas(x)).grid()

        ttk.Label(self.widgetMenu, text="Graph Type:").grid()
        for nodeType in graphical.__all__:
            ttk.Button(self.widgetMenu, text="add {}:".format(nodeType.description), command=lambda x=nodeType: self.add_node_to_canvas(x)).grid()


        ttk.Label(self.widgetMenu, text="Functions:").grid()
        for nodeType in functional.__all__:
            ttk.Button(self.widgetMenu, text="{}".format(nodeType.description), command=lambda x=nodeType: self.add_node_to_canvas(x)).grid()

        ttk.Button(self.widgetMenu, text="Run Canvas", command=self.run_canvas).grid(pady=20)
        ttk.Button(self.widgetMenu, text="Clear Canvas", command=self.clear_canvas).grid(pady=20)

    def add_node_to_canvas(self, nodeType):
        n = nodeType(self)
        n.render()
        return n
    def add_source_node_to_canvas(self, nodeType):
        n = self.add_node_to_canvas(nodeType)
        self.sources.append(n)
    def run_canvas(self):
        for node in self.sources:
            node.forward()
    def clear_canvas(self):
        self.selectedNodeVar = None
        self.sources = []
        self.canvas.delete('all')
    def update_canvas_page(self):
        pass
    
    def create_data_view_page(self):
        if self.page2:
            utils.destroy_children(self.page2)
        else:
            self.page2 = ttk.Frame(self.root)
            self.page2.grid(column=0, row=0,sticky ="nsew")
            # self.page2.configure(yscrollcommand=ttk.Scrollbar(self.page2).set)
        # TODO: fix window management adn the current variable
        ttk.Label(self.page2, text="Data Properties", padding=10).grid(column=0, row=0)
        ttk.Label(self.page2, text="Metadata").grid()
        if self.data:
            for property in self.data.attrs:
                ttk.Label(self.page2, text=property).grid()
                ttk.Label(self.page2, text=self.data.attrs[property]).grid()
        ttk.Label(self.page2, text="Variables").grid()
        if self.data:
            for variable in self.data.variables.keys():
                ttk.Label(self.page2, text=variable).grid()
                try:
                    ttk.Label(self.page2, text=self.data.variables[variable].attrs.long_name).grid()
                except:
                    pass

    def select_file(self):
        """Selects a file via os specific interface. See also: load data
        """
        self.filePath = askopenfilename()
        if self.filePath:
            self.load_data()

    def load_data(self):
        """Loads in a netcdf file as a nc4 Dataset object. Throws error if failed open. 
        Updates data sources on main canvas page and recreates data view page.
        """
        try:
            self.data = xr.open_dataset(self.filePath, decode_times=False)
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to load NetCDF file: {e}")
            return
        self.update_canvas_page()
        self.create_data_view_page()

    def set_active_page(self, page):
        """Brings page to top level of tkinter rendering. 

        Args:
            page (tkinter.Frame): page to bring 
        """
        page.tkraise()
        self.curPage = page
    def canvas_motion_handler(self, event):
        """Called any time the mouse is moved on the canvas. The
        currently selected nodeVar's line should move with the 
        mouse. If the current node is none, nothing is done.

        Args:
            event (_type_): _description_
        """
        if not self.selectedNodeVar:
            return
        x, y = event.x, event.y
        #TODO: support multiple edges.
        if self.selectedNodeVar not in self.selectedNodeVar.node.draggableWidget.lines:
            lines = self.selectedNodeVar.node.draggableWidget.lines[self.selectedNodeVar] = {}
            #TODO: Add delete handler on double click
            lines["None"] = self.canvas.create_line(0, 0, x, y, width=2)
        else:
            lines = self.selectedNodeVar.node.draggableWidget.lines[self.selectedNodeVar]
            if "None" not in lines:
                lines["None"] = self.canvas.create_line(0, 0, x, y, width=2)
            lineId = lines["None"]
            newCoords = self.canvas.coords(lineId)[:2] + [x, y]
            self.canvas.coords(lineId, *newCoords)
        self.selectedNodeVar.node.draggableWidget.update_output_lines()
    def canvas_click_handler(self, event):
        #TODO: add remove functionality
        if self.selectedNodeVar:
            lines = self.selectedNodeVar.node.draggableWidget.lines
            lineId = lines[self.selectedNodeVar]["None"]
            self.canvas.delete(lineId)
            del lines[self.selectedNodeVar]["None"]
            self.selectedNodeVar = None
    def node_select_handler(self, nodeVar: graph.NodeVar):
        """Called when a nodeVar is selected for creating an edge. If 
        self.selectedNodeVar is not None, then an edge must be created between 
        selected node and the new nodeVar

        Args:
            nodeVar (NodeVar): the new input or output being selected
        """
        if not self.selectedNodeVar and isinstance(nodeVar, graph.Output):
            self.selectedNodeVar = nodeVar
        elif self.selectedNodeVar:
            if isinstance(nodeVar, graph.Input):
            # Handle new connection
                self.selectedNodeVar.edges.append(nodeVar)
                nodeVar.edges.append(self.selectedNodeVar)
                self.selectedNodeVar.node.draggableWidget.lines[self.selectedNodeVar][nodeVar] = self.selectedNodeVar.node.draggableWidget.lines[self.selectedNodeVar]["None"]
                print(self.selectedNodeVar.node.draggableWidget.lines[self.selectedNodeVar][nodeVar])
                del self.selectedNodeVar.node.draggableWidget.lines[self.selectedNodeVar]["None"]
                nodeVar.node.draggableWidget.update_input_lines()
                self.selectedNodeVar = None
