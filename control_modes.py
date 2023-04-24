import tkinter as tk

class ControlModesUI:
    FREQUENCY = 10
    def __init__(self):
        self.fig = None
        self.window = None
        self.reverse = False
        self.custom_frame = None
        self.tolerance = 0.1
        self.current_state = 1
        self.num_modes = 4
        self.prev_vel = [0.0, 0.0, 0.0]

    def init_process(self):
        self.window = tk.Tk()
        self.window.title('Control Modes')
        self.window.geometry('500x500')

        self.custom_frame = tk.Frame(master=self.window)

        self.button1 = tk.Button(self.custom_frame,text='X',bg='green',height=2,width=50)
        self.button2 = tk.Button(self.custom_frame,text='Y',bg='red',height=2,width=50)
        self.button3 = tk.Button(self.custom_frame,text='Z',bg='red',height=2,width=50)

        self.button4 = tk.Button(self.custom_frame,text='rotate',bg='red',height=2,width=50)
        self.button5 = tk.Button(self.custom_frame,text='open/close',bg='red',height=2,width=50)

        self.button1.pack()
        self.button2.pack()
        self.button3.pack()
        self.button4.pack()
        self.button5.pack()

        self.custom_frame.pack(expand=True)
    
    def update_velocity(self, vel):
        if (abs(self.prev_vel[2]) <= self.tolerance) and (self.prev_vel[2] != vel[2]):
            if vel[2] < -self.tolerance:
                self.current_state = (self.current_state + 1) % self.num_modes
                if self.current_state == 0:
                        self.current_state = self.num_modes
            else:
                if vel[2] > self.tolerance:
                    self.current_state = (self.current_state - 1) % self.num_modes
                    if self.current_state == 0:
                        self.current_state = self.num_modes
        self.prev_vel = vel
        if self.current_state == 1:
            return [vel[0], 0.0, 0.0]
        if self.current_state == 2:
            return [0.0, 0.0, vel[0]]
        if self.current_state == 3:
            return [0.0, vel[0], 0.0]
        if self.current_state == 4:
            return [0.0, 0.0, vel[0] * 10]
        return [0.0, 0.0, 0.0]

    def update_color(self):
        self.button1.configure(bg = "red")
        self.button2.configure(bg = "red")
        self.button3.configure(bg = "red")
        self.button4.configure(bg = "red")
        self.button5.configure(bg = "red")
        if self.current_state == 1:
            self.button1.configure(bg = "green")
        if self.current_state == 2:
            self.button2.configure(bg = "green")
        if self.current_state == 3:
            self.button3.configure(bg = "green")
        if self.current_state == 4:
            self.button4.configure(bg = "green")
        if self.current_state == 5:
            self.button5.configure(bg = "green")