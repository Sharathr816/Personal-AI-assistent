import re
import time
import conversation_manager

# import sounddevice as sd
# from audio_config import INPUT_DEVICE, OUTPUT_DEVICE

# sd.default.device = (INPUT_DEVICE, OUTPUT_DEVICE)

# I set the default output device of windows as Nirvana space/truke earbuds, defaulting input device messes the earbuds sound quality

import stt
from tts import MioTTS


def main():
    print("\n==============================")
    print("       MIO VOICE SYSTEM")
    print("==============================\n")

    # Initialize TTS once.
    tts = MioTTS()
    tts.start() 

    # Warm up your existing Qwen model.
    conversation_manager.warmup()

    print("\nMio is ready! Speak to start.")
    print("Say 'goodbye Mio' to exit.\n")

    try:
        while True:

            # ----------------------------------------
            # 1. Listen
            # ----------------------------------------
            audio = stt.listen() # raw audio data

            # ----------------------------------------
            # 2. Transcribe
            # ----------------------------------------
            user_text = stt.transcribe(audio)

            if not user_text:
                print("[STT] Nothing recognized.")
                continue

            print(f"\nYou: {user_text}")

            # Normalize transcription - so that exit commands work
            normalized = re.sub(r"[^\w\s]", "", user_text.lower())
            normalized = " ".join(normalized.split())

            exit_commands = {
                "goodbye mio",
                "exit mio",
                "stop mio",
                "bye mio",
                "quit mio",
                "shutdown mio",
                "see you later mio"
            }

            if normalized in exit_commands:
                tts.feed("Goodbye! my friend")
                tts.flush()
                tts.wait()
                break

            # ----------------------------------------
            # 3. convo_manager -> LLM -> TTS
            # ----------------------------------------

            start = time.perf_counter()

            # Processing to find memory relevant stuffs to store/retrive
            conversation_manager.process_message(
                user_text,
                on_chunk=tts.feed
            )

            # Flush incomplete final sentence.
            tts.flush()

            # Wait until Mio finishes speaking.
            tts.wait()
            elapsed = time.perf_counter() - start

            print(
                f"\n[VOICE] Response completed in {elapsed:.2f}s"
            )

    except KeyboardInterrupt:
        print("\n[VOICE] Stopping...")

    finally:
        tts.stop()
        print("Mio offline.")


if __name__ == "__main__":
    main()
