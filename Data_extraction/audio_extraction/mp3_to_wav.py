from pydub import AudioSegment
audio = AudioSegment.from_mp3("D:\\AIC\\AIC\\Data_extraction\\audio_test\\L01_V001.mp3")
audio.export("D:\\AIC\\AIC\\Data_extraction\\audio_test\\L01_V001.wav", format="wav")
