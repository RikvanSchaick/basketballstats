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
        
    def adaptivethreshold(self, frame: np.array) -> np.array:
        frame = cv2.adaptiveThreshold(frame, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 19, 0)
        # frame = cv2.adaptiveThreshold(frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        return frame
    
    def digit(self, frame: np.array) -> int:
        frame = self.resize(frame, 4, 7)
        frame = np.where(frame <= 128, 0, 1)
        
        top = True if (np.sum(frame[0, 1:3])) == 0 else False
        top_left = True if (np.sum(frame[1:3, 0])) == 0 else False
        top_right = True if (np.sum(frame[1:3, 3])) == 0 else False
        middle = True if (np.sum(frame[3, 1:3])) == 0 else False
        bottom_left = True if (np.sum(frame[4:6, 0])) == 0 else False
        bottom_right = True if (np.sum(frame[4:6, 3])) == 0 else False
        bottom = True if (np.sum(frame[6, 1:3])) == 0 else False
           
        if top and top_left and top_right and middle and bottom_left and bottom_right and bottom:
            return 8
        elif top and top_left and top_right and middle and bottom_right and bottom:
            return 9
        elif top and top_left and middle and bottom_left and bottom_right and bottom:
            return 6
        elif top and top_left and top_right and bottom_left and bottom_right and bottom:
            return 0
        elif top and top_left and middle and bottom_right and bottom:
            return 5
        elif top and top_right and middle and bottom_right and bottom:
            return 3
        elif top and top_right and middle and bottom_left and bottom:
            return 2
        elif top_left and top_right and middle and bottom_right:
            return 4
        elif top and top_right and bottom_right:
            return 7
        elif top_right and bottom_right:
            return 1
        else:
            return " "
        
c = scoreboard()
# b, cap = c.open_video("test3")
b, cap = c.open_video("IMG_0879")
_, _, fps, _ = c.get_dimension()

i = 0
while(cap.isOpened()): 
    i+=1
    ret, frame = cap.read() 
    if ret == True: 
        
        # Preprocess individual frame
        gray = c.grayscaling(frame)
        black = c.adaptivethreshold(gray)
        
        # Extract time of scoreboard
        frame0,_,_ = c.crop(black, (91, 95), (114, 135))
        frame1,_,_ = c.crop(black, (119, 95), (142, 135))
        frame2,_,_ = c.crop(black, (161, 95), (184, 135))
        frame3,_,_ = c.crop(black, (191, 95), (214, 135))
        d0 = c.digit(frame0)
        d1 = c.digit(frame1)
        d2 = c.digit(frame2)
        d3 = c.digit(frame3)

        # Extract score of scoreboard
        frame4,_,_ = c.crop(black, (22, 79), (45, 119))
        frame5,_,_ = c.crop(black, (50, 79), (73, 119))
        frame6,_,_ = c.crop(black, (246, 79), (269, 119))
        frame7,_,_ = c.crop(black, (273, 79), (296, 119))
        d4 = c.digit(frame4)
        d5 = c.digit(frame5)
        d6 = c.digit(frame6)
        d7 = c.digit(frame7)        

        # Extract team fouls of scoreboard
        frame8,_,_ = c.crop(black, (17, 9), (40, 49))
        frame9,_,_ = c.crop(black, (45, 9), (68, 49))
        frame10,_,_ = c.crop(black, (238, 9), (261, 49))
        frame11,_,_ = c.crop(black, (266, 9), (289, 49))
        d8 = c.digit(frame8)
        d9 = c.digit(frame9)
        d10 = c.digit(frame10)
        d11 = c.digit(frame11)

        # Extract period of scoreboard
        frame12,_,_ = c.crop(black, (146, 6), (160, 26))
        d12 = c.digit(frame12)
        
        # Show original image
        c.show_frame(frame, 'Frame') 

        if i % int(fps/15) == 0 and i > 0:
            # print(f"Period:\t {d12}")            
            # print(f"Time: \t{d0}{d1}:{d2}{d3}")
            # print(f"Score: \t{d4}{d5}-{d6}{d7}")
            # print(f"Fouls: \t{d8}{d9}-{d10}{d11}")

            print(f"{d8}{d9}   {d12}   {d10}{d11}")
            print(f"{d4}{d5} {d0}{d1}:{d2}{d3} {d6}{d7}")
            print()
        
        if cv2.waitKey(25) & 0xFF == ord('q'): 
            break        
        
        if i == 200: 
            break
    else:
        break
c.close_video()
exit()
