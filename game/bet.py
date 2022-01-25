import random
def gamble(mybet,ophand,comcards,credit,pool):
    showdown=ophand+comcards
    for i in range(len(showdown)):
        cmbn=[]
        if showdown[i][1]='1':
            cmbn.append(showdown[i])
            if len(cmbn)==2:
                
