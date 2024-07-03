import cv2 
import numpy as np

class scoreboard():
    def __init__(self) -> None:
        self.capture = None

    def open_video(self, name: str) -> {bool, cv2.VideoCapture}:
        self.capture = cv2.VideoCapture(f'video/{name}.mov')
        if (self.capture.isOpened()== False):  
            return False, None
        if (self.capture.isOpened()):            
            return True, self.capture

    def close_video(self) -> None:
        self.capture.release() 
        cv2.destroyAllWindows()
        
    def get_dimension(self) -> {int, int, int, int}:
        width  = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.capture.get(cv2.CAP_PROP_FPS))
        frame_count = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
        return width, height, fps, frame_count
    
    def resize(self, frame: np.array, width: int, height: int) -> np.array:
        frame = cv2.resize(frame, (width, height), fx = 0, fy = 0, interpolation = cv2.INTER_CUBIC)
        return frame

    def grayscaling(self, frame: np.array) -> np.array:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame
    
    def show_frame(self, frame: np.array, name: str) -> None:
        cv2.imshow(name, frame) 
        
    def crop(self, frame: np.array, upleft: tuple, bottomright: tuple) -> {np.array, int, int}:
        frame = frame[upleft[1]:bottomright[1], upleft[0]:bottomright[0]]
        width = bottomright[1] - upleft[1]
        height = bottomright[0] - upleft[0]
        return frame, width, height
        
    def adaptivethreshold(self, frame: np.array):
        frame = cv2.adaptiveThreshold(frame, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        # frame = cv2.adaptiveThreshold(frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        return frame
    
c = scoreboard()
# b, cap = c.open_video("test")
b, cap = c.open_video("IMG_0879")
# width, height, fps, frame_count = c.get_dimension()
# print(f'width: {width}, height: {height}')
# print(f'fps: {fps}')
# print(f'frames count: {frame_count}')
while(cap.isOpened()): 
    ret, frame = cap.read() 
    if ret == True: 
        frame,_,_ = c.crop(frame, (90, 95), (215, 135))
        c.show_frame(frame, 'Frame') 
        frame = c.resize(frame, 40, 16)
        frame = c.grayscaling(frame)
        frame = c.adaptivethreshold(frame)
        frame0,_,_ = c.crop(frame, (0, 0), (7, 16))
        frame1,_,_ = c.crop(frame, (9, 0), (16, 16))
        frame2,_,_ = c.crop(frame, (23, 0), (30, 16))
        frame3,_,_ = c.crop(frame, (32, 0), (39, 16))
        c.show_frame(frame0, 'Frame0') 
        c.show_frame(frame1, 'Frame1') 
        c.show_frame(frame2, 'Frame2') 
        c.show_frame(frame3, 'Frame3') 
        if cv2.waitKey(25) & 0xFF == ord('q'): 
            break        
    else:
        break
c.close_video()
exit()
