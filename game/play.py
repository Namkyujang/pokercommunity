import random,bet
def game1(credit,opponent):
    heart=[('H','a'),('H','2'),('H','3'),('H','4'),('H','5'),('H','6'),('H','7'),('H','8'),('H','9'),('H','10'),('H','K'),('H','Q'),('H','J')]
    diamond=[('D','a'),('D','2'),('D','3'),('D','4'),('D','5'),('D','6'),('D','7'),('D','8'),('D','9'),('D','10'),('D','K'),('D','Q'),('D','J')]
    clover=[('C','a'),('C','2'),('C','3'),('C','4'),('C','5'),('C','6'),('C','7'),('C','8'),('C','9'),('C','10'),('C','K'),('C','Q'),('C','J')]
    spade=[('S','a'),('S','2'),('S','3'),('S','4'),('S','5'),('S','6'),('S','7'),('S','8'),('S','9'),('S','10'),('S','K'),('S','Q'),('S','J')]    
    while credit<=opponent[1]
        pool=0
        deck=heart+diamond+clover+spade
        random.shuffle(deck)
        ophand=deck[:2]
        myhand=deck[2:4]
        print(myhand)
        mybet=int(input('How much you wanna bet:'))
        a==True
        while a:
            if 0<=mybet<credit:
                credit=credit-mybet
                pool=pool+mybet
                opbet=mybet*2
                opponent[1]=opponent[1]-opbet
                pool=pool+opbet
                print(pool)
                comcards=deck[4:7]
                print(comcards)
                mybet=int(input('How much you wanna bet:'))
                b==True
                while b:
                    if 0<=mybet<credit:
                         credit=credit-mybet
                        pool=pool+mybet
                        print('gamble')
                        comcards=comcards+deck[7:8]
                        print(comcards)
                        print('gamble')
                        comcards=comcards+deck[8:9]
                    
                    else:
                        print('Not enough money')
                        b==False
                a==False

            
            else:
                print('Not enough money')
        
        