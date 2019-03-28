import os
import csv
from pathlib import Path
import Utility
import numpy as np
from tensorflow import keras


#TODO: this python file is only used for the accuracy test
#TODO: to be deleted


#Get useful directories for further operation
current_path = os.path.abspath(os.path.dirname(__file__))
current_path_parent = str(Path(current_path).parent)
path_raw = current_path_parent + '/data/raw'
path_features_windowing = current_path_parent + '/data/features_windowing'
path_features_windowing_noisy = current_path_parent + '/data/features_windowing_noisy'
path_raw_windowing = current_path_parent + '/data/raw_windowing'
path_raw_windowing_noisy = current_path_parent + '/data/raw_windowing_noisy'



#Rotate the raw data (one sample) for easier process
#input: signal with 80000 rows and 8 columns
#output: signal with 8 rows and 80000 columns
def rotate_raw_data(raw_data):
    rotated_data = []
    raw_data = np.array(raw_data)
    for i in range(len(raw_data[0])):
        rotated_data.append(raw_data[:,i])
    return rotated_data

#Add noise to the raw data (on sample) for testing robustness
#input: signal with 8 rows and 80000 columns
#output: signal with 8 rows and 80000 columns with extra noise
#TODO unfinished
def add_noise():
    return 0

#Crop the signal if necessary
#input: signal with 8 rows and 80000 columns
#output: signal with 8 rows and n columns
def crop_data(data, n):
    cropped_data = []
    for row in data:
        cropped_data.append(row[:n])
    return cropped_data

#Implement data windowing on each sample
#input: a signal with 8 rows and n columns
#output: a list of components of a signal generated by data windowing
def data_windowing(data, size, interval):
    components_list = []
    counter = 0
    while counter <= len(data[0]) - size:
        component = []
        for row in data:
            component.append(row[counter:counter+size])
        components_list.append(component)
        counter = counter + interval
    return components_list

#Apply wavelet analyse on the data
#input: a signal with 8 rows and n columns, n = the size of window
#output: a matrix with 8 * a rows and n columns, a = the number of components generated by each channel, in my case a = 6
def wavelet_analyse(data):
    wavelet_analysed_data = []
    for row in data:
        wavelet_analysed_data.extend(Utility.wavelet_analysis(row))
    return wavelet_analysed_data

#Extract features from each channel
#input: a matrix with 48 rows and n columns
#output: a matrix with 48 rows and m columns where m is the number of features, in my case, m = 5
def extract_features_1(data):
    feature_matrix = []
    for row in data:
        feature_matrix.append([Utility.get_mean_absolute_value(row), Utility.get_waveform_length(row)])
    return feature_matrix

def extract_features_2(data):
    feature_matrix = []
    for row in data:
        feature_matrix.append([Utility.get_mean_absolute_value(row), Utility.get_root_mean_square(row)])
    return feature_matrix




#Following functions are the combination of functions above and will be called latter to write down modified data
#crop_size = 20000, window_size = 4000, interval = 1000
def write_raw_windowing(crop_size, window_size, interval):
    for filename in os.listdir(path_raw):
        if filename.endswith(".csv"):
            os.chdir(path_raw)
            f = open(filename)
            original_matrix = Utility.read_csv(f)
            
            #Do the normalization
            original_matrix_norm = keras.utils.normalize(original_matrix)
            
            rotated_matrix = rotate_raw_data(original_matrix_norm)
            cropped_matrix = crop_data(rotated_matrix, crop_size)
            
            components_list = data_windowing(cropped_matrix, window_size, interval)
            cropped_filename = os.path.splitext(filename)[0][0:7] + "_"
            counter = 0
            for component in components_list:
                os.chdir(path_raw_windowing)
                new_filename = cropped_filename + str(counter).zfill(2) + ".csv"
                print(">>>>", new_filename)
                with open(new_filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(component)
                counter = counter + 1


#crop_size = 80000, window_size = 20000, interval = 4000
def write_features_windowing(crop_size, window_size, interval):
    for filename in os.listdir(path_raw):
        if filename.endswith(".csv"):
            os.chdir(path_raw)
            f = open(filename)
            original_matrix = Utility.read_csv(f)
            rotated_matrix = rotate_raw_data(original_matrix)
            cropped_matrix = crop_data(rotated_matrix, crop_size)
            components_list = data_windowing(cropped_matrix, window_size, interval)
            
            cropped_filename = os.path.splitext(filename)[0][0:7] + "_"
            counter = 0
            for component in components_list:
                
                wavelet_analysed_component = wavelet_analyse(component)
                
                #(MAV + WL + WAMP + Skew)
                features_component_1 = extract_features_1(component)
                #Wavelet(MAV + RMS)
                features_component_2 = extract_features_2(wavelet_analysed_component)
                
                #Do the normalization
                norm_component_1 = []
                features_component_1 = np.array(features_component_1)
                for i in range(len(features_component_1[0])):
                    norm_array_1 = keras.utils.normalize(features_component_1[:,i]).flatten()
                    norm_component_1.append(norm_array_1)
                
                norm_component_2 = []
                features_component_2 = np.array(features_component_2)
                for i in range(len(features_component_2[0])):
                    norm_array_2 = keras.utils.normalize(features_component_2[:,i]).flatten()
                    norm_component_2.append(norm_array_2)
            
                features_list_1 = np.array(norm_component_1).flatten()
                features_list_2 = np.array(norm_component_2).flatten()
                
                features_list = [np.concatenate((features_list_1, features_list_2))]
                
                os.chdir(path_features_windowing)
                new_filename = cropped_filename + str(counter).zfill(2) + ".csv"
                print(">>>>", new_filename)
                with open(new_filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(features_list)
                    #writer.writerows([features_list_1])
                    #writer.writerows([features_list_2])
                
                    counter = counter + 1






#write_raw_windowing(20000, 4000, 1000)
write_features_windowing(80000, 20000, 4000)
