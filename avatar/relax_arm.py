
import socket
import struct
import math
import time

HOST = "127.0.0.1"
PORT = 39539

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def osc_string(value):
    data = value.encode("ascii") + b"\0"
    return data + b"\0" * ((4 - len(data) % 4) % 4)


def send_bone(name, position, rotation):
    rx, ry, rz = map(math.radians, rotation)

    cx, sx = math.cos(rx / 2), math.sin(rx / 2)
    cy, sy = math.cos(ry / 2), math.sin(ry / 2)
    cz, sz = math.cos(rz / 2), math.sin(rz / 2)

    qx = sx * cy * cz - cx * sy * sz
    qy = cx * sy * cz + sx * cy * sz
    qz = cx * cy * sz - sx * sy * cz
    qw = cx * cy * cz + sx * sy * sz

    packet = (
        osc_string("/VMC/Ext/Bone/Pos")
        + osc_string(name)
        + struct.pack(
            ">7f",
            *position,
            qx, qy, qz, qw
        )
    )

    sock.sendto(packet, (HOST, PORT))


# Original positions extracted from your VRM.
# Rotate upper arms downward from the T-pose.

bones = [
    ("LeftShoulder",  (-0.0196415, 0.09794295, 0.02777318), (0, 0, 0)),
    ("RightShoulder", (0.0196415, 0.09794295, 0.02777318), (0, 0, 0)),

    ("LeftUpperArm",  (-0.0857828, -0.0128983, 0), (0, 0, 90)),
    ("RightUpperArm", (0.0857828, -0.0128983, 0), (0, 0, -90)),

    ("LeftLowerArm",  (-0.1875004, 0, 0), (0, 0, 0)),
    ("RightLowerArm", (0.1875004, 0, 0), (0, 0, 0)),

    ("LeftHand",  (-0.1714048, 0.0000023, -0.0003173), (0, 0, 0)),
    ("RightHand", (0.1714048, 0.0000023, -0.0003173), (0, 0, 0)),
]

print("Sending relaxed arm pose...")

for name, position, rotation in bones:
    send_bone(name, position, rotation)
    time.sleep(0.02)

time.sleep(0.2)
sock.close()

print("Commands sent.")
