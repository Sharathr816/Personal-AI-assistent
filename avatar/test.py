# import time

# # Import our VMC communication controller
# from avatar.vmc_controller import VMCController


# def main():

#     print("Starting VMC communication test...")

#     try:

#         # Initialize the controller and automatically close it afterward
#         with VMCController(
#             host="127.0.0.1",
#             port=39539
#         ) as vmc:

#             print("UDP socket initialized.")

#             # Send the Joy blendshape at maximum intensity
#             print("Sending Joy expression...")

#             vmc.send_blendshape(
#                 name="Joy",
#                 value=1.0
#             )

#             print("Joy message sent.")

#             # Keep the expression active for two seconds
#             time.sleep(2)

#             # Reset Joy to zero intensity
#             print("Resetting expression...")

#             vmc.send_blendshape(
#                 name="Joy",
#                 value=0.0
#             )

#             print("Reset message sent.")

#             print("VMC transmission test completed.")

#     except Exception as exc:

#         # Display any communication or execution errors
#         print(f"VMC test failed: {exc}")


# # Execute the test only when this file is run directly
# if __name__ == "__main__":
#     main()




# =============Expressions===============
# import time

# # Import the VMC communication controller
# from avatar.vmc_controller import VMCController

# # Import the facial expression controller
# from avatar.expressions import ExpressionController


# def main():

#     # Create one VMC connection for the entire test
#     with VMCController(
#         host="127.0.0.1",
#         port=39539
#     ) as vmc:

#         # Give the expression controller access to VMC
#         face = ExpressionController(vmc)

#         try:

#             #Test happy expression
#             print("Testing HAPPY...")
#             face.expression("happy", intensity=0.8)
#             time.sleep(2)

#             # Test sad expression
#             print("Testing SAD...")
#             face.expression("sad", intensity=0.8)
#             time.sleep(2)

#             # Test angry expression
#             print("Testing ANGRY...")
#             face.expression("angry", intensity=0.8)
#             time.sleep(2)

#             #Test surprised expression
#             print("Testing SURPRISED...")
#             face.expression("surprised", intensity=0.8)
#             time.sleep(5)

#             # Test relaxed/neutral expression
#             print("Testing NEUTRAL...")
#             face.expression("neutral")
#             time.sleep(1)

#             # Test blinking
#             print("Testing BLINK...")
#             face.blink()

#             # Reset all facial expressions
#             face.reset()
#             print("All expression tests completed.")

#         finally:

#             # Ensure Mio returns to neutral before closing
#             face.reset()


# if __name__ == "__main__":
#     main()


#=====================Head and eye movement=================
# import time

# from avatar.vmc_controller import VMCController
# from avatar.movements import MovementController


# def main():

#     # Create the shared VMC connection
#     with VMCController() as vmc:

#         # Initialize the movement controller
#         movement = MovementController(vmc)

#         # Test head nodding
#         print("Testing head nod...")
#         movement.head_nod()
#         time.sleep(1)

#         # Test head shaking
#         print("Testing head shake...")
#         movement.head_shake()
#         time.sleep(1)

#         # Test left head tilt
#         print("Testing left head tilt...")
#         movement.head_tilt("left")
#         time.sleep(1)

#         # Test right head tilt
#         print("Testing right head tilt...")
#         movement.head_tilt("right")
#         time.sleep(1)

#         # Reset head position
#         print("Resetting head...")
#         movement.reset_head()
#         time.sleep(1)

#         # Test looking left
#         print("Looking left...")
#         movement.look_at("left")
#         time.sleep(1)

#         # Test looking right
#         print("Looking right...")
#         movement.look_at("right")
#         time.sleep(1)

#         # Test looking up
#         print("Looking up...")
#         movement.look_at("up")
#         time.sleep(1)

#         # Test looking down
#         print("Looking down...")
#         movement.look_at("down")
#         time.sleep(1)
#         # Reset gaze
#         print("Resetting gaze...")
#         movement.reset_gaze()

#         print("Movement tests completed.")


# if __name__ == "__main__":
#     main()


#=====================hand gestures====================
# import time

# from avatar.vmc_controller import VMCController
# from avatar.gestures import GestureController


# def main():
#     vmc = VMCController(
#         host="127.0.0.1",
#         port=39539
#     )

#     gestures = GestureController(vmc)

#     try:
#         print("\n1. Original T-pose")
#         gestures.reset()
#         time.sleep(2)

#         print("\n2. Relaxed standing pose")
#         gestures.relaxed_pose()
#         time.sleep(2)

#         print("\n3. Raise right arm")
#         gestures.raise_arm("right")
#         time.sleep(2)

#         print("\n4. Lower right arm")
#         gestures.lower_arm("right")
#         time.sleep(2)

#         print("\n5. Raise left arm")
#         gestures.raise_arm("left")
#         time.sleep(2)

#         print("\n6. Lower left arm")
#         gestures.lower_arm("left")
#         time.sleep(2)

#         print("\n7. Open right hand")
#         gestures.hand_gesture("Right", "open")
#         time.sleep(2)

#         print("\n8. Relaxed right hand")
#         gestures.hand_gesture("Right", "relaxed")
#         time.sleep(2)

#         print("\n9. Right fist")
#         gestures.hand_gesture("Right", "fist")
#         time.sleep(2)

#         print("\n10. Left fist")
#         gestures.hand_gesture("Left", "fist")
#         time.sleep(2)

#         print("\n11. Right hand wave")
#         gestures.wave("right", cycles=2)
#         time.sleep(2)

#         print("\n12. Left hand wave")
#         gestures.wave("left", cycles=2)
#         time.sleep(2)

#         print("\n13. Point forward")
#         gestures.point("forward", "right")
#         time.sleep(2)

#         print("\n14. Point upward")
#         gestures.point("up", "right")
#         time.sleep(2)

#         print("\n15. Return to relaxed pose")
#         gestures.relaxed_pose()
#         time.sleep(2)

#         print("\nAll tests completed.")

#     finally:
#         vmc.close()


# if __name__ == "__main__":
#     main()



# =================Body animation=================

import time

from avatar.vmc_controller import VMCController
from avatar.body import BodyController


def main():
    vmc = VMCController(
        host="127.0.0.1",
        port=39539
    )

    body = BodyController(vmc)

    try:
        print("1. Testing breathing...")
        body.breathing(duration=10)
        time.sleep(1)

        print("2. Testing body sway...")
        body.sway(duration=5)
        time.sleep(1)

        print("3. Testing shoulder relaxation...")
        body.relax_shoulders()
        time.sleep(1)

        print("4. Testing happy reaction...")
        body.happy_reaction()
        time.sleep(1)

        print("5. Testing sad reaction...")
        body.sad_reaction()
        time.sleep(1)

        print("6. Testing surprised reaction...")
        body.surprised_reaction()
        time.sleep(1)

        print("7. Testing idle animation for 10 seconds...")
        body.idle(duration=10)

        print("8. Resetting body...")
        body.reset()

        print("All body tests completed!")

    finally:
        vmc.close()


if __name__ == "__main__":
    main()


# ==================Avatar manager=========================


import time

from avatar.avatar_manager import AvatarManager


def full():
    avatar = AvatarManager()

    try:
        print("1. Starting idle animation...")
        avatar.start_idle(intensity=0.7)
        time.sleep(5)

        print("2. Happy expression and reaction...")
        avatar.set_expression("happy", intensity=1.0)
        avatar.happy_reaction()
        avatar.wait()
        time.sleep(2)

        print("3. Head movement...")
        avatar.nod()
        avatar.wait()
        time.sleep(1)


        print("5. Sad reaction...")
        avatar.set_expression("sad")
        avatar.sad_reaction()
        avatar.wait()
        time.sleep(2)

        print("6. Return to neutral...")
        avatar.reset_expression()
        avatar.reset_body()
        avatar.reset_head()
        avatar.wait()

        print("7. Restart idle...")
        avatar.start_idle(intensity=0.5)
        time.sleep(5)

        print("8. Stopping idle...")
        avatar.stop_idle()

        print("All AvatarManager tests completed!")

    finally:
        avatar.close()
        avatar.close_vmc()


if __name__ == "__main__":
    full()

