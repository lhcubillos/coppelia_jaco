import sys, os
import csv
import plotly.graph_objects as go
import math

class PlotData:
    def __init__(self, folderpath):
        self.file = None
        self.folder_path = folderpath
        self.patient_id = ['Patient/DC013123', 'Patient/WL020223', 'Patient/SH020323', 'Patient/CR020923', 'Patient/NJ020923', 'Patient/MG021323', 'Patient/BW021423', 'Patient/DD021723', 'Patient/JP030223']
        '''  self.patient_id = ['Healthy/TN120622', 'Healthy/SO120622', 'Healthy/SO120722', 'Healthy/TA120722', 'Healthy/AS121222', 'Healthy/HZ121222', 'Healthy/AG121222', 'Healthy/TN121222', 'Healthy/MC121422', 'Healthy/JM121422', "Healthy/KR121422", "Healthy/RA122022", "Healthy/SR122022", "Healthy/LC122022", "Healthy/YC122122", "Healthy/MR122222", "Healthy/KR122222", "Healthy/EE011023", "Healthy/AM011023", "Healthy/M111111", "Healthy/A111111", "Healthy/N111111", "Healthy/S111111", "Healthy/Q111111"]'''
        
        
        """self.patient_id = ["Healthy/RA122022", "Healthy/SR122022", "Healthy/LC122022", "Healthy/YC122122", "Healthy/MR122222", "Healthy/KR122222"]
        self.patient_id = ['Healthy/TN120622', 'Healthy/SO120622', 'Healthy/SO120722', 'Healthy/TA120722', 'Healthy/AS121222', 'Healthy/HZ121222', 'Healthy/AG121222', 'Healthy/TN121222', 'Healthy/MC121422', 'Healthy/JM121422', "Healthy/KR121422", "Healthy/RA122022", "Healthy/SR122022", "Healthy/LC122022", "Healthy/M111111", "Healthy/A111111", "Healthy/N111111", "Healthy/S111111", "Healthy/Q111111"]"""
        self.string_to_match = ['pre_test', 'training_1_1', 'training_1_2', 'training_1_3', 'training_1_4', 'mid_test', 
        'training_2_1', 'training_2_2', 'training_2_3', 'training_2_4', 'post_test']
        self.negative_key = '_settings.tdt'
        # time
        self.start_time = 0.0
        self.end_time = 0.0
        self.target_count = 0
        self.average = 0.0
        self.time_taken = []
        self.target_id = []
        # path
        self.start_point = (0.0, 0.0, 0.0)
        self.prev_point = (0.0, 0.0, 0.0)
        self.short_distance = 0.0
        self.distance = 0.0
        self.target_reached = 1
        self.normalized_dist_avg = 0.0
        self.avg_path = []
        self.header = ['patient'] + self.string_to_match
        self.time_data_csv = open(folderpath + '/2d_time_data.csv', 'w')
        self.time_data_csv_writer = csv.writer(self.time_data_csv)
        self.time_data_csv_writer.writerow(self.header)
        self.path_data_csv = open(folderpath + '/2d_path_data.csv', 'w')
        self.path_data_csv_writer = csv.writer(self.path_data_csv)
        self.path_data_csv_writer.writerow(self.header)
    
    def start(self):
        fig_time = go.Figure()
        fig_path = go.Figure()

        print("Test Name (X-axis) | Average Time for test (Y-axis - Fig1) | Average normalized path (Y-axis - Fig2) | Total Targets")
        print("--------------------------------------------------------------------------------")
        for patient in self.patient_id:
            print("\nPATIENT ID: {}".format(patient))
            print("-------------------------------------------------------")
            for key_string in self.string_to_match:
                for filename in os.listdir(self.folder_path + patient):
                    if (key_string in filename) and (self.negative_key not in filename):
                        self.file = open(self.folder_path + '/' + patient + '/' + filename, newline='')
                        lines = csv.reader(self.file, delimiter='\t')
                        # time
                        self.start_time = 0.0
                        self.end_time = 0.0
                        self.target_count = 0
                        self.average = 0.0
                        time_taken = 0.0
                        # path
                        self.start_point = (0.0, 0.0, 0.0)
                        self.prev_point = (0.0, 0.0, 0.0)
                        self.short_distance = 0.0
                        self.distance = 0.0
                        self.target_reached = 1
                        self.normalized_dist_avg = 0.0

                        for line in lines:
                            # path
                            if self.target_reached == 1:
                                self.start_point = (float(line[1]), float(line[2]), float(line[3]))
                                self.distance = 0.0
                                self.prev_point = (float(line[1]), float(line[2]), float(line[3]))
                                self.target_reached = 0
                            # time
                            if self.start_time == 0.0:
                                self.start_time = float(line[0])
                            # path
                            current_point = (float(line[1]), float(line[2]), float(line[3]))
                            self.distance += math.dist(self.prev_point, current_point)
                            self.prev_point = current_point

                            if line[10] == '1':
                                # time
                                self.end_time = float(line[0])
                                self.target_count = self.target_count + 1
                                time_taken = (self.end_time - self.start_time)
                                self.start_time = self.end_time
                                self.average += time_taken
                                # path
                                self.short_distance = math.dist(self.start_point, current_point)
                                if self.short_distance == 0.0:
                                    self.short_distance = 1.0
                                self.normalized_dist_avg += self.distance/self.short_distance
                                self.target_reached = 1
                        # time
                        self.average /= self.target_count
                        self.time_taken.append(self.average)
                        # path
                        self.normalized_dist_avg /= self.target_count
                        self.avg_path.append(self.normalized_dist_avg)

                        print("{}\t| {}\t| {}\t| {}".format(key_string, self.average, self.normalized_dist_avg, self.target_count))
                        self.file.close()
                        # time
                        self.start_time = 0.0
                        self.target_count = 0
                        # path
                        self.average = 0.0
                        self.normalized_dist_avg =0.0
            # time
            fig_time.add_trace(go.Scatter(x=self.string_to_match, y=self.time_taken, name=patient+"_time"))
            self.time_data_csv_writer.writerow([patient] + list(map(str, self.time_taken)))
            self.time_taken = []
            # path
            fig_path.add_trace(go.Scatter(x=self.string_to_match, y=self.avg_path, name=patient+"_path"))
            self.path_data_csv_writer.writerow([patient] + list(map(str, self.avg_path)))
            self.avg_path = []

        self.time_data_csv.close()
        self.path_data_csv.close()
        # time
        fig_time.update_layout(yaxis_title="Movement Time", hovermode='x unified')
        fig_time.show()
        # path
        fig_path.update_layout(yaxis_title="Normalized Path Length", hovermode='x unified')
        fig_path.show()
        return

if __name__ == "__main__":
    args = sys.argv
    plot = PlotData(args[1])
    plot.start()
