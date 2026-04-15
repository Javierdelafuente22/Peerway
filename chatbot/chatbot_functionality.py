import json
import os
import queue
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav

from chatbot.chatbot_API import EnergyChatbot
from chatbot.chatbot_data import apply_lifestyle_update, get_plot_window, plot_demand_comparison

def record_audio(filename="last_recording.wav", fs=44100):
    """
    Records audio in the background until the user presses Enter.
    """
    print("\nRecording... Press ENTER to stop.")
    
    q = queue.Queue()
    is_recording = True

    def audio_callback(indata, frames, time, status):
        """This function runs in the background and grabs audio chunks."""
        if is_recording:
            q.put(indata.copy())

    # Start the microphone stream in the background
    stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', callback=audio_callback)
    
    with stream:
        # The main script waits here until you press Enter
        input() 
        is_recording = False

    print("Audio captured.")

    # Reassemble the background audio chunks into a single file
    audio_chunks = []
    while not q.empty():
        audio_chunks.append(q.get())

    if audio_chunks:
        audio_data = np.concatenate(audio_chunks, axis=0)
        wav.write(filename, fs, audio_data)
        
    return filename

def main():
    agent = EnergyChatbot()
    print("\n" + "="*50)
    print("Chat to your Energy Agent")
    print("="*50 + "\n")
    print("Type 'audio' to switch to Voice Mode. Type 'text' to switch back.")

    input_mode = "text" 

    while True:
        # [UI BUTTON REPLACEMENT: Input Mode Toggle]
        user_text = input(f"\nYou ({input_mode.upper()} MODE): ").strip()
        
        if user_text.lower() == 'audio':
            input_mode = "audio"
            continue
        elif user_text.lower() == 'text':
            input_mode = "text"
            continue

        if input_mode == "text":
            result = agent.get_chat_response(user_input=user_text)
            
        elif input_mode == "audio":
            # [UI BUTTON REPLACEMENT: Start/Stop Recording]
            audio_file = record_audio(filename="chatbot/last_recording.wav")
            print("Processing audio with Gemini...")
            
            result = agent.get_chat_response(audio_path=audio_file)

        if result.get("category") == "Error":
            print(f"Chatbot [Error]: {result.get('mission_check')}")
            print("-" * 40)
            continue

        if "transcript" in result:
            print(f"\n[Transcript]: \"{result['transcript']}\"")

        # [UI BUTTON REPLACEMENT: Yes/No Confirmation]
        print(f"Chatbot: {result.get('mission_check')} [Y/N]")
        choice = input("> ").strip().lower()

        if choice in ['y', 'yes']:
            payload = {k: v for k, v in result.items() if k not in ["mission_check", "transcript"]}
            print("\nUser Confirmed. Sending to Simulation Engine...")
            
            modified_df = apply_lifestyle_update(json_payload=payload)
            
            if modified_df is not None:
                plot_data = get_plot_window(modified_df, payload)
                plot_demand_comparison(plot_data, payload['category'])
        else:
            print("\nCancelled. No changes were made.")

        print("\n" + "="*50)
        print("Ready for your next request...")
        print("="*50 + "\n")

if __name__ == "__main__":
    main()