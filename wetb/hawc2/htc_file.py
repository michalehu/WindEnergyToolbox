'''
Created on 20/01/2014

@author: MMPE

See documentation of HTCFile below

'''
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from io import open
from builtins import str
from future import standard_library
from wetb.utils.process_exec import pexec, unix_filename
standard_library.install_aliases()
from collections import OrderedDict

from wetb.hawc2.htc_contents import HTCContents, HTCSection, HTCLine, \
    HTCDefaults
import os
from copy import copy


class HTCFile(HTCContents, HTCDefaults):
    """Wrapper for HTC files

    Examples:
    ---------
    >>> htcfile = HTCFile('htc/test.htc')
    >>> htcfile.wind.wsp = 10
    >>> htcfile.save()
    """

    filename = None
    htc_inputfiles = []
    level = 0
    modelpath = "../"
    initial_comments = None
    def __init__(self, filename=None, modelpath="../"):
        self.modelpath = modelpath
        self.contents = OrderedDict()
        self.initial_comments = []
        self.htc_inputfiles = []
        if filename is None:
            self.filename = 'empty.htc'
            self.lines = self.empty_htc.split("\n")
        else:
            self.filename = filename
            self.modelpath = os.path.realpath(os.path.join(os.path.dirname(self.filename), modelpath))
            self.lines = self.readlines(filename)
#            with open(filename) as fid:
#                self.lines = fid.readlines()
        self.lines = [l.strip() for l in self.lines]

        lines = copy(self.lines)
        while lines:
            if lines[0].startswith(";"):
                self.initial_comments.append(lines.pop(0).strip() + "\n")
            elif lines[0].lower().startswith("begin"):
                self._add_contents(HTCSection.from_lines(lines))
            else:
                line = HTCLine.from_lines(lines)
                self._add_contents(line)
                if line.name_ == "exit":
                    break
        #assert 'simulation' in self.contents, "%s could not be loaded. 'simulation' section missing" % filename


    def readfilelines(self, filename):
        with open(unix_filename(filename), encoding='cp1252') as fid:
            lines = list(fid.readlines())
        if lines[0].encode().startswith(b'\xc3\xaf\xc2\xbb\xc2\xbf'):
            lines[0] = lines[0][3:]
        return lines

    def readlines(self, filename):
        self.htc_inputfiles.append(filename)
        htc_lines = []
        lines = self.readfilelines(filename)
        for l in lines:
            if l.lower().lstrip().startswith('continue_in_file'):
                filename = l.lstrip().split(";")[0][len("continue_in_file"):].strip().lower()
                filename = os.path.join(self.modelpath, filename)

                for line in self.readlines(filename):
                    if line.lstrip().lower().startswith('exit'):
                        break
                    htc_lines.append(line)
            else:
                htc_lines.append(l)
        return htc_lines


    def __setitem__(self, key, value):
        self.contents[key] = value

    def __str__(self):
        return "".join(self.initial_comments + [c.__str__(1) for c in self])

    def save(self, filename=None):
        if filename is None:
            filename = self.filename
        else:
            self.filename = filename
        # exist_ok does not exist in Python27
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))  #, exist_ok=True)
        with open(filename, 'w', encoding='cp1252') as fid:
            fid.write(str(self))

    def set_name(self, name, htc_folder="htc", log_folder="log", res_folder="res"):
        #if os.path.isabs(folder) is False and os.path.relpath(folder).startswith("htc" + os.path.sep):
        fmt_folder = lambda folder : "./" + os.path.relpath(folder).replace("\\", "/")

        self.filename = os.path.abspath(os.path.join(self.modelpath, fmt_folder(htc_folder), "%s.htc" % name)).replace("\\", "/")
        if 'simulation' in self and 'logfile' in self.simulation:
            self.simulation.logfile = os.path.join(fmt_folder(log_folder), "%s.log" % name).replace("\\", "/")
        elif 'test_structure' in self and 'logfile' in self.test_structure:  # hawc2aero
            self.test_structure.logfile = os.path.join(fmt_folder(log_folder), "%s.log" % name).replace("\\", "/")
        self.output.filename = os.path.join(fmt_folder(res_folder), "%s" % name).replace("\\", "/")

    def set_time(self, start=None, stop=None, step=None):
        if stop is not None:
            self.simulation.time_stop = stop
        else:
            stop = self.simulation.time_stop[0]
        if step is not None:
            self.simulation.newmark.deltat = step
        if start is not None:
            self.output.time = start, stop
            if "wind" in self and self.wind.turb_format[0] > 0:
                self.wind.scale_time_start = start

    def input_files(self):
        files = self.htc_inputfiles
        if 'new_htc_structure' in self:
            for mb in [self.new_htc_structure[mb] for mb in self.new_htc_structure.keys() if mb.startswith('main_body')]:
                if "timoschenko_input" in mb:
                    files.append(mb.timoschenko_input.filename[0])
                files.append(mb.get('external_bladedata_dll', [None, None, None])[2])
        if 'aero' in self:
            files.append(self.aero.ae_filename[0])
            files.append(self.aero.pc_filename[0])
            files.append(self.aero.get('external_bladedata_dll', [None, None, None])[2])
            files.append(self.aero.get('output_profile_coef_filename', [None])[0])
            if 'dynstall_ateflap' in self.aero:
                files.append(self.aero.dynstall_ateflap.get('flap', [None] * 3)[2])
            if 'bemwake_method' in self.aero:
                files.append(self.aero.bemwake_method.get('a-ct-filename', [None] * 3)[0])
        for dll in [self.dll[dll] for dll in self.get('dll', {}).keys()]:
            files.append(dll.filename[0])
        if 'wind' in self:
            files.append(self.wind.get('user_defined_shear', [None])[0])
            files.append(self.wind.get('wind.user_defined_shear_turbulence', [None])[0])
        if 'wakes' in self:
            files.append(self.wind.get('use_specific_deficit_file', [None])[0])
            files.append(self.wind.get('write_ct_cq_file', [None])[0])
            files.append(self.wind.get('write_final_deficits', [None])[0])
        if 'hydro' in self:
            if 'water_properties' in self.hydro:
                files.append(self.hydro.water_properties.get('water_kinematics_dll', [None])[0])
                files.append(self.hydro.water_properties.get('water_kinematics_dll', [None, None])[1])
        if 'soil' in self:
            if 'soil_element' in self.soil:
                files.append(self.soil.soil_element.get('datafile', [None])[0])
        try:
            files.append(self.force.dll.dll[0])
        except:
            pass

        return [f for f in set(files) if f]

    def output_files(self):
        files = []
        for k, index in [('simulation/logfile', 0),
                         ('simulation/animation', 0),
                         ('simulation/visualization', 0),
                         ('new_htc_structure/beam_output_file_name', 0),
                         ('new_htc_structure/body_output_file_name', 0),
                         ('new_htc_structure/struct_inertia_output_file_name', 0),
                         ('new_htc_structure/body_eigenanalysis_file_name', 0),
                         ('new_htc_structure/constraint_output_file_name', 0),
                         ('turb_export/filename_u', 0),
                         ('turb_export/filename_v', 0),
                         ('turb_export/filename_w', 0)]:
            line = self.get(k)
            if line:
                files.append(line[index])
        if 'new_htc_structure' in self:
            if 'system_eigenanalysis' in self.new_htc_structure:
                f = self.new_htc_structure.system_eigenanalysis[0]
                files.append(f)
                files.append(os.path.join(os.path.dirname(f), 'mode*.dat').replace("\\", "/"))
            if 'structure_eigenanalysis_file_name' in self.new_htc_structure:
                f = self.new_htc_structure.structure_eigenanalysis_file_name[0]
                files.append(f)
                files.append(os.path.join(os.path.dirname(f), 'mode*.dat').replace("\\", "/"))
        files.extend(self.res_file_lst())

        for key in [k for k in self.contents.keys() if k.startswith("output_at_time")]:
            files.append(self[key]['filename'][0] + ".dat")
        return [f for f in files if f]

    def turbulence_files(self):
        if 'wind' not in self.contents.keys() or self.wind.turb_format[0] == 0:
            return []
        elif self.wind.turb_format[0] == 1:
            files = [self.get('wind.mann.filename_%s' % comp, [None])[0] for comp in ['u', 'v', 'w']]
        elif self.wind.turb_format[0] == 2:
            files = [self.get('wind.flex.filename_%s' % comp, [None])[0] for comp in ['u', 'v', 'w']]
        return [f for f in files if f]


    def res_file_lst(self):
        if 'output' not in self:
            return []
        dataformat = self.output.get('data_format', 'hawc_ascii')
        res_filename = self.output.filename[0]
        if dataformat[0] == "gtsdf" or dataformat[0] == "gtsdf64":
            return [res_filename + ".hdf5"]
        elif dataformat[0] == "flex_int":
            return [res_filename + ".int", os.path.join(os.path.dirname(res_filename), 'sensor')]
        else:
            return [res_filename + ".sel", res_filename + ".dat"]


    def simulate(self, exe, skip_if_up_to_date=False):
        if skip_if_up_to_date:
            from os.path import isfile, getmtime, isabs
            res_file = os.path.join(self.modelpath, self.res_file_lst()[0])
            htc_file = os.path.join(self.modelpath, self.filename)
            if isabs(exe):
                exe_file = exe
            else:
                exe_file = os.path.join(self.modelpath, exe)
            #print (from_unix(getmtime(res_file)), from_unix(getmtime(htc_file)))
            if (isfile(htc_file) and isfile(res_file) and isfile(exe_file) and
                getmtime(res_file) > getmtime(htc_file) and getmtime(res_file) > getmtime(exe_file)):
                if "".join(self.readfilelines(htc_file)) == str(self):
                        return

        self.save()
        htcfile = os.path.relpath(self.filename, self.modelpath)
        hawc2exe = exe
        errorcode, stdout, stderr, cmd = pexec([hawc2exe, htcfile], self.modelpath)

        if "logfile" in self.simulation:
            with open(os.path.join(self.modelpath, self.simulation.logfile[0])) as fid:
                log = fid.read()
        else:
            log = stderr


        if errorcode or 'Elapsed time' not in log:
            raise Exception (str(stdout) + str(stderr))

class H2aeroHTCFile(HTCFile):
    def __init__(self, filename=None, modelpath="../"):
        HTCFile.__init__(self, filename=filename, modelpath=modelpath)

    @property
    def simulation(self):
        return self.test_structure

    def set_time(self, start=None, stop=None, step=None):
        if stop is not None:
            self.test_structure.time_stop = stop
        else:
            stop = self.simulation.time_stop[0]
        if step is not None:
            self.test_structure.deltat = step
        if start is not None:
            self.output.time = start, stop
            if "wind" in self and self.wind.turb_format[0] > 0:
                self.wind.scale_time_start = start


if "__main__" == __name__:
    f = HTCFile(r"C:\mmpe\HAWC2\models\DTU10MWRef6.0\htc\DTU_10MW_RWT_power_curve.htc", "../")
    f.save(r"C:\mmpe\HAWC2\models\DTU10MWRef6.0\htc\DTU_10MW_RWT_power_curve.htc")

    f = HTCFile(r"C:\mmpe\HAWC2\models\DTU10MWRef6.0\htc\DTU_10MW_RWT.htc", "../")
    f.save(r"C:\mmpe\HAWC2\models\DTU10MWRef6.0\htc\DTU_10MW_RWT.htc")

