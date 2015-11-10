#!/usr/bin/python

import sys, socket, pickle
from random import shuffle
class TableState:
    def __init__(self, numPlayers, deck, hands, discardPile):
        self.numPlayers = numPlayers
        #self.initHandSize = initHandSize
        self.deck = deck
        self.hands = hands
        self.discardPile = discardPile

    def abstractHands(self, player):
        newlist = []
        for i in range(len(self.hands)):
            if i == player:
                newlist.append(self.hands[i][:])
            else:
                newlist.append(len(self.hands[i]))
        return newlist
                
    def abstractState(self, player):
        return [player,
                self.numPlayers,
                len(self.deck),
                self.abstractHands(player),
                self.discardPile]

def main(argv):
    arg_len = len(sys.argv)
    if arg_len < 2:
        print("usage: server.py <numPlayers>")
        sys.exit(2)

    deckSize = 104
    initHandSize = 9
    numPlayers = int(sys.argv[1])
    deck = range(deckSize)
    shuffle(deck)
    print(deck)

    hands = []

    #deal cards to players
    for i in range(numPlayers):
        hands.append([])
        for j in range(initHandSize):
            card, deck = drawCardFromDeck(deck)
            hands[i].append(card)

    #deal initial discard
    card, deck = drawCardFromDeck(deck)
    discardPile = [card]
    
    tableState = TableState(numPlayers, deck, hands, discardPile)
    print(tableState.hands)
    print(tableState.deck)
    print(tableState.discardPile)
    
    connections = []
    
    s = socket.socket()         # Create a socket object
    host = socket.gethostname() # Get local machine name
    port = 12345                # Reserve a port for your service.
    s.bind((host, port))        # Bind to the port
    s.listen(5)                 # Now wait for client connection.:w

    
    for conn_count in range(numPlayers):
        remaining = numPlayers-conn_count
        print('Waiting for ', remaining, ' more connections')
        c, addr = s.accept()     # Establish connection with client.
        print('Got connection from', addr)
        connections.append([c, addr])

    print("All players connected!")
    for conn_count in range(numPlayers):
        #print conn_count
        #print tableState.abstractState(conn_count)
        serialized_abstract_state = pickle.dumps(tableState.abstractState(conn_count))
        connections[conn_count][0].send(serialized_abstract_state)

    print("All hands sent")
    
        #c.send('Thank you for connecting')
        #c.close()                # Close the connection
    

# naive implementation of draw.
# TODO: if deck is empty, reshuffle discard pile into deck
def drawCardFromDeck(deck):
    return deck[0], deck[1:]
    
if __name__ == "__main__":
    main(sys.argv)
