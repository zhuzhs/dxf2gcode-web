# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2009-2016
#    Christian Kohlöffel
#    Jean-Paul Schouwstra
#    Xavier Izard
#
#   This file is part of DXF2GCODE.
#
#   DXF2GCODE is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   DXF2GCODE is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with DXF2GCODE.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

from __future__ import absolute_import

import os
import sys
import pprint
import logging

from globals.configobj.configobj import ConfigObj, flatten_errors
from globals.configobj.validate import Validator
import globals.globals as g
from globals.d2gexceptions import *
from gui.configwindow import *

from globals.six import text_type
import globals.constants as c
if c.PYQT5notPYQT4:
    from PyQt5 import QtCore
else:
    from PyQt4 import QtCore

try:
    from collections import OrderedDict
except ImportError:
    from globals.ordereddict import OrderedDict

logger = logging.getLogger("Core.Config")

CONFIG_VERSION = "9.9"
"""
version tag - increment this each time you edit CONFIG_SPEC

compared to version number in config file so
old versions are recognized and skipped"
"""

# Paths change whether platform is Linux or Windows
if "linux" in sys.platform.lower() or "unix" in sys.platform.lower():
    #Declare here the path that are specific to Linux
    IMPORT_DIR = "~/Documents"
    OUTPUT_DIR = "~/Documents"
    PSTOEDIT_CMD = "/usr/bin/pstoedit"
else:
    #Declare here the path that are specific to Windows
    IMPORT_DIR = "D:/Eclipse_Workspace/DXF2GCODE/trunk/dxf"
    OUTPUT_DIR = "D:"
    PSTOEDIT_CMD = "C:/Program Files (x86)/pstoedit/pstoedit.exe"

"""
HOWTO declare a new variable in the config file:
1) Choose the appropriate section and add the variable in the CONFIG_SPEC string below
(Note: the CONFIG_SPEC is used to set and check the configfile "config.cfg")

2) Set it's default value, the min/max values (if applicable) and a comment above the variable's name
(Important note: the min/max values and the comment are directly used in the configuration window, so carefully set them!)
Example of correct declaration:
    [MySection]
    # Drag angle is used to blah blah blah ...
    drag_angle = float(min = 0, max = 360, default = 20)

3) If you want the setting to appear in the configuration window, fill the cfg_widget_def variable, using the _same_ names as in the CONFIG_SPEC
Example of declaration correlated to the above one:
    'MySection':
    {
        'drag_angle': CfgDoubleSpinBox('Drag angle (in degrees):'),
    }
(Note: the list of available types for the configuration window can be found in the "configwindow.py" file)
"""
"""
ATTENTION:
_Don't_ split the long comments lines in CONFIG_SPEC!
The comments line are used as "QWhatsThis" in the config window.
Any new line in the CONFIG_SPEC is reproduced in the QWhatsThis (intented behaviour to allow creating paragraphs)
ATTENTION
"""
CONFIG_SPEC = str('''
#  Section and variable names must be valid Python identifiers
#      do not use whitespace in names

# do not edit the following section name:
    [Version]
    # do not edit the following value:
    config_version = string(default = "''' +
    str(CONFIG_VERSION) + '")\n' +
    '''
    [Paths]
    # By default look for DXF files in this directory.
    import_dir = string(default = "''' + IMPORT_DIR + '''")

    # Export generated gcode by default to this directory.
    output_dir = string(default = "''' + OUTPUT_DIR + '''")

    [Filters]
    # pstoedit is an external tool to import *.ps (postscript) files and convert them to DXF, in order to import them in dxf2gcode.
    pstoedit_cmd = string(default = "''' + PSTOEDIT_CMD + '''")
    pstoedit_opt = list(default = list('-f', 'dxf', '-mm', '-dt'))

    [Axis_letters]
    ax1_letter = string(min = 1, default = "X")
    ax2_letter = string(min = 1, default = "Y")
    ax3_letter = string(min = 1, default = "Z")

    [Plane_Coordinates]
    axis1_start_end = float(default = 0)
    axis2_start_end = float(default = 0)

    [Depth_Coordinates]
    # Third axis' coordinate at which it can do rapid move.
    axis3_retract = float(default = 15.0)
    # Third axis' margin for which it needs to do a slow move.
    axis3_safe_margin = float(default = 3.0)
    # The top third axis' coordinate of the workpiece.
    axis3_start_mill_depth = float(default = 0.0)
    # Relative depth for each cut (third axis' coordinate will be decreased by this value at each step).
    axis3_slice_depth = float(default = -1.5)
    # Relative final third axis' depth.
    axis3_mill_depth = float(default = -3.0)

    [Feed_Rates]
    f_g1_plane = float(default = 400)
    f_g1_depth = float(default = 150)

    [General]
    # Write output to stdout (console), instead of a file. May be used to interface directly with Linux CNC, for example.
    write_to_stdout = boolean(default = False)
    # When enabled, the shapes that are disabled are still shown on the graphic view.
    show_disabled_paths = boolean(default = True)
    # When enabled, export path is live updated on the graphic view.
    live_update_export_route = boolean(default = False)
    # Divide the lines in 2 parts, in order to start the cutting in the middle of a line (usefull for cutter compensation)
    split_line_segments = boolean(default = False)
    # Automatically enable cutter compensation for all the shapes (G41 & G42)
    automatic_cutter_compensation = boolean(default = False)
    # Machine types supported: milling; lathe; drag_knife
    machine_type = option('milling', 'lathe', 'drag_knife', default = 'milling')
    # The unit used for all values in this file
    tool_units = option('mm', 'in', default = 'mm')

    [Cutter_Compensation]
    # If not checked, DXF2GCODE will create a virtual path for G41 and G42 command. And output will be set to G40; i.e. it will create the path that normally your machine would create with it's cutter compensation.
    done_by_machine = boolean(default = True)


    [Drag_Knife_Options]
    # drag_angle: if angle of movement exceeds this angle (in degrees), the tool retracts to dragDepth (The dragDepth is given by axis3_slice_depth parameter).
    # This parameter depends on the knife that you are using. A bigger knife cannot make small corners like a smaller knife. You will simply break your knife or destroy your working piece. Now, if the angle your knife has to make is bigger than this angle it will move to a different depth (a less deep position) such that the knife will experience less resistance but still has some (otherwise it will not change its angle at all, whence DRAG knife).
    drag_angle = float(min = 0, max = 360, default = 20)

    [Route_Optimisation]
    # If enabled, it will by default check the TSP for all the shapes in the treeview.
    # If disabled and no shape is checked for TSP optimisation in the listbox, the export order will be as defined in the listbox.
    default_TSP = boolean(default = False)

    # Path optimizer behaviour:
    # - CONSTRAIN_ORDER_ONLY: fixed Shapes and optimized Shapes can be mixed. Only order of fixed shapes is kept
    # - CONSTRAIN_PLACE_AFTER: optimized Shapes are always placed after any fixed Shape
    TSP_shape_order = option('CONSTRAIN_ORDER_ONLY', 'CONSTRAIN_PLACE_AFTER', default = 'CONSTRAIN_ORDER_ONLY')
    # This is a value of how much it should deviate the order with each iteration. The higher the value the more you allow alterations.
    mutation_rate = float(min = 0, max = 1, default = 0.95)
    # Number of people the population has for path optimization (values higher than 200 can make everything slow).
    max_population = integer(min = 0, max = 10000, default = 20)
    # Maximum number of iterations that will be done. This is internally also calculated, based on the number of shapes to optimize.
    # Values higher than 10000 can take really long to solve the TSP and are not recommended.
    max_iterations = integer(min = 1, max = 1000000, default = 300)
    # Different methods to initialize the population for the TSP optimizer.
    # - Ordered will start with the defined one in the listbox
    # - Random just random
    # - Heuristic will search the nearest neighbors and starts with the resulting order.
    begin_art = option('ordered', 'random', 'heuristic', default = 'heuristic')

    [Import_Parameters]
    # Tolerance at which similar points will be interpreted as similar
    point_tolerance = float(min = 0, max = 1, default = 0.001)
    # Types of check performed during spline conversion:
    # 1: Checking for Nurbs degree (polygon degree) and similar knots consistence
    # 2: Checking for Nurbs degree (polygon degree) and similar control points
    # 3: Performes check 1 and check 2
    spline_check = integer(min = 1, max = 3, default = 3)
    # This is the tolerance which is used to fit the converted lines and arc segments to the converted NURBS.
    fitting_tolerance = float(min = 0, max = 1, default = 0.001)
    # If checked, the elements (shape, ...) which are part of a block will be inserted on the layer that belongs to the block (even though the elements might be defined on a different layers)
    insert_at_block_layer = boolean(default = False)

    # These settings are intented to be used in the DXF file:
    # - By using MILL: as a prefix to your layer name, you can define milling parameters by using one of the following identifiers.
    # - Example of a layer name: MILL: 1 Md: 2 Sd: 2 FeedXY: 400 FeedZ: 200
    #   (This will cut shapes on the layer 2 mm deep (in one pass, since Sd == Md) using 400 mm / minute speed for X/Y movement and 200 mm / minute for Z movement)
    [Layer_Options]
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    id_float_separator = string(default = ":")

    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    mill_depth_identifiers = list(default = list('MillDepth', 'Md', 'TiefeGesamt', 'Tg'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    slice_depth_identifiers = list(default = list('SliceDepth', 'Sd', 'TiefeZustellung', 'Tz'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    start_mill_depth_identifiers = list(default = list('StartMillDepth', 'SMd', 'StartTiefe', 'St'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    retract_identifiers = list(default = list('RetractHeight', 'Rh', 'Freifahrthoehe', 'FFh'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    safe_margin_identifiers = list(default = list('SafeMargin', 'Sm', 'Sicherheitshoehe', 'Sh'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    f_g1_plane_identifiers = list(default = list('FeedXY', 'Fxy', 'VorschubXY', 'Vxy', 'F'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    f_g1_depth_identifiers = list(default = list('FeedZ', 'Fz', 'VorschubZ', 'Vz'))

    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    tool_nr_identifiers = list(default = list('ToolNr', 'Tn', 'T', 'WerkzeugNummer', 'Wn'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    tool_diameter_identifiers = list(default = list('ToolDiameter', 'Td', 'WerkzeugDurchmesser', 'Wd'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    spindle_speed_identifiers = list(default = list('SpindleSpeed', 'Drehzahl', 'RPM', 'UPM', 'S'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    start_radius_identifiers = list(default = list('StartRadius', 'Sr'))

    # Tools table: define here the tools used for milling:
    # - name: this is the number of the tool, it will be used directly in the GCODE (eg 20 for tool T20)
    # - diameter: diameter of the tool
    # - speed: spindle speed in rpm
    # - start_radius: start radius for tool compensation when using G41 / G42 moves
    [Tool_Parameters]
    [[1]]
    diameter = float(default = 2.0)
    speed = float(default = 6000)
    start_radius = float(default = 0.2)

    [[2]]
    diameter = float(default = 2.0)
    speed = float(default = 6000.0)
    start_radius = float(default = 1.0)

    [[10]]
    diameter = float(default = 10.0)
    speed = float(default = 6000.0)
    start_radius = float(default = 2.0)

    [[__many__]]
    diameter = float(default = 3.0)
    speed = float(default = 6000)
    start_radius = float(default = 3.0)

    # Define here custom GCODE actions:
    # - name: this is the unique name of the action
    # - gcode: the text that will be inserted in the final program (each new line is also translated as a new line in the output file)
    # Custom actions can be inserted in the program by using right-click contextual menu on the treeview.
    [Custom_Actions]
    [[__many__]]
    gcode = string(default = "(change subsection name and insert your custom GCode here. Use triple quote to place the code on several lines)")

    [Logging]
    # Logging to textfile is enabled automatically for now
    logfile = string(default = "logfile.txt")

    # This really goes to stderr
    console_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'CRITICAL')

    # Log levels are, in increasing importance: DEBUG; INFO; WARNING; ERROR; CRITICAL
    # Log events with importance >= loglevel are logged to the corresponding output
    file_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'DEBUG')

    # Logging level for the message window
    window_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'INFO')

''').splitlines()
""" format, type and default value specification of the global config file"""


class MyConfig(object):
    """
    This class hosts all functions related to the Config File.
    """
    def __init__(self):
        """
        initialize the varspace of an existing plugin instance
        init_varspace() is a superclass method of plugin
        """

        self.folder = os.path.join(g.folder, c.DEFAULT_CONFIG_DIR)
        self.filename = os.path.join(self.folder, 'config' + c.CONFIG_EXTENSION)

        self.version_mismatch = '' # no problem for now
        self.default_config = False # whether a new name was generated
        self.var_dict = dict()
        self.spec = ConfigObj(CONFIG_SPEC, interpolation=False, list_values=False, _inspec=True)

        # try:

        self.load_config()
        self.update_config()

        # The following settings won't be modified after a change in the configuration window.
        # If a setting need to be updated when the configuration changes, move it to the update_config() function

        self.machine_type = self.vars.General['machine_type']
        self.fitting_tolerance = self.vars.Import_Parameters['fitting_tolerance']
        self.point_tolerance = self.vars.Import_Parameters['point_tolerance']

        self.metric = 1  # true unit is determined while importing
        self.tool_units = self.vars.General['tool_units'] # store the initial tool_units (we don't want it to change until software restart)
        self.tool_units_metric = 0 if self.vars.General['tool_units'] == 'in' else 1

        # except Exception, msg:
        #     logger.warning(self.tr("Config loading failed: %s") % msg)
        #     return False

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return text_type(string_to_translate)

    def update_config(self):
        """
        Call this function each time the self.var_dict is updated (eg when the configuration window changes some settings)
        """
        # convenience - flatten nested config dict to access it via self.config.sectionname.varname
        self.vars = DictDotLookup(self.var_dict)
        # add here any update needed for the internal variables of this class

    def make_settings_folder(self):
        """Create settings folder if necessary"""
        try:
            os.mkdir(self.folder)
        except OSError:
            pass

    def load_config(self):
        """Load Config File"""
        if os.path.isfile(self.filename):
            try:
                # file exists, read & validate it
                self.var_dict = ConfigObj(self.filename, configspec=CONFIG_SPEC)
                _vdt = Validator()
                result = self.var_dict.validate(_vdt, preserve_errors=True)
                validate_errors = flatten_errors(self.var_dict, result)

                if validate_errors:
                    logger.error(self.tr("errors reading %s:") % self.filename)

                for entry in validate_errors:
                    section_list, key, error = entry
                    if key is not None:
                        section_list.append(key)
                    else:
                        section_list.append('[missing section]')
                    section_string = ', '.join(section_list)
                    if not error:
                        error = self.tr('Missing value or section.')
                    logger.error(section_string + ' = ' + error)

                if validate_errors:
                    raise BadConfigFileError("syntax errors in config file")

                # check config file version against internal version
                if CONFIG_VERSION:
                    fileversion = self.var_dict['Version']['config_version']  # this could raise KeyError

                    if fileversion != CONFIG_VERSION:
                        raise VersionMismatchError(fileversion, CONFIG_VERSION)

            except VersionMismatchError:
                #raise VersionMismatchError(fileversion, CONFIG_VERSION)
                # version mismatch flag, it will be used to display an error.
                self.version_mismatch = self.tr("The configuration file version ({0}) doesn't match the software expected version ({1}).\n\nYou have to delete (or carefully edit) the configuration file \"{2}\" to solve the problem.").format(fileversion, CONFIG_VERSION, self.filename)

            except Exception as inst:
                logger.error(inst)
                (base, ext) = os.path.splitext(self.filename)
                badfilename = base + c.BAD_CONFIG_EXTENSION
                logger.debug(self.tr("trying to rename bad cfg %s to %s") % (self.filename, badfilename))
                try:
                    os.rename(self.filename, badfilename)
                except OSError as e:
                    logger.error(self.tr("rename(%s,%s) failed: %s") % (self.filename, badfilename, e.strerror))
                    raise
                else:
                    logger.debug(self.tr("renamed bad varspace %s to '%s'") % (self.filename, badfilename))
                    self.create_default_config()
                    self.default_config = True
                    logger.debug(self.tr("created default varspace '%s'") % self.filename)
            else:
                self.default_config = False
                # logger.debug(self.dir())
                # logger.debug(self.tr("created default varspace '%s'") % self.filename)
                # logger.debug(self.tr("read existing varspace '%s'") % self.filename)
        else:
            self.create_default_config()
            self.default_config = True
            logger.debug(self.tr("created default varspace '%s'") % self.filename)

        self.var_dict.main.interpolation = False  # avoid ConfigObj getting too clever

    def create_default_config(self):
        # check for existing setting folder or create one
        self.make_settings_folder()

        # derive config file with defaults from spec
        self.var_dict = ConfigObj(configspec=CONFIG_SPEC)
        _vdt = Validator()
        self.var_dict.validate(_vdt, copy=True)
        self.var_dict.filename = self.filename
        self.var_dict.write()

    def save_varspace(self):
        """Saves Variables space"""
        self.var_dict.filename = self.filename
        self.var_dict.write()

    def print_vars(self):
        """Prints Variables"""
        print("Variables:")
        for k, v in self.var_dict['Variables'].items():
            print(k, "=", v)

    def makeConfigWidgets(self):
        """
        Build the configuration widgets and store them into a dictionary.
        The structure of the dictionnary must match the structure of the configuration file. The names of the keys must be identical to those used in the configfile.
        If a name is declared in the configfile but not here, it simply won't appear in the config window (the config_version for example must not be modified by the user, so it is not declared here)
        """
        coordinate_unit = self.tr(" mm") if self.tool_units_metric else self.tr(" in")
        speed_unit = self.tr(" mm/min") if self.tool_units_metric else self.tr(" IPS")
        cfg_widget_def = OrderedDict([ ])

        return cfg_widget_def


class DictDotLookup(object):
    """
    Creates objects that behave much like a dictionaries, but allow nested
    key access using object '.' (dot) lookups.
    """
    def __init__(self, d):
        for k in d:
            if isinstance(d[k], dict):
                self.__dict__[k] = DictDotLookup(d[k])
            elif isinstance(d[k], (list, tuple)):
                l = []
                for v in d[k]:
                    if isinstance(v, dict):
                        l.append(DictDotLookup(v))
                    else:
                        l.append(v)
                self.__dict__[k] = l
            else:
                self.__dict__[k] = d[k]

    def __getitem__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]

    def __setitem__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value

    def __iter__(self):
        return iter(self.__dict__.keys())

    def __repr__(self):
        return pprint.pformat(self.__dict__)

# if __name__ == '__main__':
#     cfg_data = eval("""{
#         'foo' : {
#             'bar' : {
#                 'tdata' : (
#                     {'baz' : 1 },
#                     {'baz' : 2 },
#                     {'baz' : 3 },
#                 ),
#             },
#         },
#         'quux' : False,
#     }""")
#
#     cfg = DictDotLookup(cfg_data)
#
#     # iterate
#     for k, v in cfg.__iter__(): #foo.bar.iteritems():
#         print k, " = ", v
#
#     print "cfg=", cfg
#
#     #   Standard nested dictionary lookup.
#     print 'normal lookup :', cfg['foo']['bar']['tdata'][0]['baz']
#
#     #   Dot-style nested lookup.
#     print 'dot lookup    :', cfg.foo.bar.tdata[0].baz
#
#     print "qux=", cfg.quux
#     cfg.quux = '123'
#     print "qux=", cfg.quux
#
#     del cfg.foo.bar
#     cfg.foo.bar = 4711
#     print 'dot lookup    :', cfg.foo.bar #.tdata[0].baz
