from math import sqrt
import numpy as np
from model import *
import torch
import copy
from scipy.ndimage import median_filter

class PIDParameters:  # parameters for PID controller
    def __init__(self, kp, ki, kd, lower, upper):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.lower = lower
        self.upper = upper

class PIDController:  # PID controller
    def __init__(self, parameters: PIDParameters):
        self.parameters = parameters
        self.error = 0
        self.last_error = 0
        self.sum_error = 0

    def calculate_output(self, reference, feedback):  # calculate control signal
        self.error = reference - feedback
        self.sum_error += self.error
        u = 1.0 * self.parameters.kp * self.error + self.parameters.ki * self.sum_error + self.parameters.kd * (self.error - self.last_error)
        if u < self.parameters.lower:
            u = self.parameters.lower
        elif u > self.parameters.upper:
            u = self.parameters.upper
        self.last_error = self.error
        return u

    def reset(self):  # reset error, sum of error & error of error
        self.error = 0
        self.last_error = 0
        self.sum_error = 0

class Planner:  # position planner for position controller
    def __init__(self, v, a):
        self.V = v
        self.a = a
        self.v = self.V
        self.start = 0
        self.end = 0
        self.s = 0
        self.t = 0
        self.cur = 0

    def reset(self):
        self.v = self.V
        self.start = 0
        self.end = 0
        self.s = 0
        self.t = 0
        self.cur = 0

    def set(self, start, end):
        self.start = start
        self.end = end
        self.s = abs(self.start - self.end)
        if 1.5*(self.v ** 2)/self.a > self.s:
            self.v = sqrt(self.s * self.a / 1.5)

    def get_pos_from_zero(self):
        if abs(self.v) < 0.001:
            return self.s
        if self.t < self.v / self.a:
            t = self.t
            x0 = 0
            dx = 0.5 * self.a * (t ** 2)
            x = x0 + dx
        elif self.t < self.s / self.v:
            t = self.t - (self.v / self.a)
            x0 = (self.v ** 2) / self.a / 2
            dx = self.v * t
            x = x0 + dx
        elif self.t < self.s / self.v + self.v / self.a:
            t = self.t - (self.s / self.v)
            x0 = self.s - (self.v ** 2) / self.a / 2
            dx = self.v * t - self.a * (t ** 2) / 2
            x = x0 + dx
        else:
            x = self.s
        return x

    def step(self, t):
        self.t = t
        dx = self.get_pos_from_zero()
        if self.start < self.end:
            x = self.start + dx
        elif self.start == self.end:
            x = self.end
        else:
            x = self.start - dx
        return x

class CraneController:  # total control framework
    def __init__(self, v, a, pos_para, angle_para):
        # parameters
        self.v = v
        self.a = a
        self.pos_para = pos_para
        self.angle_para = angle_para

        # controllers & planners
        self.planner = Planner(self.v, self.a)
        self.pos_controller = PIDController(self.pos_para)
        self.angle_controller = PIDController(self.angle_para)

    def reset(self):
        self.pos_controller.reset()
        self.angle_controller.reset()
        self.planner.reset()

    def set(self, start, end):
        self.planner.set(start, end)

    def step(self, t, x_fdb, theta_fdb):
        x_ref = self.planner.step(t)
        u_pos = self.pos_controller.calculate_output(x_ref, x_fdb)
        u_angle = self.angle_controller.calculate_output(0, theta_fdb)
        u = u_pos - u_angle
        u = min(self.v, max(-self.v, u))
        return u, u_pos, u_angle, x_ref
        
class Predictor: # linear predictor
    def __init__(self, buffer_size=3):
        self.buffer_size = buffer_size
        self.buffer = [[0 for i in range(buffer_size)] for j in range(2)]
        self.counter = 0
        
    def update(self, new_x, new_y):
        self.buffer[0][self.counter] = new_x
        self.buffer[1][self.counter] = new_y
        self.counter = (self.counter + 1) % self.buffer_size
        
    def fit(self):
        X = np.array(self.buffer[0])
        Y = np.array(self.buffer[1])
        a1 = np.sum(X*X)
        a2 = np.sum(X)
        a3 = np.sum(X*Y)
        a4 = np.sum(X)
        a5 = self.buffer_size
        a6 = np.sum(Y)
        k = (a3*a5 - a2*a6) / (a1*a5 - a2*a4)
        b = (a1*a6 - a3*a4) / (a1*a5 - a2*a4)
        return k, b
    
    def predict(self, new_x, new_y, dx):
        self.update(new_x, new_y)
        if 0 in self.buffer[0]:
            return new_y
        k, b = self.fit()
        x = new_x + dx
        y_pred = k * x + b
        return y_pred

class DLPredictor: # deep learning predictor
    def __init__(self, weight_path) -> None:
        self.max_size = 60
        self.buffer = []
        self.lstm = LSTM(1, 50, 2, 40, 'cuda')
        self.lstm.load_state_dict(torch.load(weight_path))
        self.lstm.eval()
        self.lstm.to('cuda')
        
    def moving_average(self):
        filtered_signal = np.convolve(np.array(self.buffer), np.ones(5)/5, 'same')
        return filtered_signal
    
    def predict(self, x, if_smooth=False):
        if len(self.buffer) < self.max_size:
            self.buffer.append(x)
        else:
            self.buffer = copy.deepcopy(self.buffer[1:]) + [x]
        if len(self.buffer) < self.max_size:
            return x
        else:
            if if_smooth:
                signal = self.moving_average()[20:]
            else:
                signal = median_filter(np.array(self.buffer), 20)[20:]
            x = torch.Tensor(signal).unsqueeze(0).unsqueeze(2).to('cuda')
            y = np.array(self.lstm(x).squeeze(0).detach().cpu())[-1]
            return y
    
    def predict_max(self, x, if_smooth=False, offset = 0):
        if len(self.buffer) < self.max_size:
            self.buffer.append(x)
        else:
            self.buffer = copy.deepcopy(self.buffer[1:]) + [x]
        if len(self.buffer) < self.max_size:
            return x
        else:
            if if_smooth:
                signal = self.moving_average()[20:]
            else:
                signal = median_filter(np.array(self.buffer), 20)[20:]
            x = torch.Tensor(signal).unsqueeze(0).unsqueeze(2).to('cuda')
            y = np.array(self.lstm(x).squeeze(0).detach().cpu())[30:]
            y -= offset
            return np.max(np.abs(y))

class FastPlanner:  # velocity planner for open loop fast move
    def __init__(self, V, l, start, end):
        self.V = V
        self.T = 2*np.pi*sqrt(l/9.81)
        self.a = self.V / self.T
        self.start = start
        self.end = end
        self.s = abs(start-end)
        if (self.V**2) / self.a > self.s:
            self.a = self.s / (self.T**2)
            self.V = self.a * self.T

    def step(self, t):
        if t < self.V / self.a:
            dt = t
            v0 = 0
            dv = self.a * dt
            v = v0 + dv   
        elif t < self.s / self.V:
            v = self.V
        elif t < self.s / self.V + self.V / self.a:
            dt = t - (self.s / self.V)
            v0 = self.V
            dv = -self.a * dt
            v = v0 + dv
        else:
            v = 0.0
        if self.start > self.end:
            v = -v
        return v

class AverageFilter:
    def __init__(self, max_size):
        self.max_size = max_size
        self.buffer = []

    def append(self, x):
        if len(self.buffer) < self.max_size:
            self.buffer.append(x)
        else:
            self.buffer.append(x)
            self.buffer = self.buffer[1:]

    def get_value(self, x):
        self.append(x)
        data = np.array(self.buffer)
        return np.mean(data)

def cal_iou(bbox1, bbox2):
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2
    x1_max = x1 + w1/2
    y1_max = y1 + h1/2
    x1_min = x1 - w1/2
    y1_min = y1 - h1/2
    x2_max = x2 + w2/2
    y2_max = y2 + h2/2
    x2_min = x2 - w2/2
    y2_min = y2 - h2/2
    xx1 = max(x1_min, x2_min)
    yy1 = max(y1_min, y2_min)
    xx2 = min(x1_max, x2_max)
    yy2 = min(y1_max, y2_max)
    s1 = w1 * h1
    s2 = w2 * h2
    inter_section = max(0, xx2-xx1) * max(0, yy2-yy1) 
    res = inter_section / (s1 + s2 - inter_section)
    return res

def cal_error_x(bbox1, bbox2):
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2
    return abs(x1-x2)

def theta_zero(h:float):
    hh = h ** 2
    p1 = 5.714538523808440e-05
    p2 = -0.001530077890320
    p3 = 0.014805181138780
    return p1 * hh + p2 * h + p3