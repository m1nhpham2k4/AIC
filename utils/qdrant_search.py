import json
import torch
import clip
import open_clip
import numpy as np
from PIL import Image
from utils.languages_translate import translate_text_GoogleTranslate, translate_text_GoogleGenerativeAI, translate_text_OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

class QdrantSearch:
    def __init__(self, dict_path, is_openclip=False):
        self.dict_path = dict_path
        self.is_openclip = is_openclip
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if is_openclip:
            self.open
