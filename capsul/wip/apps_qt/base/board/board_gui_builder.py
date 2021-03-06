#! /usr/bin/env python
##########################################################################
# CAPSUL - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import logging
import subprocess
import os

# Qt import
from soma.qt_gui.qt_backend import QtGui, QtCore
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

# Capsul import
from capsul.pipeline import Pipeline
from capsul.pipeline.pipeline_nodes import Switch, PipelineNode
from soma.controller import trait_ids
from capsul.apps_qt.base.window import MyQUiLoader
import capsul.apps_qt.resources as resources


class BoardGUIBuilder(QtGui.QWidget):
    """ Create the result board of a pipeline.
    """

    def __init__(self, pipeline, ui, study_config):
        """ Method to initialize the result board interface.

        Parameters
        ----------
        pipeline: Pipeline (mandatory)
            a pipeline
        ui: enum (mandatory)
            user interface where all Qt controls are stored
        """
        # Inheritance
        super(BoardGUIBuilder, self).__init__()

        # Parameters
        self._pipeline = pipeline
        self._ui = ui
        self._study_config = study_config
        self._tree = ui.tree_controller
        self._controls = {}

        # Create the board
        self.data_to_tree()

    ##############
    # Properties #
    ##############

    #####################
    # Private interface #
    #####################

    def _title_for(self, title):
        """ Method to tune a plug name

        Parameters
        ----------
        title: str (mandatory)
            the name of a plug

        Returns
        -------
        output: str
            the tuned name
        """
        return title.replace("_", " ")

    def data_to_tree(self):
        """ Method to insert processing parameters in the class tree
        """
        # Create item
        root = QtGui.QTreeWidgetItem(self._tree.invisibleRootItem())
        root.setText(0, self._title_for(self._pipeline.name))

        # Insert expanded item
        self._tree.setItemExpanded(root, True)

        # Generate controller controls
        for node_name, node in self._pipeline.nodes.iteritems():

            # Add Processing
            if node_name is not "" and node.node_type != "view_node":

                # First borwse node to get leafs and viewers
                process_nodes = []
                view_nodes = []
                self.browse_node(node, process_nodes, view_nodes,
                                 self._pipeline)

                # Enter a new item in the list
                child = QtGui.QTreeWidgetItem(root)
                child.setText(1, self._title_for(node_name))

                # Set process logs
                for process_node in process_nodes:
                    widget = LogWidget(process_node)
                    widget.setParent(root.treeWidget())
                    child.treeWidget().setItemWidget(child, 3, widget)

                # Set viewers
                for viewer_node, pipeline in view_nodes:
                    widget = ViewerWidget(viewer_node.name, pipeline,
                                          self._study_config)
                    widget.setParent(root.treeWidget())
                    child.treeWidget().setItemWidget(child, 4, widget)

            # Set the pipeline viewer directly on the root item
            elif node.node_type == "view_node":
                widget = ViewerWidget(node_name, self._pipeline,
                                      self._study_config)
                widget.setParent(root.treeWidget())
                root.treeWidget().setItemWidget(root, 4, widget)

    def browse_node(self, node, process_nodes, view_nodes, parent_pipeline):
        """ Find view_node and leaf nodes, ie Process nodes

        Parameters
        ----------
        node: Node
            a capsul node
        process_nodes: Node
            node of type processing_node
        view_nodes: Node
            node of type view_node
        """
        # Skip Switch nodes
        if not isinstance(node, Switch):

            # Browse recursively pipeline nodes
            if (isinstance(node.process, Pipeline) and
               node.node_type != "view_node"):

                pipeline = node.process
                for sub_node in pipeline.nodes.values():
                    if not isinstance(sub_node, PipelineNode):
                        self.browse_node(sub_node, process_nodes, view_nodes,
                                         pipeline)
            # Update the results according to the node type
            else:
                if node.node_type == "view_node":
                    view_nodes.append((node, parent_pipeline))
                else:
                    process_nodes.append(node)


class LogWindow(MyQUiLoader):
    """ Window to show a process log.
    """

    def __init__(self, log_data=None, window_name=None):
        """ Method to initialize the log window.

        Parameters
        ----------
        log_data: dict (mandatory)
            the data contained in the log file
        window_name: str (optional)
            the window name
        """
        # Load UI
        ui_file = os.path.join(resources.__path__[0], "controller_viewer.ui")
        MyQUiLoader.__init__(self, ui_file)

        # Define controls
        self.controls = {QtGui.QTreeWidget: ["tree_controller", ],
                         QtGui.QWidget: ["tree_widget", ]}

        # Find controls
        self.add_controls_to_ui()

        # Init tree
        self.ui.tree_controller.setColumnCount(2)
        self.ui.tree_controller.headerItem().setText(0, "Item")
        self.ui.tree_controller.headerItem().setText(1, "Value")

        # Update window name
        self.ui.tree_widget.parentWidget().setWindowTitle(
            "Log Board Viewer: {0}".format(window_name or ""))

        # Create the board
        for item_name, item in log_data.iteritems():
            self.data_to_tree(item_name, item)

    #####################
    #      Members      #
    #####################

    def show(self):
        """ Shows the widget and its child widgets.
        """
        self.ui.show()

    #####################
    # Private interface #
    #####################

    def _title_for(self, title):
        """ Method to tune a plug name

        Parameters
        ----------
        title: str (mandatory)
            the name of a plug

        Returns
        -------
        output: str
            the tuned name
        """
        return title.replace("_", " ")

    def data_to_tree(self, name, parameters):
        """ Method to insert plug parameters in the class tree

        Parameters
        ----------
        name: str (mandatory)
            the desired new tree enty name
        parameters: object (mandatory)
            object that contain the process return code
        """
        # Create item
        root = QtGui.QTreeWidgetItem(self.ui.tree_controller.invisibleRootItem())
        root.setText(0, self._title_for(name))

        # Insert expanded item
        self.ui.tree_controller.setItemExpanded(root, True)

        # Parse the parameters
        if isinstance(parameters, dict):
            for parameter_name, parameter in parameters.iteritems():
                # Generate sub item
                child = QtGui.QTreeWidgetItem(root)
                child.setText(1, "{0}: {1}".format(parameter_name,
                                                   repr(parameter)))
        else:
            root.setText(1, repr(parameters))

    def add_controls_to_ui(self):
        """ Method that set all desired controls in ui.
        """
        for control_type in self.controls.keys():
            for control_name in self.controls[control_type]:
                try:
                    value = self.ui.findChild(control_type, control_name)
                except:
                    logging.warning(
                        "{0} has no attribute "
                        "'{1}'".format(type(self.ui), control_name))
                setattr(self.ui, control_name, value)


class LogWidget(QtGui.QWidget):
    """ Process log result class
    """

    def __init__(self, process_node):
        """ Method to initialize a LogWidget class.

        Parameters
        ----------
        process_node: ProcessingNode
            a process node
        """
        # Inheritance
        super(LogWidget, self).__init__()

        # Default parameters
        self.process = process_node.process

        # Build control
        self.button = QtGui.QToolButton(self)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icones/view_result")),
                       QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.button.setIcon(icon)
        self.button.setEnabled(os.path.isfile(self.process.log_file or ""))
        self.button.clicked.connect(self.onCreateViewerClicked)

    def onCreateViewerClicked(self):
        """ Event to create the viewer
        """
        self.log_window = LogWindow(self.process.get_log(), self.process.name)
        self.log_window.show()


class ViewerWidget(QtGui.QWidget):
    """ View result class
    """

    def __init__(self, viewer_node_name, pipeline, study_config):
        """ Method to initialize a ViewerWidget class.

        Parameters
        ----------
        viewer_node_name: str
            the name of the node containing the viewer process
        pipeline: str
            the full pipeline in order to get the viewer input trait values
            since the viewer node is unactivated
        """
        # Inheritance
        super(ViewerWidget, self).__init__()

        # Default parameters
        self.viewer_node_name = viewer_node_name
        self.pipeline = pipeline
        self.study_config = study_config

        # Build control
        button = QtGui.QToolButton(self)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icones/view_result")),
                       QtGui.QIcon.Normal, QtGui.QIcon.Off)
        button.setIcon(icon)
        button.clicked.connect(self.onCreateViewerClicked)

    def onCreateViewerClicked(self):
        """ Event to create the viewer
        """
        # Get the viewer node and process
        viewer_node = self.pipeline.nodes[self.viewer_node_name]
        viewer_process = viewer_node.process

        # Propagate the parameters to the input viewer node
        # And check if the viewer is active (ie dependencies
        # are specified -> corresponding process have run)
        is_viewer_active = True
        for plug_name, plug in viewer_node.plugs.iteritems():

            if plug_name in ["nodes_activation", "selection_changed"]:
                continue

            # Since it is a viewer node we normally have only inputs
            for (source_node_name, source_plug_name, source_node,
                 source_plug, weak_link) in plug.links_from:

                # Get the source plug value and source trait
                source_plug_value = getattr(source_node.process,
                                            source_plug_name)
                source_trait = source_node.process.trait(source_plug_name)

                # Check if the viewer is active:
                # 1) the source_plug_value has been set
                if source_plug_value == source_trait.handler.default_value:
                    is_viewer_active = False
                    break
                # 2) if the plug is a file, the file exists
                str_description = trait_ids(source_trait)
                if (len(str_description) == 1 and
                   str_description[0] == "File" and
                   not os.path.isfile(source_plug_value)):

                    is_viewer_active = False
                    break

                # Update destination trait
                setattr(viewer_process, plug_name, source_plug_value)

            # Just stop the iterations if the status of the viewer
            # is alreadu known
            if not is_viewer_active:
                break

        # Execute the viewer process using the defined study configuration
        if is_viewer_active:
            subprocess.Popen(viewer_process.get_commandline())
            # self.study_config.run(viewer_process)
        else:
            logging.error("The viewer is not active yet, maybe "
                          "because the processings steps have not run or are "
                          "not finished.")