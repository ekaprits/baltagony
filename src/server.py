#!/usr/bin/python

import sys, socket, json, threading
from random import shuffle
from Mastermind import *

ACTION_DRAW = 0
ACTION_PASS = 1
ACTION_PLAY = 2
ACTION_CONCEDE_DRAW = 3

connections = []
numConnections = 0
numPlayers = 0
tableState = None

class Server(MastermindServerTCP):
    def __init__(self):
        MastermindServerTCP.__init__(self, 0.5,0.5,100.0) #server refresh, connections' refresh, connection timeout

        self.mutex = threading.Lock()
        
    def callback_connect          (self                                          ):
        print "Server connecting"
        return super(Server,self).callback_connect()
    def callback_disconnect       (self                                          ):
        #Something could go here
        return super(Server,self).callback_disconnect()
    def callback_connect_client   (self, connection_object                       ):
        global numConnections, connections, numPlayers, tableState
        self.mutex.acquire()
        if numConnections > numPlayers:
            return super(Server,self).callback_connect_client(connection_object)
        
        connections[numConnections] = connection_object

        print "Client connected. Active connections: ", numConnections
            
        serialized_abstract_state = json.dumps(tableState.abstractState(numConnections))
        print serialized_abstract_state
        
        self.callback_client_send(connection_object, serialized_abstract_state)
        numConnections = numConnections + 1
        #if numConnections == numPlayers:
        #    self.accepting_disallow()
        
        self.mutex.release()
        return super(Server,self).callback_connect_client(connection_object)
    def callback_disconnect_client(self, connection_object                       ):
        #Something could go here
        return super(Server,self).callback_disconnect_client(connection_object)

    def callback_client_receive   (self, connection_object                       ):
        return super(Server,self).callback_client_receive(connection_object)
    def callback_client_handle    (self, connection_object, data                 ):
        global numConnections, connections, numPlayers, tableState
        action = json.loads(data)
        print "Received player action ", action
        sending_player = connections.index(connection_object)
        print "Sending player is ", sending_player
        if sending_player != tableState.activePlayer:
            print "Not the active player. Ignoring action"
            return
        actionType = action[0]
        card = action[1]
        forcedSuit = action[2]
        
        if actionType == ACTION_DRAW:
            #card, deck = drawCardFromDeck(deck)
            print "Player ", tableState.activePlayer, " drew a card"
            tableState.playerDrawsCard(tableState.activePlayer)
            tableState.seven_streak = 0
        elif actionType == ACTION_PASS:
            print "Player ", tableState.activePlayer, " passed his turn"
            tableState.numDraws[tableState.activePlayer] = 0
            tableState.activePlayer = (tableState.activePlayer+1)%numPlayers
            tableState.seven_streak = 0
        elif actionType == ACTION_PLAY:
            print "Player ", tableState.activePlayer, " played ", card
            tableState.playerPlaysCard(tableState.activePlayer, card, forcedSuit)
            tableState.numDraws[tableState.activePlayer] = 0
            if len(tableState.hands[tableState.activePlayer]) == 0:
                tableState.win_status = tableState.activePlayer
                tableState.activePlayer = -1
            elif card % 13 == 6:  # card is a 7
                tableState.seven_streak = tableState.seven_streak + 1
                tableState.activePlayer = (tableState.activePlayer+1)%numPlayers
            elif card % 13 == 8:  # a 9 skips next player
                tableState.activePlayer = (tableState.activePlayer+2)%numPlayers
                tableState.seven_streak = 0
            elif card % 13 != 7:   # with an 8, you play again 
                tableState.activePlayer = (tableState.activePlayer+1)%numPlayers
                tableState.seven_streak = 0
        elif actionType == ACTION_CONCEDE_DRAW:
            print "Player ", tableState.activePlayer, " concedes draw"
            numCardsToDraw = 2*tableState.seven_streak
            for i in range(numCardsToDraw):
                tableState.playerDrawsCard(tableState.activePlayer,False)
            tableState.seven_streak = 0
            
        for conn_index in range(numPlayers):
            serialized_abstract_state = json.dumps(tableState.abstractState(conn_index))
            self.callback_client_send(connections[conn_index], serialized_abstract_state)

    def callback_client_send      (self, connection_object, data,compression=None):
        #Something could go here
        return super(Server,self).callback_client_send(connection_object, data,compression)

class TableState:
    def __init__(self, numPlayers, deck, hands,
                 discardPile, numDraws, activePlayer,
                 forcedSuit, seven_streak, win_status):
        self.numPlayers = numPlayers
        self.deck = deck
        self.hands = hands
        self.discardPile = discardPile
        self.numDraws = numDraws
        self.activePlayer = activePlayer
        self.forcedSuit = forcedSuit
        self.seven_streak = seven_streak
        self.win_status = win_status

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
                self.discardPile,
                self.numDraws,
                self.activePlayer,
                self.forcedSuit,
                self.seven_streak,
                self.win_status]

    def playerDrawsCard(self, player, countsForNumDraws=True):
        # TODO: shuffle when deck is empty
        if len(self.deck)==0:
            print "Deck is empty. Shuffling all but the top card of discard pile into deck."
            cardOnTopList = self.discardPile[-1:]
            rest = self.discardPile[:-1]
            shuffle(rest)
            self.deck = rest
            self.discardPile = cardOnTopList
            
        card, self.deck = drawCardFromDeck(self.deck)
        self.hands[player].append(card)
        if countsForNumDraws:
            self.numDraws[player] = self.numDraws[player] + 1

    def playerPlaysCard(self, player, card, forcedSuit):
        if card not in self.hands[player]:
            card = card+52
        self.hands[player].remove(card)
        self.discardPile.append(card)
        if(card % 13 == 0):
            self.forcedSuit = forcedSuit
        else:
            self.forcedSuit = -1
        
        
def main(argv):
    global numConnections, connections, numPlayers, tableState
    arg_len = len(sys.argv)
    if arg_len < 2:
        print("usage: server.py <numPlayers>")
        sys.exit(2)

    print "1"
    deckSize = 104
    initHandSize = 9
    numPlayers = int(sys.argv[1])
    connections = [None] * numPlayers
    deck = range(deckSize)
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
    discardPile = [card]

    numDraws = [0] * numPlayers
    tableState = TableState(numPlayers, deck, hands, discardPile, numDraws, 0, -1, 0, -1)
    print tableState.hands
    print tableState.deck 
    print tableState.discardPile 
    
    '''
    s = socket.socket()         # Create a socket object
    host = socket.gethostname() # Get local machine name
    port = 12345                # Reserve a port for your service.
    s.bind((host, port))        # Bind to the port
    s.listen(5)                 # Now wait for client connection.:w
    '''
    
    server = Server()
    host = socket.gethostname() # Get local machine name
    server.connect(host, 12345)
    try:
        server.accepting_allow_wait_forever()
    except:
        #Only way to break is with an exception
        pass
    server.accepting_disallow()
    server.disconnect_clients()
    server.disconnect()

    
# naive implementation of draw.
# TODO: if deck is empty, reshuffle discard pile into deck
def drawCardFromDeck(deck):
    return deck[0], deck[1:]
    
if __name__ == "__main__":
    main(sys.argv)
