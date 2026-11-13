import math
import socket

# Used to construct properly formatted OSC messages
from pythonosc.osc_message_builder import OscMessageBuilder


# Custom exception for VMC communication errors
class VMCConnectionError(Exception):
    pass


class VMCController:

    def __init__(self, host="127.0.0.1", port=39539):

        # VSeeFace receiver address and port
        self.host = host
        self.port = port

        # Create a UDP IPv4 socket for sending OSC packets
        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        # Track whether the socket has been closed
        self.closed = False

    def send_message(self, address, *args):
        """
        Construct an OSC message and send it to VSeeFace.
        """

        # Prevent sending messages through a closed socket
        if self.closed:
            raise VMCConnectionError("VMC socket is closed.")

        # OSC addresses must begin with '/'
        if not address.startswith("/"):
            raise ValueError("OSC address must start with '/'.")

        try:
            # Create an OSC message builder for the given address
            builder = OscMessageBuilder(address=address)

            # Add each argument using its appropriate OSC data type
            for arg in args:
                builder.add_arg(arg)

            # Build the final binary OSC packet
            message = builder.build()

            # Send the packet to the configured VSeeFace UDP endpoint
            sent_bytes = self.socket.sendto(
                message.dgram,
                (self.host, self.port)
            )

            # Return the number of bytes accepted by the local socket
            return sent_bytes

        except (OSError, ValueError) as exc:

            # Convert low-level errors into a VMC-specific exception
            raise VMCConnectionError(
                f"Failed to send VMC message: {exc}"
            ) from exc

    def send_time(self, timestamp):
        """
        Send the sender timestamp using the VMC protocol.
        """

        # VMC uses /VMC/Ext/T to communicate sender time
        self.send_message(
            "/VMC/Ext/T",
            float(timestamp)
        )

    def send_blendshape(self, name, value):
        """
        Send a VRM 0.x blendshape value and apply it.
        """

        # Convert the supplied value into a floating-point number
        value = float(value)

        # Reject NaN and infinite values
        if not math.isfinite(value):
            raise ValueError("Blendshape value must be finite.")

        # VRM blendshape values must be between 0.0 and 1.0
        if not 0.0 <= value <= 1.0:
            raise ValueError(
                "Blendshape value must be between 0 and 1."
            )

        # Send the blendshape name and its corresponding value
        self.send_message(
            "/VMC/Ext/Blend/Val",
            name,
            value
        )

        # Tell VSeeFace to apply the updated blendshape values
        self.send_message(
            "/VMC/Ext/Blend/Apply"
        )

    def close(self):
        """
        Close the UDP socket and release its resources.
        """
        # Avoid closing the same socket multiple times
        if not self.closed:
            self.socket.close()
            self.closed = True

    def __enter__(self):
        # Allow VMCController to be used with Python's 'with' statement
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Automatically close the socket when leaving the 'with' block
        self.close()