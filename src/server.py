#!/usr/bin/python

import sys, socket, json, threading
from random import shuffle
from Mastermind import *

ACTION_DRAW = 0
ACTION_PASS = 1
ACTION_PLAY = 2

connections = []
numConnections = 0
numPlayers = 0
tableState = None

class Server(MastermindServerTCP):
    def __init__(self):
        MastermindServerTCP.__init__(self, 0.5,0.5,10.0) #server refresh, connections' refresh, connection timeout

        #self.chat = [None]*scrollback
        self.mutex = threading.Lock()
        '''
        def add_message(self, msg):
        timestamp = strftime("%H:%M:%S",gmtime())

        self.mutex.acquire()
        self.chat = self.chat[1:] + [timestamp+" | "+msg]
        self.mutex.release()
        '''
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
            return
        print "numConnections = ", numConnections
        connections[numConnections] = connection_object

        print "Client connected. Active connections: ", numConnections
            
        serialized_abstract_state = json.dumps(tableState.abstractState(numConnections))
        print serialized_abstract_state
        #connections[conn_index].socket.send([serialized_abstract_state])
        self.callback_client_send(connection_object, serialized_abstract_state)
        numConnections = numConnections + 1
        if numConnections == numPlayers:
            self.accepting_disallow()
        
        self.mutex.release()
        return super(Server,self).callback_connect_client(connection_object)
    def callback_disconnect_client(self, connection_object                       ):
        #Something could go here
        return super(Server,self).callback_disconnect_client(connection_object)

    def callback_client_receive   (self, connection_object                       ):
        #Something could go here
        return super(Server,self).callback_client_receive(connection_object)
    def callback_client_handle    (self, connection_object, data                 ):
        action = json.loads(data)
        print("Received player action ", action)
        actionType = action[0]
        card = action[1]
        activeSuit = action[2]
        
        if actionType == ACTION_DRAW:
            #card, deck = drawCardFromDeck(deck)
            tableState.playerDrawsCard(tableState.activePlayer)
        elif actionType == ACTION_PASS:
            tableState.activePlayer = (tableState.activePlayer+1)%numPlayers
        elif actionType == ACTION_PLAY:
            tableState.playerPlaysCard(activePlayer, card, activeSuit)
            tableState.activePlayer = (tableState.activePlayer+1)%numPlayers

        for conn_index in range(numPlayers):
            serialized_abstract_state = json.dumps(tableState.abstractState(conn_index))
            self.callback_client_send(connections[conn_index], serialized_abstract_state)
            #connections[conn_index].socket.send(serialized_abstract_state)

        '''
        cmd = data[0]
        if cmd == "introduce":
            self.add_message("Server: "+data[1]+" has joined.")
        elif cmd == "add":
            self.add_message(data[1])
        elif cmd == "update":
            pass
        elif cmd == "leave":
            self.add_message("Server: "+data[1]+" has left.")
        '''
        #self.callback_client_send(connection_object, self.chat)
    def callback_client_send      (self, connection_object, data,compression=None):
        #Something could go here
        return super(Server,self).callback_client_send(connection_object, data,compression)

class TableState:
    def __init__(self, numPlayers, deck, hands, discardPile, numDraws, activePlayer, activeSuit, seven_streak):
        self.numPlayers = numPlayers
        #self.initHandSize = initHandSize
        self.deck = deck
        self.hands = hands
        self.discardPile = discardPile
        self.numDraws = numDraws
        self.activePlayer = activePlayer
        self.activeSuit = activeSuit
        self.seven_streak = seven_streak

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
                self.activeSuit,
                self.seven_streak]

    def playerDrawsCard(self, player):
        # TODO: shuffle when deck is empty
        card, self.deck = drawCardFromDeck(self.deck)
        self.hands[player].append(card)

    def playerPlaysCard(self, player, card, activeSuit):
        self.hands[player].remove(card)
        self.discardPile.append(card)
        if(card % 13 == 0):
            self.activeSuit == activeSuit
        
        
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
    tableState = TableState(numPlayers, deck, hands, discardPile, numDraws, 0, 0, 0)
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
    print "before server connect"
    server.connect(host, 12345)
    print "after server connect"
    server.accepting_allow()
    '''
    for conn_count in range(numPlayers):
        remaining = numPlayers-conn_count
        print('Waiting for ', remaining, ' more connections')
        c, addr = s.accept()     # Establish connection with client.
        print('Got connection from', addr)
        connections.append([c, addr])
    
    while numConnections < numPlayers:
        pass
    
    print("All players connected!")
    for conn_index in range(numPlayers):
        serialized_abstract_state = json.dumps(tableState.abstractState(conn_index))
        print serialized_abstract_state
        connections[conn_index].socket.send([serialized_abstract_state])
    
    print("All hands sent")
    
    while True:
        print("Waiting for player action")
        action_string = connections[tableState.activePlayer].socket.recv(128)
        action = json.loads(action_string)
        print("Received player action ", action)
        actionType = action[0]
        card = action[1]
        activeSuit = action[2]
        
        if actionType == ACTION_DRAW:
            #card, deck = drawCardFromDeck(deck)
            tableState.playerDrawsCard(tableState.activePlayer)
        elif actionType == ACTION_PASS:
            tableState.activePlayer = (tableState.activePlayer+1)%numPlayers
        elif actionType == ACTION_PLAY:
            tableState.playerPlaysCard(activePlayer, card, activeSuit)
            tableState.activePlayer = (tableState.activePlayer+1)%numPlayers

        for conn_index in range(numPlayers):
            serialized_abstract_state = json.dumps(tableState.abstractState(conn_index))
            connections[conn_index].socket.send(serialized_abstract_state)
        
        #c.send('Thank you for connecting')
        #c.close()                # Close the connection
    '''

# naive implementation of draw.
# TODO: if deck is empty, reshuffle discard pile into deck
def drawCardFromDeck(deck):
    return deck[0], deck[1:]
    
if __name__ == "__main__":
    main(sys.argv)
