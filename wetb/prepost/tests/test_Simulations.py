'''
Created on 05/11/2015

@author: MMPE
'''
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import unittest
import os
import filecmp
import shutil

import numpy as np
import pandas as pd

from wetb.prepost import dlctemplate as tmpl
from wetb.prepost import Simulations as sim
from wetb.fatigue_tools.fatigue import eq_load


class Template(unittest.TestCase):
    def setUp(self):
        self.basepath = os.path.dirname(__file__)


class TestGenerateInputs(Template):

    def test_launch_dlcs_excel(self):
        # manually configure paths, HAWC2 model root path is then constructed as
        # p_root_remote/PROJECT/sim_id, and p_root_local/PROJECT/sim_id
        # adopt accordingly when you have configured your directories differently
        p_root = os.path.join(self.basepath, 'data/')
        # project name, sim_id, master file name
        tmpl.PROJECT = 'demo_dlc'
        tmpl.MASTERFILE = 'demo_dlc_master_A0001.htc'
        # MODEL SOURCES, exchanche file sources
        tmpl.P_RUN = os.path.join(p_root, tmpl.PROJECT, 'remote/')
        tmpl.P_SOURCE = os.path.join(p_root, tmpl.PROJECT, 'source/')
        # location of the master file
        tmpl.P_MASTERFILE = os.path.join(p_root, tmpl.PROJECT,
                                         'source', 'htc', '_master/')
        # location of the pre and post processing data
        tmpl.POST_DIR = os.path.join(p_root, tmpl.PROJECT, 'remote',
                                     'prepost/')

        # make sure the remote dir is empty so a test does not pass on data
        # generated during a previous cycle
        if os.path.exists(os.path.join(p_root, tmpl.PROJECT, 'remote')):
            shutil.rmtree(os.path.join(p_root, tmpl.PROJECT, 'remote'))

        tmpl.force_dir = tmpl.P_RUN
        tmpl.launch_dlcs_excel('remote', silent=True, runmethod='gorm',
                               pbs_turb=True)

        # we can not check-in empty dirs so we can not compare the complete
        # directory structure withouth manually creating the empty dirs here
        for subdir in ['control', 'data', 'htc', 'pbs_in', 'pbs_in_turb',
                       'htc/_master', 'htc/dlc01_demos', 'pbs_in/dlc01_demos']:
            remote = os.path.join(p_root, tmpl.PROJECT, 'remote', subdir)
            ref = os.path.join(p_root, tmpl.PROJECT, 'ref', subdir)
            cmp = filecmp.dircmp(remote, ref)
            self.assertEqual(len(cmp.diff_files), 0, cmp.diff_files)
            self.assertEqual(len(cmp.right_only), 0, cmp.right_only)
            self.assertEqual(len(cmp.left_only), 0, cmp.left_only)

        # for the pickled file we can just read it
        remote = os.path.join(p_root, tmpl.PROJECT, 'remote', 'prepost')
        ref = os.path.join(p_root, tmpl.PROJECT, 'ref', 'prepost')
        cmp = filecmp.cmp(os.path.join(remote, 'remote_tags.txt'),
                          os.path.join(ref, 'remote_tags.txt'), shallow=False)
        self.assertTrue(cmp)
#        with open(os.path.join(remote, 'remote.pkl'), 'rb') as FILE:
#            pkl_remote = pickle.load(FILE)
#        with open(os.path.join(ref, 'remote.pkl'), 'rb') as FILE:
#            pkl_ref = pickle.load(FILE)
#        self.assertTrue(pkl_remote == pkl_ref)


class TestFatigueLifetime(Template):

    def test_leq_1hz(self):
        """Simple test of wetb.fatigue_tools.fatigue.eq_load using a sine
        signal.
        """
        amplitude = 1
        m = 1
        point_per_deg = 100

        # sine signal with 10 periods (20 peaks)
        nr_periods = 10
        time = np.linspace(0, nr_periods*2*np.pi, point_per_deg*180)
        neq = time[-1]
        # mean value of the signal shouldn't matter
        signal = amplitude * np.sin(time) + 5
        r_eq_1hz = eq_load(signal, no_bins=1, m=m, neq=neq)[0]
        r_eq_1hz_expected = ((2*nr_periods*amplitude**m)/neq)**(1/m)
        np.testing.assert_allclose(r_eq_1hz, r_eq_1hz_expected)

        # sine signal with 20 periods (40 peaks)
        nr_periods = 20
        time = np.linspace(0, nr_periods*2*np.pi, point_per_deg*180)
        neq = time[-1]
        # mean value of the signal shouldn't matter
        signal = amplitude * np.sin(time) + 9
        r_eq_1hz2 = eq_load(signal, no_bins=1, m=m, neq=neq)[0]
        r_eq_1hz_expected2 = ((2*nr_periods*amplitude**m)/neq)**(1/m)
        np.testing.assert_allclose(r_eq_1hz2, r_eq_1hz_expected2)

        # 1hz equivalent load should be independent of the length of the signal
        np.testing.assert_allclose(r_eq_1hz, r_eq_1hz2)

    def test_leq_life(self):
        """Verify if prepost.Simulation.Cases.fatigue_lifetime() returns
        the expected life time equivalent load.
        """
        # ---------------------------------------------------------------------
        # very simple case
        cases = {'case1':{'[post_dir]':'no-path', '[sim_id]':'A0'},
                 'case2':{'[post_dir]':'no-path', '[sim_id]':'A0'}}
        cc = sim.Cases(cases)

        fh_list = [('case1', 10/3600), ('case2', 20/3600)]
        dfs = pd.DataFrame({'m=1.0' : [2, 3],
                            'channel' : ['channel1', 'channel1'],
                            '[case_id]' : ['case1', 'case2']})
        neq_life = 1.0
        df_Leq = cc.fatigue_lifetime(dfs, neq_life, fh_lst=fh_list,
                                     save=False, update=False, csv=False,
                                     xlsx=False, silent=False)
        np.testing.assert_allclose(df_Leq['m=1.0'].values, 2*10 + 3*20)
        self.assertTrue(df_Leq['channel'].values[0]=='channel1')

        # ---------------------------------------------------------------------
        # slightly more complicated
        neq_life = 3.0
        df_Leq = cc.fatigue_lifetime(dfs, neq_life, fh_lst=fh_list,
                                     save=False, update=False, csv=False,
                                     xlsx=False, silent=False)
        np.testing.assert_allclose(df_Leq['m=1.0'].values,
                                   (2*10 + 3*20)/neq_life)

        # ---------------------------------------------------------------------
        # a bit more complex and also test the sorting of fh_lst and dfs
        cases = {'case1':{'[post_dir]':'no-path', '[sim_id]':'A0'},
                 'case2':{'[post_dir]':'no-path', '[sim_id]':'A0'},
                 'case3':{'[post_dir]':'no-path', '[sim_id]':'A0'},
                 'case4':{'[post_dir]':'no-path', '[sim_id]':'A0'}}
        cc = sim.Cases(cases)

        fh_list = [('case3', 10/3600), ('case2', 20/3600),
                   ('case1', 50/3600), ('case4', 40/3600)]
        dfs = pd.DataFrame({'m=3.0' : [2, 3, 4, 5],
                            'channel' : ['channel1']*4,
                            '[case_id]' : ['case4', 'case2', 'case3', 'case1']})
        neq_life = 5.0
        df_Leq = cc.fatigue_lifetime(dfs, neq_life, fh_lst=fh_list,
                                     save=False, update=False, csv=False,
                                     xlsx=False, silent=False)
        expected = ((2*2*2*40 + 3*3*3*20 + 4*4*4*10 + 5*5*5*50)/5)**(1/3)
        np.testing.assert_allclose(df_Leq['m=3.0'].values, expected)

        # ---------------------------------------------------------------------
        # more cases and with sorting
        base = {'[post_dir]':'no-path', '[sim_id]':'A0'}
        cases = {'case%i' % k : base for k in range(50)}
        cc = sim.Cases(cases)
        # reverse the order of how they appear in dfs and fh_lst
        fh_list = [('case%i' % k, k*10/3600) for k in range(49,-1,-1)]
        dfs = pd.DataFrame({'m=5.2' : np.arange(1,51,1),
                            'channel' : ['channel1']*50,
                            '[case_id]' : ['case%i' % k for k in range(50)]})
        df_Leq = cc.fatigue_lifetime(dfs, neq_life, fh_lst=fh_list,
                                     save=False, update=False, csv=False,
                                     xlsx=False, silent=False)
        expected = np.sum(np.power(np.arange(1,51,1), 5.2)*np.arange(0,50,1)*10)
        expected = np.power(expected/neq_life, 1/5.2)
        np.testing.assert_allclose(df_Leq['m=5.2'].values, expected)


if __name__ == "__main__":
    unittest.main()
