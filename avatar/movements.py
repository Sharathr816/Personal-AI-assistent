
import math
import time


class MovementController:

    def __init__(self, vmc):

        # Reuse the existing VMC connection
        self.vmc = vmc

        # Store the last commanded head rotation
        self.head_rotation = (0.0, 0.0, 0.0)

        # Store the last commanded eye rotations
        self.left_eye_rotation = (0.0, 0.0, 0.0)
        self.right_eye_rotation = (0.0, 0.0, 0.0)

    def _to_quaternion(self, pitch, yaw, roll):
        """
        Convert Euler angles in degrees into a quaternion.
        """

        # Convert degrees into radians
        pitch = math.radians(pitch) / 2
        yaw = math.radians(yaw) / 2
        roll = math.radians(roll) / 2

        # Calculate quaternion components
        cx = math.cos(pitch)
        sx = math.sin(pitch)

        cy = math.cos(yaw)
        sy = math.sin(yaw)

        cz = math.cos(roll)
        sz = math.sin(roll)

        qw = cx * cy * cz + sx * sy * sz
        qx = sx * cy * cz - cx * sy * sz
        qy = cx * sy * cz + sx * cy * sz
        qz = cx * cy * sz - sx * sy * cz

        return qx, qy, qz, qw

    def _send_bone_rotation(self, bone, rotation):
        """
        Send a rotation command for a humanoid bone.
        """

        # Convert the requested Euler rotation into a quaternion
        qx, qy, qz, qw = self._to_quaternion(*rotation)

        # Send bone position and rotation through VMC
        self.vmc.send_message(
            "/VMC/Ext/Bone/Pos",
            bone,
            0.0, 0.0, 0.0,
            qx, qy, qz, qw
        )

    def _interpolate(self, start, target, duration=0.3):
        """
        Smoothly transition between two rotations.
        """

        # Calculate the number of updates at approximately 30 FPS
        steps = max(1, int(duration * 30))

        for step in range(1, steps + 1):

            # Calculate transition progress
            progress = step / steps

            # Interpolate each rotation component
            current = tuple(
                s + (t - s) * progress
                for s, t in zip(start, target)
            )

            yield current

            # Maintain the approximate update frequency
            if step < steps:
                time.sleep(1 / 30)

    def rotate_head(self, pitch=0, yaw=0, roll=0, duration=0.3):
        """
        Rotate Mio's head.
        Pitch: up/down
        Yaw: left/right
        Roll: tilt
        """

        # Define the requested target rotation
        target = (pitch, yaw, roll)

        # Smoothly move from the previous rotation
        for rotation in self._interpolate(
            self.head_rotation,
            target,
            duration
        ):
            self._send_bone_rotation("Head", rotation)

        # Save the final commanded rotation
        self.head_rotation = target

    def head_nod(self, intensity=15, duration=0.5):
        """
        Nod Mio's head up and down.
        """

        # Move head down
        self.rotate_head(
            pitch=intensity,
            duration=duration / 2
        )

        # Return to neutral
        self.rotate_head(
            pitch=0,
            duration=duration / 2
        )

    def head_shake(self, intensity=20, duration=0.6):
        """
        Shake Mio's head left and right.
        """

        # Turn left
        self.rotate_head(
            yaw=-intensity,
            duration=duration / 3
        )

        # Turn right
        self.rotate_head(
            yaw=intensity,
            duration=duration / 3
        )

        # Return to neutral
        self.rotate_head(
            yaw=0,
            duration=duration / 3
        )

    def head_tilt(self, direction="left", intensity=12, duration=0.3):
        """
        Tilt Mio's head toward one shoulder.
        """

        # Determine tilt direction
        if direction == "left":
            roll = -intensity
        elif direction == "right":
            roll = intensity
        else:
            raise ValueError("Direction must be left or right.")

        # Apply the tilt
        self.rotate_head(
            roll=roll,
            duration=duration
        )

    def reset_head(self, duration=0.3):
        """
        Return Mio's head to its neutral rotation.
        """

        self.rotate_head(
            pitch=0,
            yaw=0,
            roll=0,
            duration=duration
        )

    def rotate_eyes(self, yaw=0, pitch=0, duration=0.2):
        """
        Move both eyes in the same direction.
        """

        # Calculate the target eye rotation
        target = (pitch, yaw, 0)

        # Smoothly interpolate both eyes
        for rotation in self._interpolate(
            self.left_eye_rotation,
            target,
            duration
        ):

            # Apply rotation to the left eye
            self._send_bone_rotation("LeftEye", rotation)

            # Apply rotation to the right eye
            self._send_bone_rotation("RightEye", rotation)

        # Save the final eye rotations
        self.left_eye_rotation = target
        self.right_eye_rotation = target

    def look_at(self, direction="forward", duration=0.2):
        """
        Move Mio's gaze in a predefined direction.
        """

        # Define simple gaze directions
        directions = {
            "left": (0, -15),
            "right": (0, 15),
            "up": (-10, 0),
            "down": (10, 0),
            "forward": (0, 0)
        }

        # Validate the requested direction
        if direction not in directions:
            raise ValueError("Unsupported gaze direction.")

        pitch, yaw = directions[direction]

        # Apply the eye rotation
        self.rotate_eyes(
            yaw=yaw,
            pitch=pitch,
            duration=duration
        )

    def reset_gaze(self, duration=0.2):
        """
        Return Mio's eyes to their forward position.
        """

        self.look_at(
            direction="forward",
            duration=duration
        )
