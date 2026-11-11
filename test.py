# import time

# first_token_time = None

# start_time = time.perf_counter()
# final_chunk = None # for metrics

# # inside if content: in llm.py
# if first_token_time is None:
#         first_token_time = time.perf_counter()
#         final_chunk = chunk
            
# end_time = time.perf_counter()


 # ---------------- PERFORMANCE METRICS ----------------
    # print("\n\n--- Performance ---")
    # if first_token_time:
    #     ttft = first_token_time - start_time
    #     print(f"Time to first token: {ttft:.2f}s")
    # print(f"Total response time: {end_time - start_time:.2f}s")
    # if final_chunk and final_chunk.eval_count:
    #     duration = final_chunk.eval_duration / 1e9
    #     if duration > 0:
    #         speed = final_chunk.eval_count / duration
    #         print(f"Generation speed: {speed:.2f} tokens/sec")
    # print("-------------------")



# test audio preprocessing
# import sounddevice as sd
# import numpy as np
# import noisereduce as nr
# import wave

# SAMPLE_RATE = 16000
# DURATION = 5


# def preprocess_audio(audio):
#     # Noise reduction
#     audio = nr.reduce_noise(
#         y=audio,
#         sr=SAMPLE_RATE,
#         stationary=False,
#         prop_decrease=0.90,
#         time_mask_smooth_ms=100,
#         freq_mask_smooth_hz=200
#     )

#     # Volume normalization
#     rms = np.sqrt(np.mean(audio ** 2) + 1e-10)

#     target_rms = 0.16
#     gain = min(target_rms / rms, 8.0)

#     audio *= gain

#     # Prevent clipping
#     peak = np.max(np.abs(audio))
#     if peak > 0.95:
#         audio *= 0.95 / peak

#     return audio


# def save_wav(filename, audio):
#     audio_int16 = np.clip(
#         audio * 32768, -32768, 32767
#     ).astype(np.int16)

#     with wave.open(filename, "wb") as wav:
#         wav.setnchannels(1)
#         wav.setsampwidth(2)
#         wav.setframerate(SAMPLE_RATE)
#         wav.writeframes(audio_int16.tobytes())


# print("Recording... Speak normally!")

# recording = sd.rec(
#     int(DURATION * SAMPLE_RATE),
#     samplerate=SAMPLE_RATE,
#     channels=1,
#     dtype="float32"
# )

# sd.wait()

# original = recording.flatten()

# processed = preprocess_audio(original.copy())

# save_wav("original2.wav", original)
# save_wav("processed2.wav", processed)

# print("Saved original.wav and processed.wav")



# # To check available devices in my laptop
# # devices.py
# import sounddevice as sd

# print(sd.query_devices())
# print("Default devices:", sd.default.device)



# import torch
# from qwen_tts import Qwen3TTSModel

# print("Qwen3-TTS imported successfully!")

# print("PyTorch:", torch.__version__)
# print("CUDA available:", torch.cuda.is_available())

# if torch.cuda.is_available():
#     print("GPU:", torch.cuda.get_device_name(0))
#     print("CUDA version:", torch.version.cuda)
#     print("VRAM:", round(
#         torch.cuda.get_device_properties(0).total_memory / 1024**3,
#         2
#     ), "GB")


# testing mio's voice
# from tts import MioTTS

# tts = MioTTS()

# tts.start()

# tts.feed("Hey! You're finally here.")
# tts.feed("I've been waiting for you.")
# tts.feed("How was your day?")

# tts.flush()
# tts.wait()

# tts.stop()



# checking models precision
# import torch
# from tts import MioTTS

# tts = MioTTS()

# print("\n--- Model dtype summary ---")

# dtypes = {}
# for name, param in tts.voice.model.named_parameters():
#     dtypes[str(param.dtype)] = dtypes.get(str(param.dtype), 0) + 1

# print(dtypes)

# print("\n--- Code predictor dtype ---")

# for name, module in tts.voice.model.named_modules():
#     if "code_predictor" in name:
#         param = next(module.parameters(), None)
#         if param is not None:
#             print(name, param.dtype, param.device)
#         break

# print("\n--- GPU memory ---")
# print("Allocated:", round(torch.cuda.memory_allocated() / 1024**3, 2), "GB")
# print("Reserved:", round(torch.cuda.memory_reserved() / 1024**3, 2), "GB")

# release gpu memory
# Release the VoiceDesign model to free GPU memory

# import gc
# import torch

# gc.collect()
# torch.cuda.empty_cache()

# MEmory testing
import memory

# Save
# m = memory.save_memory("explicit", "I am building Mio.")

# # Retrieve
# print(memory.get_memory(m.id))

# # Update
# memory.update_memory(m.id, content="I am developing Mio.")

# List
# print(memory.get_all_memories())

# Delete
# memory.delete_memory(m.id)


# import memory

# test_memories = [
#     "I love Python.",
#     "I am good at Python backend development.",
#     "I enjoy building AI applications.",
#     "I prefer dark mode.",
#     "I love sweets.",
#     "I keep sweets with me everytime.",
#     "I enjoy running.",
#     "I like learning new technologies.",
#     "I use VS Code for development.",
#     "I am interested in machine learning.",
#     "I enjoy building personal AI assistants.",
#     "I prefer practical project-based learning.",
#     "I love listening to music.",
#     "I enjoy reading books.",
#     "I want to improve my coding skills.",
#     "I am interested in Docker.",
#     "I enjoy working with Linux.",
#     "I prefer simple explanations.",
#     "I am learning about LLMs.",
#     "I want to build my own AI ecosystem."
# ]

# for content in test_memories:
#     saved = memory.save_memory(
#         category="explicit",
#         content=content
#     )
#     print(f"Saved ID {saved.id}: {saved.content}")

# print("\nTotal explicit memories:",
#       len(memory.get_all_memories(category="explicit")))


# from agent.orchestrator import run_agent


# response = run_agent("What time is it?")


# from conversation_manager import process_message

# # Test ordinary conversation
# response = process_message("Hey Mio, how are you?")


# # Test tool execution
# response = process_message("What time is it?")


# # Test explicit memory
# response = process_message("forget running.")

print(memory.get_all_memories())
