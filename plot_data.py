import sys, os
import csv
import plotly.graph_objects as go

class PlotData:
    def __init__(self, folderpath):
        self.file = None
        self.folder_path = folderpath
        self.string_to_match = ['pre_test', 'training_1', 'mid_test', 'training_2', 'post_test']
        self.negative_key = '_settings.tdt'
        self.key_id = 0
        self.start_time = 0.0
        self.end_time = 0.0
        self.target_count = 0

        self.time_taken = []
        self.target_id = []
    
    def start(self):
        fig1 = go.Figure()
        fig2 = go.Figure()

        for filename in os.listdir(self.folder_path):
            self.key_id = 0
            for key_string in self.string_to_match:
                if (key_string in filename) and (self.negative_key not in filename):
                    print("processing file: {}".format(filename))
                    self.file = open(self.folder_path + '/' + filename, newline='')
                    lines = csv.reader(self.file, delimiter='\t')
                    time_taken = 0.0
                    for line in lines:
                        if self.start_time == 0.0:
                            self.start_time = float(line[0])
                        if line[10] == '1':
                            self.end_time = float(line[0])
                            self.target_count = self.target_count + 1
                            time_taken = self.end_time - self.start_time
                            print("{}: {} - {} = {}".format(self.target_count, self.end_time, self.start_time, time_taken))
                            self.time_taken.append(time_taken)
                            self.target_id.append(self.target_count)
                            self.start_time = self.end_time

                    
                    # Tests
                    if self.key_id % 2 == 0:
                        fig1.add_trace(go.Scatter(x=self.target_id, y=self.time_taken, name=self.string_to_match[self.key_id]))
                    # Training
                    else:
                        fig2.add_trace(go.Scatter(x=self.target_id, y=self.time_taken, name=self.string_to_match[self.key_id]))
                    
                    self.file.close()
                    print("time_taken: {}, target_count: {}".format(self.time_taken, self.target_count))
                    self.target_id = []
                    self.time_taken = []
                    self.start_time = 0.0
                    self.target_count = 0
                
                self.key_id = self.key_id + 1

        fig1.update_layout(hovermode='x unified')
        fig2.update_layout(hovermode='x unified')
        fig1.show()
        fig2.show()
        return

if __name__ == "__main__":
    args = sys.argv
    plot = PlotData(args[1])
    plot.start()
