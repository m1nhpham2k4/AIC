import nltk
nltk.download('punkt_tab')
from nltk.tokenize import word_tokenize

caption0 = "A man is riding a horse on the beach."
tokens = word_tokenize(caption0)
print(tokens)