import os
import pickle
import threading
import queue
import base64
import json
import time
import asyncio
from io import BytesIO
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Callable
import random

import pyautogui
import sounddevice as sd
from vosk import KaldiRecognizer
from colorama import Fore
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import Document

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM

from text_to_voice import speak_through_vbcable
from voice_to_text import load_vosk_model
from query import maybe_fetch_articles
from training_tags import training_tags
from SYS_MSG import system_prompt
from training import training_loop
# from memory_methods import 



from training_tags import training_tags

    # ======TRAINING LOOP==============================================================


    def _training_loop(self, tags: List[str], config: Config) -> None:
        """
        Run a training loop over each tag: fetch top search results, prompt the LLM, and store the summary.
        """
        import json

        for tag in tags:
            # Build the search query and fetch top articles
            query = f"{tag} tutorial"
            try:
                articles = maybe_fetch_articles(query) or []
            except Exception as e:
                # Print and skip if fetching fails
                print(f"Failed to fetch articles for '{query}': {e}")
                articles = []

            # Take up to three results and serialize
            top_articles = articles[:3]
            if top_articles:
                serialized = json.dumps(
                    [
                        {"title": art.title, "snippet": art.snippet, "url": art.url}
                        for art in top_articles
                    ],
                    ensure_ascii=False,
                )
                search_results = f"[Search]\n{serialized}\n\n"
            else:
                search_results = ""

            # Build the prompt payload matching the PromptTemplate variables
            prompt_payload = {
                "system_prompt": config.system_prompt,
                "history": "",                            # No past conversation in training
                "embeddings": self._retrieve_memory(tag),  # Retrieve prior summary as embeddings
                "search_results": search_results,
                "screenshot_image": "",                   # Vision not used in this loop
                "user_input": f"Summarize '{tag}' tutorial with the above search results.",
            }

            # Run the chain and extract the summary
            reply = self.chain.run(**prompt_payload)
            summary = extract_summary(reply)

            # Store the new summary back into memory
            self._store_memory(tag, summary)