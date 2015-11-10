#!/usr/bin/python

import sys, socket
from random import shuffle

def main(argv):
    arg_len = len(sys.argv)
    if arg_len < 2:
        print "usage: ", sys.argv[0]," <numPlayers>"
        sys.exit(2)

    initHandSize = 9
    numPlayers = int(sys.argv[1])
    deck = range(104)
    shuffle(deck)
    print deck

    hands = []

    #deal cards to players
    for i in range(numPlayers):
        hands.append([])
        for j in range(initHandSize):
            card, deck = drawCardFromDeck(deck)
            hands[i].append(card)

    #deal initial discard
    card, deck = drawCardFromDeck(deck)
    discard = [card]
    
    print hands
    print deck
    print discard
    
    '''
    # Commenting all network connections for now
    
    s = socket.socket()         # Create a socket object
    host = socket.gethostname() # Get local machine name
    port = 12345                # Reserve a port for your service.
    s.bind((host, port))        # Bind to the port
    s.listen(5)                 # Now wait for client connection.:w
    
    while True:
        c, addr = s.accept()     # Establish connection with client.
        print 'Got connection from', addr
        #c.send('Thank you for connecting')
        #c.close()                # Close the connection
    '''

# naive implementation of draw.
# TODO: if deck is empty, reshuffle discard pile into deck
def drawCardFromDeck(deck):
    return deck[0], deck[1:]
    
if __name__ == "__main__":
    main(sys.argv)
