##########################################################################
# CAPSUL - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

from traits.api import Bool, Str, Undefined, DictStrAny
from capsul.study_config.study_config import StudyConfigModule


class SomaWorkflowConfig(StudyConfigModule):
    def __init__(self, study_config, configuration):
        super(SomaWorkflowConfig, self).__init__(study_config, configuration)
        study_config.add_trait('use_soma_workflow', Bool(
            False,
            output=False,
            desc='Use soma woklow for the execution'))
        study_config.add_trait('somaworkflow_computing_resource', Str(
            Undefined,
            output=False,
            desc='Soma-woklow computing resource to be used to run processing'))
        study_config.add_trait(
            'somaworkflow_computing_resources_config',
            DictStrAny(
                {},
                output=False,
                desc='Soma-woklow computing resources configs'))

    def initialize_callbacks(self):
        self.study_config.on_trait_change(self.initialize_module, 'use_soma_workflow')
