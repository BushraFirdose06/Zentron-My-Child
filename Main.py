from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)
from Backend.Model import FirstLayerDMM
from googlesearch import search
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from Backend.PowerPointGeneration import GeneratePresentation
from dotenv import dotenv_values
from asyncio import run
from time import sleep
from PyQt5.QtGui import QTextCursor
import subprocess
import threading
import json
import os
shared_lock = threading.Lock()
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
DefaultMessage = f'''{Username} : Hello {Assistantname}, How are you?
{Assistantname} : Welcome {Username}. I am doing well. How may i help you?'''
subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]


class Status:
    LISTENING = "Listening ..."
    THINKING = "Thinking ..."
    ANSWERING = "Answering ..."
    SEARCHING = "Searching ..."
    AVAILABLE = "Available ..."

# Usage:
SetAssistantStatus(Status.THINKING)

def ShowDefaultChatIfNoChats():
    with open(r'Data\ChatLog.json', "r", encoding='utf-8') as file:
        if len(file.read()) < 5:
            with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as db_file:
                db_file.write("")
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as resp_file:
                resp_file.write(DefaultMessage)

                
def ReadChatLogJson():
    try:
        with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading ChatLog: {e}")
        return []
    
def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"Assistant: {entry['content']}\n"
    formatted_chatlog = formatted_chatlog.replace("User",Username + " ")
    formatted_chatlog = formatted_chatlog.replace("Assistant",Assistantname + " ")

    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    File = open(TempDirectoryPath('Database.data'),"r", encoding='utf-8')
    Data = File.read()
    if len(str(Data))>0:
        lines = Data.split('\n')
        result = '\n'.join(lines)
        File.close()
        File = open(TempDirectoryPath('Responses.data'),"w", encoding='utf-8')
        File.write(result)
        File.close()

def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

InitialExecution()

def MainExecution():
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""
    
    for queries in Decision:
        if "generate presentation" in queries:
            topic = queries.replace("generate presentation ", "")
            # First get content
            content = ChatBot(f"Provide detailed content for a PowerPoint presentation about {topic}")
            # Then generate presentation
            presentation_path = GeneratePresentation(topic, content)
            if presentation_path:
                ShowTextToScreen(f"{Assistantname} : I've created a PowerPoint presentation about {topic}")
                TextToSpeech(f"I've created a PowerPoint presentation about {topic}")
                # Open the presentation
                subprocess.Popen(['start', presentation_path], shell=True)
            else:
                ShowTextToScreen(f"{Assistantname} : Sorry, I couldn't generate the presentation")
                TextToSpeech("Sorry, I couldn't generate the presentation")
            return True

    SetAssistantStatus("Listening ...")
    Query = SpeechRecognition()  # Note: Fix SpeechToText.py to use manual ChromeDriver to avoid KeyboardInterrupt
    ShowTextToScreen(f"{Username} : {Query}")
    SetAssistantStatus("Thinking...")
    Decision = FirstLayerDMM(Query)

    print("")
    print(f"Decision : {Decision}")
    print("")

    G = any([i for i in Decision if i.startswith("general")])
    R = any([i for i in Decision if i.startswith("realtime")])

    Merged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )

    for queries in Decision:
        if "generate " in queries:
            ImageGenerationQuery = str(queries)
            ImageExecution = True

    for queries in Decision:
        if TaskExecution == False:
            if any(queries.startswith(func) for func in Functions):
                run(Automation(list(Decision)))
                TaskExecution = True

        if ImageExecution == True:
            with open(r"Frontend\Files\ImageGeneration.data", "w") as file:
                file.write(f"{ImageGenerationQuery},True")

            try:
                pl = subprocess.Popen(['python', r'Backend\ImageGeneration.py'],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     stdin=subprocess.PIPE, shell=False)
                subprocesses.append(pl)
            except Exception as e:
                print(f"Error starting ImageGeneration.py: {e}")

        if G and R:
            SetAssistantStatus("Searching...")
            Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
            ShowTextToScreen(f"{Assistantname} : {Answer}")
            SetAssistantStatus("Answering...")
            TextToSpeech(Answer)
            return True
        else:
            for Queries in Decision:
                if "general" in Queries:
                    SetAssistantStatus("Thinking...")
                    QueryFinal = Queries.replace("general ", "")
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname} : {Answer}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    return True
                elif "realtime" in Queries:
                    SetAssistantStatus("Searching...")
                    QueryFinal = Queries.replace("realtime ", "")
                    Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname} : {Answer}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    return True
                elif "exit" in Queries:
                    QueryFinal = "Okay, Bye!"
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname} : {Answer}")
                    SetAssistantStatus("Answering ..")
                    TextToSpeech(Answer)
                    SetAssistantStatus("Answering...")
                    os._exit(1)

def FirstThread():
    while True:
        with shared_lock:
            CurrentStatus = GetMicrophoneStatus()
            if CurrentStatus == "True":
                MainExecution()
            else:
                AIStatus = GetAssistantStatus()
                if "Available..." in AIStatus:
                    sleep(0.1)
                else:
                    SetAssistantStatus("Available...")

def SecondThread():
    GraphicalUserInterface()
    global shutdown_flag
    shutdown_flag = True

if __name__ == "__main__":
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    SecondThread()