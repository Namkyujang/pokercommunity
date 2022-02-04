from game import play

def opp(credit):
    lopp={'Marcus':1000,'Mr Volovski':2000,'Pokerbot':3000,'Checkmate':4000,'Mr Mafia':5000}
    #play=True   
    for key in lopp.keys():
        print(key,':',lopp[key])
    a=input('Choose your opponent:')
    if a=='Marcus':
        if credit>=1000:
            print('Ok')
            play.game1(credit, ('Marcus', 1000))#game1 is a fuction from module play referring to the 1 verses 1 situation
        else:
            print('No')
            
    elif a=='Mr Volovski':
        if credit>=2000:
            print('Ok')
            play.game1(credit,('Mr Volovski',2000))
        else:
            print('No')
            
    elif a=='Pokerbot':
        if credit>=3000:
            print('Ok')
        else:
            print('No')
            
    elif a=='Checkmate':
        if credit>=4000:
            print('Ok')
        else:
            print('No')
            
    elif a=='Mr Mafia':
        if credit>=5000:
            print('Ok')
        else:
            print('No')
            
    else:
        print('No such opponent')
    