
# Original local bone positions extracted from Mio0.0.vrm.
# VMC uses Unity HumanBodyBones names.

BIND_POSE = {
    # Arms
    "LeftUpperArm": (-0.0620329157, -0.009327292, 0.0),
    "LeftLowerArm": (-0.187500417, 0.0, 0.0),
    "LeftHand": (-0.1714049, 0.0000022649765, -0.000317297876),

    "RightUpperArm": (0.0620329157, -0.009327292, 0.0),
    "RightLowerArm": (0.187500417, 0.0, 0.0),
    "RightHand": (0.1714049, 0.0000022649765, -0.000317297876),
}


# Finger bone positions.
# Each finger has three joints.

FINGER_POSITIONS = {
    "LeftThumbProximal": (-0.00285896659, -0.008078694, -0.0137510225),
    "LeftThumbIntermediate": (-0.02869907, -0.00166487694, -0.02606855),
    "LeftThumbDistal": (-0.0182665586, -0.000789642334, -0.0152523331),

    "LeftIndexProximal": (-0.0531264544, 0.005957246, -0.0169325769),
    "LeftIndexIntermediate": (-0.0269857347, 0.0, 0.0005566552),
    "LeftIndexDistal": (-0.0165992975, -0.000477314, 0.000650078058),

    "LeftMiddleProximal": (-0.0538501143, 0.005957365, -0.00176329166),
    "LeftMiddleIntermediate": (-0.0300647318, 0.0, 0.0),
    "LeftMiddleDistal": (-0.0185474157, 0.0, 0.0),

    "LeftRingProximal": (-0.0532368124, 0.005957246, 0.011704959),
    "LeftRingIntermediate": (-0.0278886557, 0.0, 0.0),
    "LeftRingDistal": (-0.016094625, 0.0, 0.0),

    "LeftLittleProximal": (-0.0495711565, 0.005957246, 0.025132291),
    "LeftLittleIntermediate": (-0.0255098641, 0.0, 0.0),
    "LeftLittleDistal": (-0.01470232, 0.0, 0.0),

    "RightThumbProximal": (0.00285896659, -0.008078694, -0.0137510225),
    "RightThumbIntermediate": (0.02869907, -0.00166487694, -0.02606855),
    "RightThumbDistal": (0.0182665586, -0.000789642334, -0.0152523331),

    "RightIndexProximal": (0.0531264544, 0.005957246, -0.0169325769),
    "RightIndexIntermediate": (0.0269857347, 0.0, 0.0005566552),
    "RightIndexDistal": (0.0165992975, -0.000477314, 0.000650078058),

    "RightMiddleProximal": (0.0538501143, 0.005957365, -0.00176329166),
    "RightMiddleIntermediate": (0.0300647318, 0.0, 0.0),
    "RightMiddleDistal": (0.0185474157, 0.0, 0.0),

    "RightRingProximal": (0.0532368124, 0.005957246, 0.011704959),
    "RightRingIntermediate": (0.0278886557, 0.0, 0.0),
    "RightRingDistal": (0.016094625, 0.0, 0.0),

    "RightLittleProximal": (0.0495711565, 0.005957246, 0.025132291),
    "RightLittleIntermediate": (0.0255098641, 0.0, 0.0),
    "RightLittleDistal": (0.01470232, 0.0, 0.0),
}

BIND_POSE.update(FINGER_POSITIONS)

# All these original rotations are identity quaternions.
BIND_ROTATIONS = {
    bone: (0.0, 0.0, 0.0, 1.0)
    for bone in BIND_POSE
}
