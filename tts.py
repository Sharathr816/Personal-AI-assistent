
import queue
import re
import threading

import sounddevice as sd
from piper import PiperVoice
import emoji


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

# https://piperhub.org/voices/ -> Various voice
VOICE_PATH = "voices/Amy_model.onnx"


def clean_for_tts(text):
    text = emoji.replace_emoji(text, replace="")
    return text.strip()


class MioTTS:

    def __init__(self):
        print("[TTS] Loading Piper...")

        self.voice = PiperVoice.load(VOICE_PATH)

        self.audio_queue = queue.Queue()
        self.text_buffer = ""

        self.lock = threading.Lock()
        self.worker = None

        self.pending_sentences = []

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

                        if output_stream is None:
                            output_stream = sd.RawOutputStream(
                                samplerate=chunk.sample_rate,
                                channels=chunk.sample_channels,
                                dtype="int16",
                                device=None
                            )

                            output_stream.start()

                        output_stream.write(
                            chunk.audio_int16_bytes
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
