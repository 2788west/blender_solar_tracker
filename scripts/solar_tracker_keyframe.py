import math
import datetime
import bpy
import cv2
import numpy as np
from PIL import Image


class SolarSystem:
    """
    The solar system class, consisting of tilt and rotation adjustment as well
    as the sensor functionality. 
    """
    def __init__(self):
        # Panel parameters
        self.tilt = 0
        self.rotation = 0
        self.step = 1  # Movement step in degrees
        self.iteration_time = 0.1
        self.impossible_move = False
        self.dir_x = None
        self.dir_y = None

        # Reset the panel orientation when initiated
        bpy.data.objects['motor_tilt'].rotation_euler[1] = math.radians(self.tilt)
        bpy.data.objects['motor_rotate'].rotation_euler[2] = math.radians(self.rotation)

        # Sensor parameters
        self.data = None
        self.gray = None
        self.image = None
        self.res_x = 512
        self.res_y = 512
        self.center = self.res_x // 2
        self.t = 32  # tolerance value for centering the sun

        # Blender scene render settings
        self.scene = bpy.data.scenes["Scene"]
        self.scene.render.engine = 'BLENDER_EEVEE'
        self.scene.render.resolution_x = self.res_x
        self.scene.render.resolution_y = self.res_y

        # Keyframe parameters
        self.frame_no = 0
        self.frame_step = 5

    def iterate(self):
        """
        Main driver function that moves the solar panel. This function gets called
        from the external loop to adjust the solar panel.
        """
        direction = self._find_bright_spot()
        self.dir_x = direction[0]
        self.dir_y = direction[1]

        if self.dir_x == "CENTER" and self.dir_y == "CENTER":
            # Base case--we've reached goal orientation
            return

        if self.dir_x == "RIGHT":
            self._decrease_rotation()
        if self.dir_x == "LEFT":
            self._increase_rotation()
        if self.dir_y == "DOWN":
            self._decrease_tilt()
        if self.dir_y == "UP":
            self._increase_tilt()

            # Generate keyframes
            self.frame_no += self.frame_step
            bpy.data.objects['motor_tilt'].keyframe_insert(
                data_path="rotation_euler",
                index=1,
                frame=self.frame_no
            )
            bpy.data.objects['motor_rotate'].keyframe_insert(
                data_path="rotation_euler",
                index=2,
                frame=self.frame_no
            )

    def _update_sensor(self):
        """
        Function to update the camera image, convert it to an array, and save
        it to disk.
        """
        # Render image and get pixels
        self.scene.view_layers["ViewLayer"].update()  # Ensure the view layer is up-to-date
        bpy.context.scene.frame_set(self.frame_no)  # Make sure we're on the current frame
        bpy.ops.render.render(write_still=True)
        pixels = bpy.data.images['Viewer Node'].pixels

        # Get the dimensions of the image
        width = bpy.data.images['Viewer Node'].size[0]
        height = bpy.data.images['Viewer Node'].size[1]

        # Convert the pixels to a 1D NumPy array, then reshape and convert to 8-bit integer
        np_pixels = np.array(pixels)  # This creates a flat array
        np_pixels = np.clip(np_pixels * 255, 0, 255).astype(np.uint8)  # Convert to [0, 255] range
        np_pixels = np_pixels.reshape((height, width, 4))  # Reshape to (height, width, RGBA)
        np_pixels = np.flipud(np_pixels)

        self.data = np_pixels

        # Create an image using Pillow and save it
        path = "C:/Users/johan/Desktop/SolarTracker/view/"
        filename = path + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".png"
        img = Image.fromarray(np_pixels, 'RGBA')
        img.save(filename)

    def _find_bright_spot(self):
        """
        Function to find the sun in the camera image. This function creates the move command.
        """
        self._update_sensor()  # Get a new image before trying to find the bright spot
        self.image = cv2.cvtColor(self.data, cv2.COLOR_RGBA2BGR)
        self.gray = cv2.cvtColor(self.data, cv2.COLOR_RGBA2GRAY)
        (_, _, _, max_loc) = cv2.minMaxLoc(self.gray)
        cv2.circle(self.image, max_loc, 5, (255, 0, 255), 1)
        cv2.line(self.image, (self.center, 0), (self.center, self.res_x), (255, 0, 255), 1)
        cv2.line(self.image, (0, self.center), (self.res_x, self.center), (255, 0, 255), 1)

        # Create an image using Pillow and save it
        path = "C:/Users/johan/Desktop/SolarTracker/cv/"
        filename = path + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".png"
        cv2.imwrite(filename, self.image)

        # Produce the move command according to the sun's location in the image
        if max_loc[0] >= self.center:
            dir_x = "RIGHT"
        else:
            dir_x = "LEFT"
        if max_loc[1] >= self.center:
            dir_y = "DOWN"
        else:
            dir_y = "UP"

        if self.center - self.t < max_loc[0] < self.center + self.t:
            dir_x = "CENTER"

        if self.center - self.t < max_loc[1] < self.center + self.t:
            dir_y = "CENTER"

        return (dir_x, dir_y)

    def _increase_tilt(self):
        self.tilt += self.step
        if self.tilt > 90:
            self.impossible_move = True
        else:
            bpy.data.objects['motor_tilt'].rotation_euler[1] = math.radians(self.tilt)

    def _decrease_tilt(self):
        self.tilt -= self.step
        if self.tilt < 0:
            self.impossible_move = True
        else:
            bpy.data.objects['motor_tilt'].rotation_euler[1] = math.radians(self.tilt)

    def _increase_rotation(self):
        self.rotation += self.step
        bpy.data.objects['motor_rotate'].rotation_euler[2] = math.radians(self.rotation)

    def _decrease_rotation(self):
        self.rotation -= self.step
        bpy.data.objects['motor_rotate'].rotation_euler[2] = math.radians(self.rotation)


if __name__ == "__main__":
    ss = SolarSystem()

    for i in range(50):
        # If the sun was animated in the scene, then this should be an infinite loop
        print(i)
        ss.iterate()
