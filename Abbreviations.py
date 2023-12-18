import re
import itertools as it
import pandas as pd
import numpy as np

#Function to read a file and save each line as a list.
def FileRead():
    list_words = []
    FileRead.filename = input("Enter the file name:") #storing file name as a function attribute to reference later
    f = FileRead.filename + ".txt"
    file_words = open(f,"r")
    lines = file_words.read()
    list_words = lines.splitlines() #splitting each name into a list
    file_words.close()
    return(list_words)

#Function to clean each name by removing all characters & replacing '-' to space
def CleanWords():
    list_words = FileRead()
    orig_words = list_words
    list_words = [word.upper() for word in list_words] #making all letters to upper case
    list_words = [word.replace("-"," ") for word in list_words] #replacing - to space
    list_words = [re.sub(r"[^\w\s]", '', word) for word in list_words] #ignoring all other characters
    CleanWords.orig_word_dict = {list_words[i]: orig_words[i] for i in range(len(list_words))} #creating a dictionary (as function attribute) of cleaned words and original words to reference later
    return(list_words)

#Function to get all possible 3-letter combinations for each name.
def CreateAbbr():
    list_words = CleanWords()
    acr_list = []
    acr_dict = {}
    for word in list_words:
        word1 = word.replace(" ", "") #ignore the spaces while making combinations
        for (a,b,c) in it.combinations(word1, 3):
            acr_list.append(a+b+c) 
        acr_list_set = set(acr_list) #unique combinations for each name
        acr_list = list(acr_list_set)
        acr_dict[word] =acr_list #making a dict with names as key and list of acronyms as value
        acr_list = []
    return(acr_dict)

#Function to calculate score of each acronyms of words.
def CalculateScore():
    acr_dict = CreateAbbr()
    with open("value.txt","r") as val: #open values.txt to use as reference
        values = {k:v for k, v in map(str.split, val)} #storing as key:value pairs

    score = 0
    full_list = []
    for words,acr_list in acr_dict.items():
        wordlist = words.split() #split each name to consider multiple words in a name
        for acr in acr_list:
            flag =0
            pos1 = wordlist[0].find(acr[0]) #find position of first letter in first word
            if pos1 == 0:
                score = score+0 #score =0
            else:
                score = score+10000 #the first letter of acronym should be the first letter of the name else setting score to high value
            
            for w in range(0,len(wordlist)):
                temp_word = wordlist[w]
                if pos1 ==0 and w==0:
                    temp_word= temp_word[:pos1] + "#"+ temp_word[pos1+1:] #Makiing first letter to '#' so it wont be considered again
                pos2 = temp_word.find(acr[1]) #finding position of 2nd acronym in the name
                if pos2 == 0:
                        score =score+0
                        flag = 3 #to flag that the second acronym has been found and scored
                        temp_word= temp_word[:pos2] + "#"+ temp_word[pos2+1:] #to ignore in next iteration as it is already considered
                elif pos2 == len(wordlist[w])-1 and flag != 3:
                    if acr[1] != 'E':
                        score = score+5
                        flag =1
                        temp_word= temp_word[:pos2] + "#"+ temp_word[pos2+1:]
                    else:
                        score =score+20
                        flag =1
                        temp_word= temp_word[:pos2] + "#"+ temp_word[pos2+1:]
                elif (pos2 in [1,2]) and flag != 3:
                    score = score+ pos2+ int(values[acr[1]]) #score calculated with position and the value assosciated to each letter
                    flag =1
                    temp_word= temp_word[:pos2] + "#"+ temp_word[pos2+1:]
                elif pos2>=3 and flag != 3:
                    score = score+ 3+ int(values[acr[1]]) #score calculated with position_score =3 and the value assosciated to each letter
                    flag =1
                    temp_word= temp_word[:pos2] + "#"+ temp_word[pos2+1:]
            
                if pos2 != -1:
                    temp_word1 = temp_word[pos2:]
                    pos3 = temp_word1.find(acr[2])
                else:
                    pos3 = temp_word.find(acr[2]) #finding position of 3rd acronym in the name
                if  pos3 != -1 and flag !=0: #making sure the score of 3rd acronym is only found after 2nd acronym
                    if temp_word.find(acr[2]) == len(temp_word)-1:
                        if acr[2] != 'E':
                            score = score+5
                        else:
                            score = score+20
                    elif temp_word.find(acr[2]) == 1:
                        score = score+1+ int(values[acr[2]])
                    elif temp_word.find(acr[2]) == 2:
                        score = score+2+ int(values[acr[2]])
                    elif temp_word.find(acr[2]) >=3:
                        score = score+3+ int(values[acr[2]])
                    elif temp_word.find(acr[2]) == 0:
                            score =score+0
            new_list = [CleanWords.orig_word_dict[words],acr,score] #referncing earlier directory to store the user given names
            full_list.append(new_list)
            score=0
    acr_df = pd.DataFrame(full_list,columns=["words","acr","score"]) #create dataframe with names,acr and score
    return(acr_df)

#Function to find the best accronym for the name
def FindAcr():
    acr_df = CalculateScore()
    #creating copy of the dataframe
    acr_df_copy = acr_df[['words']].copy()
    acr_df_copy = acr_df_copy.assign(acr = '')
    acr_df_copy = acr_df_copy.drop_duplicates(subset = "words")
    #Dropping all unwanted rows
    acr_df.drop(acr_df[acr_df['score']>=10000].index,inplace = True) #drop all acronyms with high scores
    acr_df = acr_df.drop_duplicates(subset="acr",keep=False) #drop all duplicates
    #Finding minimum score
    min_value = acr_df.groupby('words').score.min()
    acr_df = acr_df.merge(min_value, on = 'words', suffixes = ('','_min'))
    acr_df = acr_df[acr_df.score == acr_df.score_min].drop('score_min',axis =1)
    #to find any names without any acronyms
    acr_df_diff = acr_df_copy[~acr_df_copy.words.isin(acr_df.words)]
    acr_df_full =  pd.concat([acr_df,acr_df_diff]).sort_index() #concat the missing names
    #drop the score column
    acr_df_full.drop('score', axis=1, inplace=True)
    #Group names and concat those with multiple abbreviations
    acr_df_full['acr'] = acr_df_full[['words','acr']].groupby(['words'])['acr'].transform(lambda x: ' '.join(x))
    acr_df_full = acr_df_full[['words','acr']].drop_duplicates()
    return(acr_df_full)

#main function to save the output as csv
def main():
    acr_df = FindAcr()
    output_name = 'Raman_'+FileRead.filename+'_abbrevs.txt' #Referncing the input file name for output name scheme
    acr_df.to_csv(output_name,sep = '\n',encoding='utf-8',index =False, header = False) #output the file as txt
main()
