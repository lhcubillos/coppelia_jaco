import sys, os
import csv
import plotly.graph_objects as go

class PlotData:
    def __init__(self, folderpath):
        self.file = None
        self.folder_path = folderpath
        self.patient_id = ['']
        self.string_to_match = ['pre_test', 'training_1_1', 'training_1_2', 'training_1_3', 'training_1_4', 'mid_test', 
        'training_2_1', 'training_2_2', 'training_2_3', 'training_2_4', 'post_test']
        self.negative_key = '_settings.tdt'
        self.start_time = 0.0
        self.end_time = 0.0
        self.target_count = 0
        self.average = 0.0

        self.time_taken = []
        self.target_id = []
    
    def start(self):
        fig = go.Figure()

        
        for patient in self.patient_id:
            for key_string in self.string_to_match:
                for filename in os.listdir(self.folder_path + '/' + patient):
                    if (key_string in filename) and (self.negative_key not in filename):
                        print("processing file: {}".format(filename))
                        self.file = open(self.folder_path + '/' + patient + '/' + filename, newline='')
                        lines = csv.reader(self.file, delimiter='\t')
                        time_taken = 0.0
                        for line in lines:
                            if self.start_time == 0.0:
                                self.start_time = float(line[0])
                            if line[10] == '1':
                                self.end_time = float(line[0])
                                self.target_count = self.target_count + 1
                                time_taken = (self.end_time - self.start_time)
                                self.start_time = self.end_time
                                self.average += time_taken

                        self.average /= self.target_count
                        self.time_taken.append(self.average)
                        print("time_taken: {}, target_count: {}".format(self.average, self.target_count))
                        self.file.close()

                        self.start_time = 0.0
                        self.target_count = 0
                        self.average = 0.0

            fig.add_trace(go.Scatter(x=self.string_to_match, y=self.time_taken, name=patient))

        fig.update_layout(hovermode='x unified')
        fig.show()
        return

if __name__ == "__main__":
    args = sys.argv
    plot = PlotData(args[1])
    plot.start()
