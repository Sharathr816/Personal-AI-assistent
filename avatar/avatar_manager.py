
import queue
import threading
import traceback

from avatar.vmc_controller import VMCController
from avatar.expressions import ExpressionController
from avatar.movements import MovementController
from avatar.body import BodyController


class AvatarManager:
    """
    Central manager for all Mio avatar controllers.

    Responsibilities:
    - Coordinate expressions, movements, gestures and body animations.
    - Execute animation commands in a background worker.
    - Prevent idle animation from conflicting with other body animations.
    - Manage safe shutdown.
    """

    def __init__(self, vmc=None):
        # Reuse an existing VMC connection when provided.
        self.vmc = vmc or VMCController()

        # Initialize all avatar controllers with the same connection.
        self.expressions = ExpressionController(self.vmc)
        self.movements = MovementController(self.vmc)
        self.body = BodyController(self.vmc)

        # Queue for animation commands.
        self.action_queue = queue.Queue()

        # Track manager state.
        self.running = True
        self.idle_thread = None

        # Background worker for sequential animation execution.
        self.worker = threading.Thread(
            target=self._animation_worker,
            daemon=True
        )
        self.worker.start()

    # -----------------------------------------------------
    # Background animation worker.
    # -----------------------------------------------------
    def _animation_worker(self):
        while True:
            action = self.action_queue.get()

            try:
                if action is None:
                    return

                function, args, kwargs = action
                function(*args, **kwargs)

            except Exception:
                traceback.print_exc()

            finally:
                self.action_queue.task_done()

    # -----------------------------------------------------
    # Queue an animation action.
    # Stop idle animation before queuing body-related actions.
    # -----------------------------------------------------
    def _queue_action(self, function, *args, **kwargs):
        if not self.running:
            raise RuntimeError("AvatarManager has been shut down.")

        self.stop_idle()

        self.action_queue.put(
            (function, args, kwargs)
        )

    # -----------------------------------------------------
    # Stop idle animation and wait for its thread to finish.
    # -----------------------------------------------------
    def stop_idle(self):
        if self.idle_thread and self.idle_thread.is_alive():
            self.body.stop_idle()
            self.idle_thread.join()

        self.idle_thread = None

    # -----------------------------------------------------
    # Start continuous idle animation.
    # Wait for queued actions to finish first.
    # -----------------------------------------------------
    def start_idle(self, intensity=1.0):
        if not self.running:
            raise RuntimeError("AvatarManager has been shut down.")

        if self.idle_thread and self.idle_thread.is_alive():
            return

        # Finish pending actions before starting idle.
        self.action_queue.join()

        self.idle_thread = threading.Thread(
            target=self.body.idle,
            kwargs={"intensity": intensity},
            daemon=True
        )

        self.idle_thread.start()

    # =====================================================
    # FACIAL EXPRESSIONS
    # =====================================================

    def set_expression(self, emotion="neutral", intensity=1.0,
                       duration=0.3):
        self._queue_action(
            self.expressions.expression,
            emotion,
            intensity,
            duration
        )

    def blink(self, duration=0.15):
        self._queue_action(
            self.expressions.blink,
            duration
        )

    def reset_expression(self, duration=0.3):
        self._queue_action(
            self.expressions.reset,
            duration
        )

    # =====================================================
    # HEAD AND EYE MOVEMENTS
    # =====================================================

    def nod(self, intensity=15, duration=0.5):
        self._queue_action(
            self.movements.head_nod,
            intensity,
            duration
        )

    def shake_head(self, intensity=20, duration=0.6):
        self._queue_action(
            self.movements.head_shake,
            intensity,
            duration
        )

    def tilt_head(self, direction="left", intensity=12,
                  duration=0.3):
        self._queue_action(
            self.movements.head_tilt,
            direction,
            intensity,
            duration
        )

    def look_at(self, direction="forward", duration=0.2):
        self._queue_action(
            self.movements.look_at,
            direction,
            duration
        )

    def reset_head(self, duration=0.3):
        self._queue_action(
            self.movements.reset_head,
            duration
        )

    def reset_gaze(self, duration=0.2):
        self._queue_action(
            self.movements.reset_gaze,
            duration
        )



    # =====================================================
    # BODY ANIMATIONS
    # =====================================================

    def happy_reaction(self, duration=0.5):
        self._queue_action(
            self.body.happy_reaction,
            duration
        )

    def sad_reaction(self, duration=0.5):
        self._queue_action(
            self.body.sad_reaction,
            duration
        )

    def surprised_reaction(self, duration=0.3):
        self._queue_action(
            self.body.surprised_reaction,
            duration
        )

    def breathing(self, duration=3.0, intensity=1.0):
        self._queue_action(
            self.body.breathing,
            duration,
            intensity
        )

    def sway(self, duration=4.0, intensity=1.0):
        self._queue_action(
            self.body.sway,
            duration,
            intensity
        )

    def relax_shoulders(self, duration=0.4):
        self._queue_action(
            self.body.relax_shoulders,
            duration
        )

    def reset_body(self, duration=0.5):
        self._queue_action(
            self.body.reset,
            duration
        )

    # =====================================================
    # GENERAL CONTROL
    # =====================================================

    def wait(self):
        """Wait until all queued animations finish."""
        self.action_queue.join()

    def close(self):
        """Stop animations and release manager resources."""
        if not self.running:
            return

        # Stop idle animation.
        self.stop_idle()

        # Finish any remaining queued animations.
        self.action_queue.join()

        # Stop the worker.
        self.running = False
        self.action_queue.put(None)
        self.worker.join()

        print("[Avatar] AvatarManager stopped.")

    def close_vmc(self):
        """
        Close the VMC connection.

        Call this only when no other component, such as TTS,
        is still using the shared VMC connection.
        """
        self.vmc.close()
