import random
def game1(credit,opponent):#opponnent is a tuple variable from module opp
    heart=[('H','a'),('H','2'),('H','3'),('H','4'),('H','5'),('H','6'),('H','7'),('H','8'),('H','9'),('H','10'),('H','K'),('H','Q'),('H','J')]
    diamond=[('D','a'),('D','2'),('D','3'),('D','4'),('D','5'),('D','6'),('D','7'),('D','8'),('D','9'),('D','10'),('D','K'),('D','Q'),('D','J')]
    clover=[('C','a'),('C','2'),('C','3'),('C','4'),('C','5'),('C','6'),('C','7'),('C','8'),('C','9'),('C','10'),('C','K'),('C','Q'),('C','J')]
    spade=[('S','a'),('S','2'),('S','3'),('S','4'),('S','5'),('S','6'),('S','7'),('S','8'),('S','9'),('S','10'),('S','K'),('S','Q'),('S','J')]    
    while credit<=opponent[1]:
        pool=0
        deck=heart+diamond+clover+spade
        random.shuffle(deck)
        print("You have {} credits".format(credit))
        mybet=int(input("How much do you wanna bet?:"))
        if mybet>credit:
            print("Thats too much")
        elif mybet==credit:
            print("All in")
            credit=credit-mybet
            opbet=opponent[1]
            opponent[1]=opponent[1]-opbet
            pool=mybet+opbet
            print("There is {} on the pool".format(pool))
            myhand=deck[:2]
            ophand=deck[2:4]
            print("This is your hand\t{}".format(myhand))
            comcards=deck[4:7]
            print("The community cards are these.")
            print("{}".format(comcards))
            comcards=comcards+deck[7:8]
            print("The community cards are these.")
            print("{}".format(comcards))
            comcards=comcards+deck[8:9]
            myline=myhand+comcards
            opline=ophand+comcards#going to make a compare funtion in hand in order to define who wins
            #first have to make function makebest in order to define the best set of hands each player has.
            #then have to make compare function to define winner.


#I am right now in the process of creating game1 and the functions nessessary for it. The only probelm is to create the system that will represent the card rankings in order 
#to define the winner and create the best set of hands that either player has.
#I still have to create the non all in situation.