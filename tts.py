
import queue
import re
import threading

import sounddevice as sd
from piper import PiperVoice
import emoji

import struct

from avatar.vmc_controller import VMCController #Lip sync


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

# https://piperhub.org/voices/ -> Various voice
VOICE_PATH = "voices/Amy_model.onnx"


def clean_for_tts(text):
    text = emoji.replace_emoji(text, replace="")
    return text.strip()


class MioTTS:

    def __init__(self, vmc):
        print("[TTS] Loading Piper...")

        self.voice = PiperVoice.load(VOICE_PATH)

        self.audio_queue = queue.Queue()
        self.text_buffer = ""

        self.lock = threading.Lock()
        self.worker = None

        self.pending_sentences = []

        # Reuse the avatar's VMC connection
        self.vmc = vmc

        # Lip-sync configuration
        self.lip_sync_enabled = vmc is not None
        self.lip_sync_fps = 25

        print("[TTS] Mio's voice is ready!")

    # --------------------------------------------------------
    # Start background audio worker
    # --------------------------------------------------------

    def start(self):
        if self.worker and self.worker.is_alive():
            return

        self.worker = threading.Thread(
            target=self._audio_worker,
            daemon=True
        )

        self.worker.start()


    # -------------------------------------------------------------
    # Lip synchronization
    # -------------------------------------------------------------
    def _set_mouth(self, value):
        """
        Send mouth-opening intensity to Mio through VMC.
        """

        if not self.lip_sync_enabled:
            return

        # Keep the blendshape intensity within its valid range
        value = max(0.0, min(1.0, float(value)))

        # Send the VRM vowel A blendshape
        self.vmc.send_message(
            "/VMC/Ext/Blend/Val",
            "A",
            value
        )

        # Apply the updated facial blendshape
        self.vmc.send_message(
            "/VMC/Ext/Blend/Apply"
        )


    def _process_audio_for_lipsync(
        self, audio_bytes, sample_rate, channels, output_stream
    ):
        """
        Analyse and play audio in small frames while moving Mio's mouth.
        """

        if not self.lip_sync_enabled:
            output_stream.write(audio_bytes)
            return

        # Calculate samples and bytes per frame
        samples_per_frame = max(1, sample_rate // self.lip_sync_fps)
        bytes_per_frame = samples_per_frame * channels * 2

        # Process audio approximately 40 milliseconds at a time
        for offset in range(0, len(audio_bytes), bytes_per_frame):

            frame = audio_bytes[offset:offset + bytes_per_frame]

            # Ensure the frame contains complete int16 samples
            frame = frame[:len(frame) - (len(frame) % 2)]

            if not frame:
                continue

            # Decode the raw audio samples
            samples = [
                sample[0]
                for sample in struct.iter_unpack("<h", frame)
            ]

            # Calculate RMS amplitude
            rms = (
                sum(sample * sample for sample in samples)
                / len(samples)
            ) ** 0.5

            # Convert amplitude into mouth-opening intensity
            intensity = (rms - 500) / 7000
            intensity = max(0.0, min(1.0, intensity))

            # Update Mio's mouth before playing this audio frame
            self._set_mouth(intensity)

            # Play the corresponding audio frame
            output_stream.write(frame)
    # --------------------------------------------------------
    # Receive streamed LLM text
    # --------------------------------------------------------

    def feed(self, token):
        with self.lock:
            self.text_buffer += token

            while True:
                match = re.search(
                    r'[.!?](?:["\']|[\)\]]|(?=\s|$))',
                    self.text_buffer
                )

                if not match:
                    break

                end = match.end()
                sentence = self.text_buffer[:end].strip()
                self.text_buffer = self.text_buffer[end:].lstrip()

                if sentence:
                    self.pending_sentences.append(sentence)

                word_count = sum(
                    len(sentence.split())
                    for sentence in self.pending_sentences
                )

                # Generate after 2 sentences or 25 words
                if len(self.pending_sentences) >= 2 or word_count >= 25:
                    phrase = " ".join(self.pending_sentences)

                    self.audio_queue.put(phrase)
                    self.pending_sentences.clear()

    # --------------------------------------------------------
    # Flush remaining text after LLM completes
    # --------------------------------------------------------

    def flush(self):
        with self.lock:
            remaining = self.text_buffer.strip()

            if remaining:
                self.pending_sentences.append(remaining)

            self.text_buffer = ""

            if self.pending_sentences:
                phrase = " ".join(self.pending_sentences)

                self.audio_queue.put(phrase)
                self.pending_sentences.clear()

    # --------------------------------------------------------
    # Background synthesis and playback
    # --------------------------------------------------------

    def _audio_worker(self):
        output_stream = None
        try:
            while True:
                text = self.audio_queue.get()

                try:
                    if text is not None:
                        text = clean_for_tts(text)

                    if text is None:
                        return

                    for chunk in self.voice.synthesize(text):
                        # Close Mio's mouth after the phrase finishes playing
                        self._set_mouth(0.0)

                        if output_stream is None:
                            output_stream = sd.RawOutputStream(
                                samplerate=chunk.sample_rate,
                                channels=chunk.sample_channels,
                                dtype="int16",
                                device=None
                            )

                            output_stream.start()

                        # Analyse and play audio while synchronizing Mio's mouth
                        self._process_audio_for_lipsync(
                            audio_bytes=chunk.audio_int16_bytes,
                            sample_rate=chunk.sample_rate,
                            channels=chunk.sample_channels,
                            output_stream=output_stream
                            )

                finally:
                    self.audio_queue.task_done()

        finally:
            if output_stream is not None:
                output_stream.stop()
                output_stream.close()

    # --------------------------------------------------------
    # Wait until all speech is played
    # --------------------------------------------------------

    def wait(self):
        self.audio_queue.join()

    # --------------------------------------------------------
    # Shutdown
    # --------------------------------------------------------

    def stop(self):
        self.audio_queue.put(None)

        if self.worker:
            self.worker.join(timeout=10)
