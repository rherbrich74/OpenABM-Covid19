#!/usr/bin/env python3
"""
Tests of the individual-based model, COVID19-IBM, using the individual file

Usage:
With pytest installed (https://docs.pytest.org/en/latest/getting-started.html) tests can be 
run by calling 'pytest' from project folder.  

Created: March 2020
Author: p-robot
"""

import subprocess, shutil, os
from os.path import join
import numpy as np, pandas as pd
import pytest

from parameters import ParameterSet
import utilities as utils

# Directories
IBM_DIR = "src"
IBM_DIR_TEST = "src_test"
DATA_DIR_TEST = "data_test"

TEST_DATA_TEMPLATE = "./tests/data/baseline_parameters.csv"
TEST_DATA_FILE = join(DATA_DIR_TEST, "test_parameters.csv")

TEST_OUTPUT_FILE = join(DATA_DIR_TEST, "test_output.csv")
TEST_INDIVIDUAL_FILE = join(DATA_DIR_TEST, "individual_file_Run1.csv")

TEST_HOUSEHOLD_TEMPLATE = "./tests/data/baseline_household_demographics.csv"
TEST_HOUSEHOLD_FILE = join(DATA_DIR_TEST, "test_household_demographics.csv")

PARAM_LINE_NUMBER = 1

# Construct the executable command
EXE = "covid19ibm.exe {} {} {} {}".format(TEST_DATA_FILE,
                                       PARAM_LINE_NUMBER,
                                       DATA_DIR_TEST, 
                                       TEST_HOUSEHOLD_FILE)

command = join(IBM_DIR_TEST, EXE)

def pytest_generate_tests(metafunc):
    # called once per each test function
    funcarglist = metafunc.cls.params[metafunc.function.__name__]
    argnames = sorted(funcarglist[0])
    metafunc.parametrize(
        argnames, [[funcargs[name] for name in argnames] for funcargs in funcarglist]
    )



class TestClass(object):
    params = {
        "test_file_exists": [dict()],
        "test_disease_transition_times": [ 
            dict(
                mean_time_to_symptoms = 4.0,
                sd_time_to_symptoms   = 2.0,
                mean_time_to_hospital = 1.0,
                mean_time_to_critical = 1.0
            ), 
            dict( 
                mean_time_to_symptoms = 4.5,
                sd_time_to_symptoms   = 2.0,
                mean_time_to_hospital = 1.2,
                mean_time_to_critical = 1.2
            ),
            dict(
                mean_time_to_symptoms = 5.0,
                sd_time_to_symptoms   = 2.5,
                mean_time_to_hospital = 1.4,
                mean_time_to_critical = 1.4
            ),
            dict(
                mean_time_to_symptoms = 5.5,
                sd_time_to_symptoms   = 2.5,
                mean_time_to_hospital = 1.6,
                mean_time_to_critical = 1.6
            ),
            dict(
                mean_time_to_symptoms = 6.0,
                sd_time_to_symptoms   = 3.0,
                mean_time_to_hospital = 1.8,
                mean_time_to_critical = 2.0
            ),
            dict(
                mean_time_to_symptoms = 6.5,
                sd_time_to_symptoms   = 3.0,
                mean_time_to_hospital = 1.6,
                mean_time_to_critical = 2.0
            )
        ] 
        }
    """
    Test class for checking 
    """
    @classmethod
    def setup_class(self):
        """
        When the class is instantiated: compile the IBM in a temporary directory
        """
        
        # Make a temporary copy of the code (remove this temporary directory if it already exists)
        shutil.rmtree(IBM_DIR_TEST, ignore_errors = True)
        shutil.copytree(IBM_DIR, IBM_DIR_TEST)
                
        # Construct the compilation command and compile
        compile_command = "make clean; make all"
        completed_compilation = subprocess.run([compile_command], 
            shell = True, cwd = IBM_DIR_TEST, capture_output = True)
    
    @classmethod
    def teardown_class(self):
        """
        Remove the temporary code directory (when this class is removed)
        """
        shutil.rmtree(IBM_DIR_TEST, ignore_errors = True)
    
    def setup_method(self):
        """
        Called before each method is run; creates a new data dir, copies test datasets
        """
        os.mkdir(DATA_DIR_TEST)
        shutil.copy(TEST_DATA_TEMPLATE, TEST_DATA_FILE)
        shutil.copy(TEST_HOUSEHOLD_TEMPLATE, TEST_HOUSEHOLD_FILE)
        
        # Adjust any parameters that need adjusting for all tests
        params = ParameterSet(TEST_DATA_FILE, line_number = 1)
        params.set_param("n_total", 10000)
        params.set_param("end_time", 100)
        params.write_params(TEST_DATA_FILE)
        
    def teardown_method(self):
        """
        At the end of each method (test), remove the directory of test input/output data
        """
        shutil.rmtree(DATA_DIR_TEST, ignore_errors = True)
        
    def test_file_exists(self):
        """
        Test that the individual file exists
        """
        
        # Call the model using baseline parameters, pipe output to file, read output file
        file_output = open(TEST_OUTPUT_FILE, "w")
        completed_run = subprocess.run([command], stdout = file_output, shell = True)
        
        df_output = pd.read_csv(TEST_OUTPUT_FILE, comment = "#", sep = ",")
        df_individual = pd.read_csv(TEST_INDIVIDUAL_FILE, comment = "#", sep = ",")
        
        np.testing.assert_equal(df_individual.shape[0] > 1, True)


    def test_disease_transition_times(
            self,
            mean_time_to_symptoms,
            sd_time_to_symptoms,
            mean_time_to_hospital,
            mean_time_to_critical
        ):
        """
        Test that the mean and standard deviation of the transition times between 
        states agrees with the parameters
        """
        tolerance_mean = 0.1
        tolerance_sd   = 0.2
        
        params = ParameterSet(TEST_DATA_FILE, line_number = 1)
        params.set_param("n_total", 10000)
        params.set_param("n_seed_infection",200)
        params.set_param("end_time", 70)
        params.set_param("infectious_rate", 4.0)  
        params.set_param("mean_time_to_symptoms",mean_time_to_symptoms)
        params.set_param("sd_time_to_symptoms",sd_time_to_symptoms)
        params.set_param("mean_time_to_hospital",mean_time_to_hospital)
        params.set_param("mean_time_to_critical",mean_time_to_critical)
        params.write_params(TEST_DATA_FILE)
    
        file_output = open(TEST_OUTPUT_FILE, "w")
        completed_run = subprocess.run([command], stdout = file_output, shell = True)
        df_indiv = pd.read_csv(TEST_INDIVIDUAL_FILE, comment = "#", sep = ",", skipinitialspace = True )
        
        # time infected until showing symptoms
        df_indiv["t_p_s"] =  df_indiv["time_symptomatic"] - df_indiv["time_infected"]  
        mean = df_indiv[ ( df_indiv['time_infected'] > 0 ) & ( df_indiv['time_asymptomatic'] <0 ) ] [ "t_p_s" ].mean()
        sd   = df_indiv[ ( df_indiv['time_infected'] > 0 ) & ( df_indiv['time_asymptomatic'] <0 ) ] [ "t_p_s" ].std()
        np.testing.assert_allclose( mean, mean_time_to_symptoms, atol = tolerance_mean )
        np.testing.assert_allclose( sd, sd_time_to_symptoms, atol = tolerance_sd )
                               
        # time showing symptoms until going to hospital
        df_indiv["t_s_h"] =  df_indiv["time_hospitalised"] - df_indiv["time_symptomatic"]  
        mean = df_indiv[ ( df_indiv['time_hospitalised'] > 0 ) ] [ "t_s_h" ].mean()
        np.testing.assert_allclose( mean, mean_time_to_hospital, atol = tolerance_mean )
        
        # time hospitalilsed until moving to the ICU
        df_indiv["t_h_c"] =  df_indiv["time_critical"] - df_indiv["time_hospitalised"]  
        mean = df_indiv[ ( df_indiv['time_critical'] > 0 ) ] [ "t_h_c" ].mean()
        np.testing.assert_allclose( mean, mean_time_to_critical, atol = tolerance_mean )
        