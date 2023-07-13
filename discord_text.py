import csv
import pandas as pd
import numpy as np
import nltk
from nltk.corpus import stopwords
from textblob import TextBlob
from nltk.stem import PorterStemmer
from textblob import Word
import sklearn
#from sklearn.feature_extraction.text import TfidfVectorizer

https://www.analyticsvidhya.com/blog/2018/02/the-different-methods-deal-text-data-predictive-python/

df = pd.read_csv("bananabread_chat_csv_form.csv")

# look at head of dataset
df.head()
df.shape # 1,520 messages shared between the two of us, 6 variables

for col in df.columns:
  print(col)
# AuthorID
# Author
# Date
# Content
# Attachments
# Reactions

# convert variable names to lowercase 
disc_df = df.rename(columns=str.lower)

list(disc_df.columns)
# colnames: 'authorid', 'author', 'date', 'content', 'attachments', 'reactions'

disc_df.head()

# save rows where content isn't NaN
disc_df = disc_df[disc_df['content'].notna()]

# attachments columns links to jpg, png, mov, etc.
disc_df.attachments.unique()

# if attachment is NaN - replace value with 0, if attachment is not NaN - replace value with 1
#disc_df['attachments'] = np.where(pd.isna(disc_df['attachments']), 0, 1)


# find unique values under reactions
disc_df.reactions.unique()
sum(pd.isna(disc_df.reactions))/len(disc_df)
# 99.6% of messages have no reactions, so I'll remove reactions as a column

sum(disc_df['attachments'] == 1) / len(disc_df)
# 97.27% of messages have an attachment so remove attachment

# we just want to work with the content

disc_df.content.unique()

# remove messages that were just discord calls being started
# example: Started a call that lasted 96 minutes

disc_df = disc_df[disc_df['content'].str.contains("Started a call that lasted")==False]

# remove messages with JUST links

disc_df = disc_df[~(disc_df['content'].str.contains("https://") & ~disc_df['content'].str.contains(" "))]

disc_df.shape # 1319 messages

# drop attachments and reactions columns
disc_df = disc_df.drop(columns=['attachments', 'reactions'])


# separate data into my messages and my sister's messages
sister_df = disc_df[disc_df['author'] == "bananaabread"]

# double checking for NaN values
sister_df.content.isna().sum()

# 686 messages sent to me from my sister
sister_df.shape


# add information to categorize the spam message 
sister_df['spam'] = np.where(sister_df['content'].str.contains("heyy ummm idk what happened or if its really you but"), 1, 0)

sister_df.spam.value_counts()

# count number of words in each message 
sister_df['word_count'] = sister_df['content'].apply(lambda x: len(str(x).split(" ")))

# number of characters
sister_df['char_count'] = sister_df['content'].str.len() ## including spaces

# average word length
def avg_word(sentence):
  words = sentence.split()
  return (sum(len(word) for word in words)/len(words))

sister_df['avg_word'] = sister_df['content'].apply(lambda x: avg_word(x))

# checkpoint: write csv
#disc_df.to_csv('disc_df.csv')
#sister_df.to_csv('sister_df.csv')

disc_df = pd.read_csv("disc_df.csv")
sister_df = pd.read_csv("sister_df.csv")

stop = stopwords.words('english')

sister_df['stopwords'] = sister_df['content'].apply(lambda x: len([x for x in x.split() if x in stop]))

# number of special characters
sister_df['hastags'] = sister_df['content'].apply(lambda x: len([x for x in x.split() if x.startswith('#')]))


# number of numerics 
sister_df['numerics'] = sister_df['content'].apply(lambda x: len([x for x in x.split() if x.isdigit()]))


# numer of uppercase words
sister_df['upper'] = sister_df['content'].apply(lambda x: len([x for x in x.split() if x.isupper()]))




# PREPROCESSING
sister_df_proc = sister_df 

# transform all messages to lowercase
sister_df_proc['content'] = sister_df_proc['content'].apply(lambda x: " ".join(x.lower() for x in x.split()))

# remove punctuation
sister_df_proc['content'] = sister_df_proc['content'].str.replace('[^\w\s]','')

# remove stopwords
sister_df_proc['content'] = sister_df_proc['content'].apply(lambda x: " ".join(x for x in x.split() if x not in stop))

# common word removal
freq = pd.Series(' '.join(sister_df_proc['content']).split()).value_counts()[:10]
#print(freq)
# brena: 44, yes: 27, ok: 27, im: 22, call: 17, i'm: 17, yeah: 16, like: 14, idk: 14, thank: 12
freq = list(freq.index)
sister_df_proc['content'] = sister_df_proc['content'].apply(lambda x: " ".join(x for x in x.split() if x not in freq))

# rare words removal
freq = pd.Series(' '.join(sister_df_proc['content']).split()).value_counts()[-10:]
#print(freq)
# dollar: 1, lordy: 1, lord: 1, pass: 1, pro: 1, di: 1, do*: 1, okok: 1, okurrr: 1, notice: 1
freq = list(freq.index)
sister_df_proc['content'] = sister_df_proc['content'].apply(lambda x: " ".join(x for x in x.split() if x not in freq))

# spelling correction
#sister_df_proc['content'].apply(lambda x: str(TextBlob(x).correct()))
# too much text lingo to make sense to apply

# tokenization
# divide text into individual words
TextBlob(sister_df_proc['content'][1]).words

# lemmatization
# remove suffices like "ing", "ly", "s", etc. - strips words to their root words
sister_df_proc['content'] = sister_df_proc['content'].apply(lambda x: " ".join([Word(word).lemmatize() for word in x.split()]))


## ADVANCE TEXT PROCESSING ##

# N-grams: bi-grams
TextBlob(sister_df_proc['content'][0]).ngrams(2)

# term frequency 
# ratio of count of word present in a sentence, to length of sentence
tf1 = (sister_df_proc['content']).apply(lambda x: pd.value_counts(x.split(" "))).sum(axis = 0).reset_index()
tf1.columns = ['words','tf']
tf1

# collect the words in the spam message
spam_message_words = sister_df_proc[sister_df_proc['spam'] == 1]
spam_message_words
TextBlob(spam_message_words['content'][1]).words

spam_message_words = spam_message_words.content.astype('string')


## inverse document frequency
# idf of each word - log of the ratio of the total number of rows to the number of rows in which that word is present

for i,word in enumerate(tf1['words']):
  tf1.loc[i, 'idf'] = np.log(sister_df_proc.shape[0]/(len(sister_df_proc[sister_df_proc['content'].str.contains(word)])))
  
tf1

# tf-idf multiplication of the TF and IDF
tf1['tfidf'] = tf1['tf']*tf1['idf']

tf1

# sentiment analysis
sister_df_proc['content'].apply(lambda x: TextBlob(x).sentiment)

spam_message_words = spam_message_words.to_string()


word_list = TextBlob(spam_message_words).words

sister_df_proc['sentiment'] = sister_df_proc['content'].apply(lambda x: TextBlob(x).sentiment[0])

tf1['spam'] = np.where(tf1['words'].isin(word_list), 1, 0)

# write data to use in project
tf1.to_csv('tf1_df.csv')
sister_df_proc.to_csv('sister_df_proc.csv')

