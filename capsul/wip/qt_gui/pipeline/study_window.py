# -*- coding: utf-8 -*-
if __name__ == '__main__':
    from soma.qt_gui.qt_backend import set_qt_backend
    set_qt_backend('PyQt4')
from soma.qt_gui.qt_backend import QtGui, QtCore, getOpenFileName
from soma.gui.widget_controller_creation import ControllerWidget
from capsul.qt_gui.pipeline.process_database_widget \
    import ProcessDatabaseWidget
from soma.application import Application 
from capsul.study_config.study_config import StudyConfig
from capsul.study_config.study_config_fom import StudyConfigFomManager
from capsul.qt_gui.pipeline.process_with_fom_widget import ProcessWithFomWidget
from capsul.qt_gui.pipeline.process_iteration_gui \
    import ProcessIterationGui, ProcessParametersTable
from capsul.process import get_process_instance
from capsul.process.process_with_fom import ProcessWithFom
import os
try:
    from traits.api import Str
except:
    from enthought.traits.api import Str


class StudyWindow(QtGui.QMainWindow):
    """Class to create study and to launch Simple or iteration process"""
    def __init__(self):
        super(StudyWindow, self).__init__()
        self.main_widget = QtGui.QWidget()
        self.vbox = QtGui.QVBoxLayout()

        ##Study
        self.btn_get_study=QtGui.QPushButton('Get .json from study')
        self.vbox.addWidget(self.btn_get_study)

        self.vbox.addWidget(QtGui.QLabel('Study Information'))
        # Find foms available
        foms = Application().fom_manager.find_foms()
        #self.grid=QtGui.QGridLayout()

        #Scroll area to show completion
        self.scroll_area = QtGui.QScrollArea(parent=self)
        self.scroll_area.setWidgetResizable(True)
        self.vbox.addWidget(self.scroll_area)

        #Create controller widget for process and object_attribute
        self.study_config = StudyConfig()
        self.study_config.add_trait('process', Str())
        self.controller_widget22 = ControllerWidget(self.study_config,
            live=True, parent=self.scroll_area)
        self.scroll_area.setWidget(self.controller_widget22)


        #Launch Simple process
        self.btn_show_process = QtGui.QPushButton('View process')
        #Launch Pipeline Process
        self.btn_run_pipeline_process = QtGui.QPushButton('View pipeline')
        #Launch Iteration process
        self.btn_iterate_process = QtGui.QPushButton('Iteration')
        #Launch display DB
        self.btn_display_database=QtGui.QPushButton(
            'Database view (for outputs)')

        self.vbox.addWidget(self.btn_show_process)
        self.vbox.addWidget(self.btn_run_pipeline_process)
        self.vbox.addWidget(self.btn_iterate_process)
        self.vbox.addWidget(self.btn_display_database)
        #self.vbox.addStretch(1)
        self.signals()
        self.main_widget.setLayout(self.vbox)
        self.setCentralWidget(self.main_widget)


    def signals(self):
        """Create widgets signals """
        self.btn_get_study.clicked.connect(self.on_get_study)
        self.btn_show_process.clicked.connect(self.show_process)
        self.btn_run_pipeline_process.clicked.connect(
            self.run_pipeline_process)
        self.btn_iterate_process.clicked.connect(
            self.iterate_process)
        self.btn_display_database.clicked.connect(self.on_display_database)


    def on_get_study(self):
        name_json = getOpenFileName(self, 'Select a .json study','', '*.json')
        if name_json:
            self.study_config.load(name_json)
            StudyConfigFomManager.check_and_update_foms(self.study_config)



    def show_process(self):
        """Launch simple process"""
        #FIXME utile je pense pour creer fichier json si existe pas..
        #self.study_config.save()
        process = self.get_process()
        #To have attributes on header
        process_with_fom = ProcessWithFom(process, self.study_config)
        self.process_gui = ProcessWithFomWidget(process_with_fom, process)
        self.process_gui.show()


    def run_pipeline_process(self):
        """Launch pipeline process"""
        raise NotImplementedError(
            'StudyWindow.run_pipeline_process(): not working yet.')


    def iterate_process(self):
        """Launch iteration process"""
        process = self.get_process()
        process_with_fom = ProcessWithFom(process, self.study_config)
        self.wizard = QtGui.QWizard()
        self.wizard.setButtonText(3, 'Run all')
        self.connect(self.wizard, QtCore.SIGNAL('currentIdChanged( int )'),
            self.on_page_changed)
        self.first_page = ProcessIterationGui(self.study_config)
        self.wizard.addPage(self.first_page)
        self.second_page = ProcessParametersTable(process, process_with_fom)
        self.connect(self.wizard.button(3), QtCore.SIGNAL('clicked()'),
            process_with_fom.iteration_run)
        self.wizard.addPage(self.second_page)
        self.wizard.show()


    def on_page_changed(self,ide):
        if ide==1:
            ##Check if subjects have selected
            if not self.second_page.list_subjects_selected:
                self.second_page.list_subjects_selected \
                    = self.first_page.list_subjects_selected[:]
                self.second_page.go()
            elif self.second_page.list_subjects_selected \
                    == self.first_page.list_subjects_selected:
                print 'NO SUBJECTS ADDED'

            else:
                self.add_element(self.first_page.list_subjects_selected,
                    self.second_page.list_subjects_selected)
                self.del_element(self.first_page.list_subjects_selected,
                    self.second_page.list_subjects_selected)
                self.second_page.list_subjects_selected \
                    = self.first_page.list_subjects_selected[:]


    def add_element(self, new_list, prev_list):
        list_add_element = [x for x in new_list if x not in prev_list]
        if list_add_element:
            self.second_page.add_element_on_table(list_add_element)


    def del_element(self, new_list,prev_list):
        list_del_element = [x for x in prev_list if x not in new_list]
        if list_del_element:
            for ele in list_del_element:
                self.second_page.del_element_on_table(ele)


    def on_display_database(self):
        process = self.get_process()
        self.display_database = ProcessDatabaseWidget(process,
            self.study_config)
        self.display_database.open()


    def get_process(self):
        """This will be automatic"""
        return get_process_instance(str(self.study_config.process))


if __name__ == '__main__':
    import sys
    soma_app = Application( 'soma.fom', '1.0' )
    # Register module to load and call functions before and/or after
    # initialization
    soma_app.plugin_modules.append( 'soma.fom' )
    # Application initialization (e.g. configuration file may be read here)
    soma_app.initialize()

    app = QtGui.QApplication( sys.argv )
    w = StudyWindow()
    if len(sys.argv) >= 2:
        study_file = sys.argv[1]
        w.study_config.load(study_file)
        StudyConfigFomManager.check_and_update_foms(w.study_config)
    w.show()
    app.exec_()
