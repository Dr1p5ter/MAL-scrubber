#!/bin/bash

season_data_test_path='_test_season_data'
test_file_name='test.py'

# make the directory and ensure that it is empty
mkdir -pv $season_data_test_path
rm -rfv $season_data_test_path/*

# run the testing file
python3 -m unittest -vc $test_file_name

# remove the directory
rm -rfv $season_data_test_path/*
rmdir -pv $season_data_test_path