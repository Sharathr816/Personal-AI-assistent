
import time

# Import the UDP/OSC communication controller from Phase 1
from avatar.vmc_controller import VMCController


class ExpressionController:

    # Map human-readable emotions to VRM 0.x blendshape presets
    EXPRESSIONS = {
        "happy": "Joy",
        "sad": "Sorrow",
        "angry": "Angry",
        "surprised": "Surprised",
    }

    def __init__(self, vmc: VMCController):

        # Reuse the existing VMC connection
        self.vmc = vmc

        # Store the current intensity of each expression preset
        self.current_values = {
            preset: 0.0
            for preset in self.EXPRESSIONS.values()
        }

        # Track the currently active expression
        self.current_expression = "neutral"

    def _send_values(self, values):
        """
        Send multiple blendshape values in one VMC update.
        """

        # Send each blendshape value to VSeeFace
        for preset, value in values.items():
            self.vmc.send_message(
                "/VMC/Ext/Blend/Val",
                preset,
                float(value)
            )

        # Apply all submitted blendshape values together
        self.vmc.send_message(
            "/VMC/Ext/Blend/Apply"
        )

    def expression(
        self,
        emotion="neutral",
        intensity=1.0,
        duration=0.3
    ):
        """
        Change Mio's facial expression with a smooth transition.
        """

        emotion = emotion.lower()

        # Validate the requested emotion
        if emotion not in self.EXPRESSIONS and emotion != "neutral":
            raise ValueError(
                f"Unsupported expression: {emotion}"
            )

        # Validate expression intensity
        if not 0.0 <= intensity <= 1.0:
            raise ValueError(
                "Intensity must be between 0 and 1."
            )

        # Prevent negative transition durations
        if duration < 0:
            raise ValueError(
                "Duration cannot be negative."
            )

        # Prepare the target values with all expressions disabled
        target_values = {
            preset: 0.0
            for preset in self.EXPRESSIONS.values()
        }

        # Activate the requested expression
        if emotion != "neutral":
            preset = self.EXPRESSIONS[emotion]
            target_values[preset] = intensity

        # Save the starting values for interpolation
        start_values = self.current_values.copy()

        # Calculate transition steps
        steps = max(1, int(duration * 30))

        # Gradually interpolate from the current to target expression
        for step in range(1, steps + 1):
            progress = step / steps
            interpolated_values = {}

            for preset in target_values:
                start = start_values[preset]
                target = target_values[preset]

                # Linear interpolation between the two intensities
                interpolated_values[preset] = (
                    start + (target - start) * progress
                )

            # Send the interpolated facial values
            self._send_values(interpolated_values)

            # Approximately 30 updates per second
            if step < steps:
                time.sleep(1 / 30)

        # Save the final expression state
        self.current_values = target_values.copy()
        self.current_expression = emotion

    def blink(self, duration=0.15):
        """
        Perform a single blink without changing the active emotion.
        """

        if duration <= 0:
            raise ValueError(
                "Blink duration must be positive."
            )

        # Split the blink into closing and opening movements
        half_duration = duration / 2
        steps = max(1, int(half_duration * 30))

        # Gradually close both eyes
        for step in range(1, steps + 1):
            progress = step / steps
            self.vmc.send_message(
                "/VMC/Ext/Blend/Val",
                "Blink",
                float(progress)
            )

            self.vmc.send_message(
                "/VMC/Ext/Blend/Apply"
            )

            if step < steps:
                time.sleep(half_duration / steps)

        # Gradually reopen both eyes
        for step in range(1, steps + 1):
            progress = 1.0 - (step / steps)
            self.vmc.send_message(
                "/VMC/Ext/Blend/Val",
                "Blink",
                float(progress)
            )
            self.vmc.send_message(
                "/VMC/Ext/Blend/Apply"
            )

            if step < steps:
                time.sleep(half_duration / steps)

    def reset(self, duration=0.3):
        """
        Return Mio's facial expressions to neutral.
        """

        self.expression(
            emotion="neutral",
            duration=duration
        )
