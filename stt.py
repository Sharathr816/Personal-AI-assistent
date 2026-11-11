from collections import deque

import numpy as np
import sounddevice as sd
import webrtcvad

# To reduce uneccesary noise in input voice
import noisereduce as nr

from faster_whisper import WhisperModel


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

SAMPLE_RATE = 16000 # common sampling rate for speech recognition
FRAME_MS = 20 # each frame represents 20 milliseconds of audio.

FRAME_SAMPLES = int(
    SAMPLE_RATE * FRAME_MS / 1000
)

SILENCE_DURATION = 0.6
PRE_ROLL_DURATION = 0.3

MIN_SPEECH_DURATION = 0.35

LANGUAGE = "en"

# Reject empty or low-energy recordings
def has_speech_energy(audio, threshold=0.008):
    rms = np.sqrt(np.mean(audio ** 2))
    return rms >= threshold


# ------------------------------------------------------------
# INITIALIZE MODELS
# ------------------------------------------------------------

print("[STT] Loading Whisper...")

whisper = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8",
    cpu_threads=4
)

# detects silence frames and audio frames
vad = webrtcvad.Vad(2) # 2 = agressiveness - Higher aggressiveness means the detector is more likely to reject sounds as non-speech.
'''Frame = a small block of audio.
Sample rate = how many audio measurements happen per second.
Pre-roll = a small history of audio kept before speech detection, 
so the beginning of your words isn't clipped.'''
print("[STT] Ready!")


# ------------------------------------------------------------
# Audio preprocessing - for more clearer voice
# ------------------------------------------------------------
def preprocess_audio(audio):
    # Noise reduction
    audio = nr.reduce_noise(
        y=audio,
        sr=SAMPLE_RATE,
        stationary=False,
        prop_decrease=0.90,
        time_mask_smooth_ms=100,
        freq_mask_smooth_hz=200
    )

    # Volume normalization
    rms = np.sqrt(np.mean(audio ** 2) + 1e-10)

    target_rms = 0.16
    gain = min(target_rms / rms, 8.0)

    audio *= gain

    # Prevent clipping
    peak = np.max(np.abs(audio))
    if peak > 0.95:
        audio *= 0.95 / peak

    return audio


# ------------------------------------------------------------
# MICROPHONE + VAD
# ------------------------------------------------------------

def listen():
    print("\n[MIC] Listening...")

    pre_roll = deque(
        maxlen=int(
            PRE_ROLL_DURATION * 1000 / FRAME_MS
        )
    )

    audio_frames = []

    speaking = False
    silence_frames = 0

    required_silence = int(
        SILENCE_DURATION * 1000 / FRAME_MS
    )

    '''we want raw audio bytes instead of SoundDevice 
    automatically creating a NumPy array for every microphone read.'''
    with sd.RawInputStream( 
        samplerate=SAMPLE_RATE, # Capture 16,000 samples per second
        blocksize=FRAME_SAMPLES, # 	Return 320 samples per read
        channels=1, # 	Mono audio
        dtype="int16",
        device=None
    ) as stream:

        while True:
            '''This retrieves the next audio frame.
            data contains the captured audio.
            overflowed indicates whether the input buffer overflowed, 
            meaning the application failed to consume audio quickly enough.
            We skip that frame if overflow occurs.'''
            data, overflowed = stream.read(FRAME_SAMPLES)

            if overflowed:
                continue
             
            frame = bytes(data)
            
            is_speech = vad.is_speech(
                frame,
                SAMPLE_RATE
            )
            '''vad.is_speech() returns a Boolean:
                    True   # Speech detected
                    False  # Non-speech detected'''

            if not speaking:
                pre_roll.append(frame)

                if is_speech:
                    speaking = True
                    audio_frames.extend(pre_roll)
                    silence_frames = 0
                    # print("[MIC] Speech detected...")

            else:
                audio_frames.append(frame)

                if is_speech:
                    silence_frames = 0
                else:
                    silence_frames += 1

                '''We join all collected frames into one continuous byte sequence.
                This is done after a certain time of silence'''
                if silence_frames >= required_silence:
                    duration = (
                        len(audio_frames) * FRAME_MS / 1000
                    )

                    if duration >= MIN_SPEECH_DURATION:
                        # print("[MIC] Speech ended.")
                        return b"".join(audio_frames)

                    # Discard noise or very short speech.
                    speaking = False
                    audio_frames.clear()
                    pre_roll.clear()
                    silence_frames = 0


# ------------------------------------------------------------
# WHISPER TRANSCRIPTION
# ------------------------------------------------------------

def transcribe(audio_bytes):
    audio = np.frombuffer( #v Converts the raw bytes into a NumPy array of 16-bit integers.
        audio_bytes,
        dtype=np.int16 #Converts those integer samples into floating-point numbers.
    ).astype(np.float32) / 32768.0 # Normalizes the audio amplitude into approximately the range -1 to +1.

    # print("[STT] Transcribing...")

    # Audio preprocessing for clarity
    audio = preprocess_audio(audio)

    if not has_speech_energy(audio):
        return ""

    '''language="en": Tell Whisper to recognize English.
        beam_size=1: Use greedy-style decoding for faster inference.
        condition_on_previous_text=False: Don't use previous transcription 
            text as context for the next transcription.
        vad_filter=False: Don't apply another VAD filter inside Whisper because 
            we already segmented the audio ourselves.'''
    segments, info = whisper.transcribe(
        audio,
        language="en",
        beam_size=5, # Whisper explores more candidate sequences(Sentences) before selecting one
        initial_prompt="Mio - My personal AI assistent.",
        condition_on_previous_text=False,
        vad_filter=False,

        # To remove uneccesary segments of whisper when no audio input given
        no_speech_threshold=0.6,
        log_prob_threshold=-1.0,
        compression_ratio_threshold=2.4
    )

    ignored_phrases = {
    "Mio - My personal AI assistent."
    }
    # faster-whisper returns a lazy generator.
    text = []
    for segment in segments:
        sentence = segment.text.strip()
        if segment.no_speech_prob >= 0.6:
            continue
        if sentence.lower() in ignored_phrases:
            continue
        text.append(sentence)
    return " ".join(text).strip()
