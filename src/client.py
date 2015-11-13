#!/usr/bin/python

import sys, socket, json, thread
import pygame
from pygame.locals import *
from Mastermind import *

suits = ['c', 'd', 'h', 's']
facecards = ['j', 'q', 'k']
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
CARD_WIDTH = 71
CARD_HEIGHT = 96
DECK_DISCARD_GAP = 20
CARD_GAP = 20
hand_rect = pygame.Rect((0,0),(0,0))
deck_rect = pygame.Rect((0,0),(0,0))
cTS = None
client_timeout_connect = 5.0
client_timeout_receive = 10.0

class ClientTableState:
    def __init__(self, myIndex, numPlayers, deckSize, hands, discardPile, numDraws, activePlayer, activeSuit, seven_streak):
        self.myIndex = myIndex
        self.numPlayers = numPlayers
        self.deckSize = deckSize
        self.hands = hands
        self.discardPile = discardPile
        self.numDraws = numDraws
        self.activePlayer = activePlayer
        self.activeSuit = activeSuit
        self.seven_streak = seven_streak
        
def readStateFromServer(client, blocking=True):
    global cTS
    state_string = client.receive(blocking)
    if state_string == None:
        return False
    state = json.loads(state_string)
    cTS = ClientTableState(state[0], state[1], state[2],
                            state[3], state[4], state[5],
                            state[6], state[7], state[8])
    if (cTS.activePlayer == cTS.myIndex):
        pygame.display.set_caption("Baltagony (active)")
    else:
        pygame.display.set_caption("Baltagony (inactive)")
    return True

#def recvloop(sock):
#    while True:
#        readStateFromServer(sock)
    
def main(argv):
    global cTS
    arg_len = len(sys.argv)
    if arg_len < 3:
        print("usage: client.py <server IP> <serverPort>")
        sys.exit(2)
    
    serverIP = socket.gethostname()
    serverPort = int(sys.argv[2])
    #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.connect((serverIP, serverPort))
    client = MastermindClientTCP(client_timeout_connect,client_timeout_receive)
    client.connect(serverIP, serverPort)
    #data = client.receive()
    readStateFromServer(client)
    
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF)
    pygame.display.set_caption("Baltagony")
    #printAllHands(screen, allhands, myIndex)
    #printDiscardPile(screen, discardPile)
    #printDeck(screen, deckSize)
    draw(screen)
    #thread.start_new_thread(recvloop, (s, ))
        
    while True:
        existsNewState = True
        if cTS.activePlayer != cTS.myIndex:
            existsNewState = readStateFromServer(client, False)
                
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEBUTTONUP:
                pos = event.pos
                print("Mouse click at position ", pos)
                print deck_rect
                if deck_rect.collidepoint(pos):
                    print "Clicked deck"
                    lst = [0,0,0]
                    send_string = json.dumps(lst)
                    client.send(send_string)
                    
                elif hand_rect.collidepoint(pos):
                    print "Clicked hand"

        # print("Updating screen")
        draw(screen)
        existsNewState = False

def draw(screen):
    global cTS
    screen.fill((255,255,255))
    printAllHands(screen, cTS.hands, cTS.myIndex)
    printDiscardPile(screen, cTS.discardPile)
    printDeck(screen, cTS.deckSize)
    pygame.display.update()
    
def printDeck(screen, deckSize):
    global deck_rect
    if (deckSize > 0):
        deck = pygame.image.load('..\\media\\cards_gif\\b1fv.gif')
        init_x = (WINDOW_WIDTH/2)-CARD_WIDTH-DECK_DISCARD_GAP
        init_y = (WINDOW_HEIGHT-CARD_HEIGHT)/2
        deck_rect = pygame.Rect((init_x,init_y),(init_x+CARD_WIDTH,init_y+CARD_HEIGHT))
        screen.blit(deck, (init_x,init_y))
    
def printDiscardPile(screen, discardPile):
    cardOnTop = discardPile[-1:][0]
    imageFile = getFilenameFromCardNumber(cardOnTop)
    image = pygame.image.load('..\\media\\cards_gif\\'+imageFile)
    init_x = (WINDOW_WIDTH/2)+DECK_DISCARD_GAP
    init_y = (WINDOW_HEIGHT-CARD_HEIGHT)/2
    screen.blit(image, (init_x,init_y))

def printAllHands(screen, hands, myIndex):
    printMyHand(screen, hands[myIndex])
    
    for i in range(len(hands)-1):
        offset = 0
        nextIndex = (myIndex + 1 + i) % len(hands)
        numCards = hands[nextIndex]
        cardBack = pygame.image.load('..\\media\\cards_gif\\b1fv.gif')
        estimated_width = CARD_WIDTH + (numCards*CARD_GAP)
        height = CARD_HEIGHT
        if i == 0:
            init_x =(3*WINDOW_WIDTH/4)-(estimated_width/2)
            init_y = WINDOW_HEIGHT/2 - CARD_HEIGHT/2
        elif i == 1:
            init_x =(WINDOW_WIDTH - estimated_width)/2
            init_y = WINDOW_HEIGHT - 50 - CARD_HEIGHT
        elif i == 2:
            init_x =(WINDOW_WIDTH/4)-(estimated_width/2)
            init_y = WINDOW_HEIGHT/2 - CARD_HEIGHT/2
            
        for j in range(numCards):
            screen.blit(cardBack, (init_x+offset,init_y))
            offset += CARD_GAP
            
def printMyHand(screen, hand):
    global hand_rect
    estimated_width = CARD_WIDTH + (len(hand)*CARD_GAP)
    init_x =(WINDOW_WIDTH-estimated_width)/2
    init_y = 50
    hand_rect = pygame.Rect((init_x, init_y),(init_x+estimated_width,init_y+CARD_WIDTH))
    offset = 0
    for card in hand:
        imageFile = getFilenameFromCardNumber(card)
        myvar = pygame.image.load('..\\media\\cards_gif\\'+imageFile)
        screen.blit(myvar, (init_x+offset,init_y))
        offset += CARD_GAP
        #print(imageFile)
        
        
def getFilenameFromCardNumber(card):
    suit = suits[int(card%52/13)]
    number = card % 13
    if number > 9:
        strnumber = facecards[number - 10]
    else:
        strnumber = str(number+1)
    return suit + strnumber + ".gif"

if __name__ == "__main__":
    main(sys.argv)
