
import math
import time

from avatar.vrm_bind_pose import BIND_POSE


class BodyController:
    """
    Controls Mio's upper-body animations.

    Supports:
    - Idle breathing
    - Gentle body sway
    - Shoulder movement
    - Happy, sad and surprised reactions
    - Smooth transitions

    Bust spring bones are deliberately not controlled here.
    Their secondary motion should be handled by VRM physics.
    """

    def __init__(self, vmc, fps=30):
        self.vmc = vmc
        self.fps = fps

        # Body bones and their original local positions.
        self.body_positions = {
            "Spine": (0.0, 0.0492954254, -0.0117317792),
            "Chest": (0.0, 0.105305076, -0.00291390531),
            "UpperChest": (0.0, 0.100226164, 0.0136309415),
            "Neck": (0.0, 0.122595906, 0.0355460346),
            "LeftShoulder": (-0.0196415056, 0.09794295, 0.02777318),
            "RightShoulder": (0.0196415056, 0.09794295, 0.02777318),
        }

        self.current_pose = {
            bone: (0.0, 0.0, 0.0)
            for bone in self.body_positions
        }

        self.idle_running = False

    # -----------------------------------------------------
    # Euler angles to quaternion.
    # -----------------------------------------------------
    @staticmethod
    def _to_quaternion(x, y, z):
        x, y, z = (
            math.radians(x) / 2,
            math.radians(y) / 2,
            math.radians(z) / 2
        )

        cx, sx = math.cos(x), math.sin(x)
        cy, sy = math.cos(y), math.sin(y)
        cz, sz = math.cos(z), math.sin(z)

        return (
            sx * cy * cz - cx * sy * sz,
            cx * sy * cz + sx * cy * sz,
            cx * cy * sz - sx * sy * cz,
            cx * cy * cz + sx * sy * sz
        )

    # -----------------------------------------------------
    # Send a body bone rotation while preserving position.
    # -----------------------------------------------------
    def _send_bone(self, bone, rotation):
        position = self.body_positions[bone]
        qx, qy, qz, qw = self._to_quaternion(*rotation)

        self.vmc.send_message(
            "/VMC/Ext/Bone/Pos",
            bone,
            *position,
            qx, qy, qz, qw
        )

    # -----------------------------------------------------
    # Smoothly transition between body poses.
    # -----------------------------------------------------
    def _animate(self, target_pose, duration=0.4):
        if duration < 0:
            raise ValueError("Duration cannot be negative.")

        steps = max(1, int(duration * self.fps))

        start_pose = {
            bone: self.current_pose[bone]
            for bone in target_pose
        }

        for step in range(1, steps + 1):
            progress = step / steps

            for bone, target in target_pose.items():
                start = start_pose[bone]

                rotation = tuple(
                    old + (new - old) * progress
                    for old, new in zip(start, target)
                )

                self._send_bone(bone, rotation)

            if step < steps:
                time.sleep(1 / self.fps)

        self.current_pose.update(target_pose)

    # -----------------------------------------------------
    # Idle breathing.
    # -----------------------------------------------------
    def breathing(self, duration=3.0, intensity=1.0):
        """
        A subtle breathing cycle.

        The chest expands and relaxes through small rotations.
        """

        if duration <= 0:
            raise ValueError("Duration must be positive.")

        if not 0 <= intensity <= 1:
            raise ValueError("Intensity must be between 0 and 1.")

        steps = max(1, int(duration * self.fps))

        for step in range(steps):
            phase = 2 * math.pi * step / steps

            breath = math.sin(phase)

            chest_pitch = -2.0 * breath * intensity
            upper_pitch = -1.0 * breath * intensity

            pose = {
                "Chest": (chest_pitch, 0, 0),
                "UpperChest": (upper_pitch, 0, 0),
            }

            for bone, rotation in pose.items():
                self._send_bone(bone, rotation)
                self.current_pose[bone] = rotation

            time.sleep(1 / self.fps)

    # -----------------------------------------------------
    # Gentle upper-body sway.
    # -----------------------------------------------------
    def sway(self, duration=4.0, intensity=1.0):
        if duration <= 0:
            raise ValueError("Duration must be positive.")

        steps = max(1, int(duration * self.fps))

        for step in range(steps):
            phase = 2 * math.pi * step / steps

            sway_angle = math.sin(phase) * 3.0 * intensity

            pose = {
                "Spine": (0, 0, sway_angle * 0.5),
                "Chest": (0, 0, sway_angle),
                "UpperChest": (0, 0, sway_angle * 0.7),
            }

            for bone, rotation in pose.items():
                self._send_bone(bone, rotation)
                self.current_pose[bone] = rotation

            time.sleep(1 / self.fps)

    # -----------------------------------------------------
    # Shoulder relaxation.
    # -----------------------------------------------------
    def relax_shoulders(self, duration=0.4):
        self._animate({
            "LeftShoulder": (0, 0, 3),
            "RightShoulder": (0, 0, -3),
        }, duration)

    # -----------------------------------------------------
    # Happy reaction.
    # -----------------------------------------------------
    def happy_reaction(self, duration=0.5):
        self._animate({
            "Spine": (-3, 0, 0),
            "Chest": (-5, 0, 0),
            "UpperChest": (-3, 0, 0),
            "LeftShoulder": (0, 0, 5),
            "RightShoulder": (0, 0, -5),
        }, duration)

    # -----------------------------------------------------
    # Sad reaction.
    # -----------------------------------------------------
    def sad_reaction(self, duration=0.5):
        self._animate({
            "Spine": (5, 0, 0),
            "Chest": (7, 0, 0),
            "UpperChest": (4, 0, 0),
            "LeftShoulder": (0, 0, -5),
            "RightShoulder": (0, 0, 5),
        }, duration)

    # -----------------------------------------------------
    # Surprised reaction.
    # -----------------------------------------------------
    def surprised_reaction(self, duration=0.3):
        self._animate({
            "Spine": (-2, 0, 0),
            "Chest": (-8, 0, 0),
            "UpperChest": (-6, 0, 0),
            "LeftShoulder": (0, 0, 10),
            "RightShoulder": (0, 0, -10),
        }, duration)

    # -----------------------------------------------------
    # Return the body to neutral.
    # -----------------------------------------------------
    def reset(self, duration=0.5):
        self._animate({
            bone: (0, 0, 0)
            for bone in self.body_positions
        }, duration)

    # -----------------------------------------------------
    # Continuous idle animation.
    # -----------------------------------------------------
    def idle(self, duration=None, intensity=0.6):
        """
        Run continuous breathing and gentle swaying.

        duration=None means run until stop_idle() is called.
        """

        if self.idle_running:
            return

        self.idle_running = True
        start_time = time.monotonic()
        step = 0

        try:
            while self.idle_running:
                elapsed = time.monotonic() - start_time

                if duration is not None and elapsed >= duration:
                    break

                # Slow breathing cycle.
                breath = math.sin(2 * math.pi * elapsed / 3.5)

                # Gentle body sway.
                sway = math.sin(2 * math.pi * elapsed / 6.0)

                # Gentle, slow head nod.
                head_nod = math.sin(2 * math.pi * elapsed / 5.0) * 2.0 * intensity

                pose = {
                    # "Spine": (0, 0, sway * 0.1 * intensity),
                    "Chest": (-breath * 1.5 * intensity, 0,
                              sway * 0.3 * intensity),
                    "UpperChest": (-breath * 1.0 * intensity, 0,
                                   sway * 0.1 * intensity),
                    "Neck": (head_nod, 0, 0),
                }

                for bone, rotation in pose.items():
                    self._send_bone(bone, rotation)
                    self.current_pose[bone] = rotation

                step += 1
                time.sleep(1 / self.fps)

        finally:
            self.idle_running = False
            self.reset()

    def stop_idle(self):
        self.idle_running = False
