import sys, os
import csv
import plotly.graph_objects as go
import math

class PlotData:
    def __init__(self, folderpath):
        self.file = None
        self.folder_path = folderpath
        self.patient_id = ['dn113022']
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
                        time_taken = 0.0

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
            self.time_taken = []
            # path
            fig_path.add_trace(go.Scatter(x=self.string_to_match, y=self.avg_path, name=patient+"_path"))
            self.avg_path = []
        # time
        fig_time.update_layout(hovermode='x unified')
        fig_time.show()
        # path
        fig_path.update_layout(hovermode='x unified')
        fig_path.show()
        return

if __name__ == "__main__":
    args = sys.argv
    plot = PlotData(args[1])
    plot.start()
