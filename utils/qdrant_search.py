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