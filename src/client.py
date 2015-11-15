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
MARGIN_GAP = 50
PASS_BUTTON_GAP = 30
hand_rect = pygame.Rect((0,0),(0,0))
deck_rect = pygame.Rect(((WINDOW_WIDTH/2)-CARD_WIDTH-DECK_DISCARD_GAP,(WINDOW_HEIGHT-CARD_HEIGHT)/2),(CARD_WIDTH,CARD_HEIGHT))
pass_rect = pygame.Rect((WINDOW_WIDTH/2-30, MARGIN_GAP+CARD_HEIGHT+PASS_BUTTON_GAP), (60, 30))
ace_rect = pygame.Rect((WINDOW_WIDTH/2-262,WINDOW_HEIGHT/2-75),(525, 150))
win_rect = pygame.Rect((WINDOW_WIDTH/2-100,WINDOW_HEIGHT/2-150),(200, 50))
seven_rect = pygame.Rect(((WINDOW_WIDTH-CARD_WIDTH)/2,MARGIN_GAP+CARD_HEIGHT+PASS_BUTTON_GAP),(CARD_WIDTH,CARD_HEIGHT))

cTS = None
client_timeout_connect = 50.0
client_timeout_receive = 100.0
showAcePopup = False
tempAceCard = 0
showSevenPopup = False
tempSevenChoice = 0

class ClientTableState:
    def __init__(self, myIndex, numPlayers, deckSize,
                 hands, discardPile, numDraws,
                 activePlayer, forcedSuit, seven_streak, win_status):
        self.myIndex = myIndex
        self.numPlayers = numPlayers
        self.deckSize = deckSize
        self.hands = hands
        self.discardPile = discardPile
        self.numDraws = numDraws
        self.activePlayer = activePlayer
        self.forcedSuit = forcedSuit
        self.seven_streak = seven_streak
        self.win_status = win_status
        
def readStateFromServer(client, blocking=True):
    global cTS
    state_string = client.receive(blocking)
    if state_string == None:
        return False
    print "received: ", state_string
    state = json.loads(state_string)
    cTS = ClientTableState(state[0], state[1], state[2],
                            state[3], state[4], state[5],
                            state[6], state[7], state[8], state[9])
    print "Just read state = ", state
    print "cTS.activePlayer = ", cTS.activePlayer
    print "cTS.myIndex = ", cTS.myIndex
    if (cTS.activePlayer == cTS.myIndex):
        pygame.display.set_caption("Baltagony (active)")
    else:
        pygame.display.set_caption("Baltagony (inactive)")
    return True

#def recvloop(sock):
#    while True:
#        readStateFromServer(sock)
    
def main(argv):
    global cTS, showAcePopup, tempAceCard
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
                if cTS.win_status >= 0:
                    continue
                if cTS.activePlayer != cTS.myIndex:
                    print "Not active player, ignoring click"
                    continue
                pos = event.pos
                print("Mouse click at position ", pos)
                print deck_rect
                if (not showAcePopup) and deck_rect.collidepoint(pos):
                    print "Clicked deck"
                    if cTS.numDraws[cTS.activePlayer] < 2:
                        if cTS.seven_streak == 0:
                            lst = [0,0,0]
                        else:
                            lst = [3,0,0]
                        send_string = json.dumps(lst)
                        client.send(send_string)
                        readStateFromServer(client, True)
                    else:
                        print "You can't draw any more. You must play or pass"
                elif (not showAcePopup) and (cTS.seven_streak==0) and pass_rect.collidepoint(pos):
                    print "Clicked pass"
                    if cTS.numDraws[cTS.activePlayer] == 2:
                        lst = [1,0,0]
                        send_string = json.dumps(lst)
                        client.send(send_string)
                        readStateFromServer(client, True)
                    else:
                        print "You can't pass yet."
                elif (not showAcePopup) and hand_rect.collidepoint(pos):
                    print "Clicked hand"
                    card_index = (pos[0]-hand_rect.left)/CARD_GAP
                    if card_index > len(cTS.hands[cTS.activePlayer])-1:
                        card_index = len(cTS.hands[cTS.activePlayer])-1
                    hand = cTS.hands[cTS.activePlayer]
                    norm_hand = map(normalizeCard, hand)
                    norm_hand.sort()
                    card = norm_hand[card_index]
                    cardOnTop = cTS.discardPile[-1:][0]
                    if isPlayableCard(card, cardOnTop, cTS.forcedSuit, cTS.seven_streak):
                        print "You played index = ", card_index, " card = ", cardToString(card)
                        if card % 13 > 0:   #not an ace
                            print "Not an ace"
                            lst = [2,card,-1]
                            send_string = json.dumps(lst)
                            client.send(send_string)
                            print "Sent and waiting to hear from server"
                            readStateFromServer(client, True)
                            print "read state from server"
                        else:
                            showAcePopup = True
                            tempAceCard = card
                    else:
                        print "You can't play this card! (", cardToString(card), ")"
                elif showAcePopup and ace_rect.collidepoint(pos):
                    print "You clicked the Ace popup"
                    suit = (pos[0]-ace_rect.left)/(ace_rect.width/4)
                    print "suit = ", suit
                    lst = [2,tempAceCard,suit]
                    showAcePopup = False
                    send_string = json.dumps(lst)
                    client.send(send_string)
                    readStateFromServer(client, True)

                        
        # print("Updating screen")
        draw(screen)
        existsNewState = False

def draw(screen):
    global cTS, showAcePopup
    screen.fill((255,255,255))
    printAllHands(screen, cTS)
    printDiscardPile(screen, cTS.discardPile)
    printDeck(screen, cTS.deckSize)
    if cTS.win_status >= 0:
        printWin(screen, cTS.win_status)
        
    if cTS.activePlayer == cTS.myIndex and cTS.numDraws[cTS.myIndex] == 2:
        printPassButton(screen)
    if showAcePopup:
        printShowAcePopup(screen)
    if cTS.activePlayer == cTS.myIndex and cTS.seven_streak > 0:
        printShowSevenPopup(screen, cTS.seven_streak)
    if (cTS.activePlayer == cTS.myIndex):
        caption = "Baltagony - Player %d (active)" % (cTS.myIndex+1)
    else:
        caption = "Baltagony - Player %d (inactive)" % (cTS.myIndex+1)
    pygame.display.set_caption(caption)
    pygame.display.update()

def printShowSevenPopup(screen, seven_streak):
    global deck_rect
    darkgray = (180, 180, 180)
    #deck = pygame.image.load('..\\media\\cards_gif\\b1fv.gif')
    #pygame.draw.rect(screen, (0,0,0), seven_rect, 1)
    #screen.blit(deck, (seven_rect.left,seven_rect.top))
    sevenfont = pygame.font.SysFont("Helvetica", 13)
    numCardsToDraw = 2*seven_streak
    string1 = "Draw "+str(numCardsToDraw)
    string2 = "cards"
    grayrect = pygame.Rect((deck_rect.left+10, deck_rect.top+30),(deck_rect.width-20,deck_rect.height-60))
    gray = (200, 200, 200)
    pygame.draw.rect(screen, gray, grayrect, 0)
    pygame.draw.rect(screen, (0,0,0), grayrect, 1)
    
    label1 = sevenfont.render(string1, 1, (0,0,0))
    label2 = sevenfont.render(string2, 1, (0,0,0))
    screen.blit(label1, (deck_rect.left+14, deck_rect.top+33))
    screen.blit(label2, (deck_rect.left+17, deck_rect.top+48))
    
def printShowAcePopup(screen):
    global ace_rect
    darkgray = (180, 180, 180)
    pygame.draw.rect(screen, darkgray, ace_rect, 0)
    pygame.draw.rect(screen, (0,0,0), ace_rect, 1)
    suits = pygame.image.load('..\\media\\cards_gif\\suits.png')
    screen.blit(suits, (ace_rect.left+25,ace_rect.top+25), (100,100,100,100))
    screen.blit(suits, (ace_rect.left+150,ace_rect.top+25), (0,100,100,100))
    screen.blit(suits, (ace_rect.left+275,ace_rect.top+25), (100,0,100,100))
    screen.blit(suits, (ace_rect.left+400,ace_rect.top+25), (0,0,100,100))
    
def printPassButton(screen):
    global pass_rect
    gray = (200, 200, 200)
    pygame.draw.rect(screen, gray, pass_rect, 0)
    pygame.draw.rect(screen, (0,0,0), pass_rect, 1)
    passfont = pygame.font.SysFont("Helvetica", 15)
    label = passfont.render("Pass", 1, (0,0,0))
    screen.blit(label, (pass_rect.left+13, pass_rect.top+6))
    
def printDeck(screen, deckSize):
    global deck_rect
    pygame.draw.rect(screen, (0,0,0), deck_rect, 1)
    
    deck = pygame.image.load('..\\media\\cards_gif\\b1fv.gif')
    #init_x = (WINDOW_WIDTH/2)-CARD_WIDTH-DECK_DISCARD_GAP
    #init_y = (WINDOW_HEIGHT-CARD_HEIGHT)/2
    #deck_rect = pygame.Rect((init_x,init_y),(CARD_WIDTH,CARD_HEIGHT))
    screen.blit(deck, (deck_rect.left,deck_rect.top))
        

def printWin(screen, win_status):
    global win_rect
    darkgray = (180, 180, 180)
    pygame.draw.rect(screen, darkgray, win_rect, 0)
    pygame.draw.rect(screen, (0,0,0), win_rect, 1)
    winfont = pygame.font.SysFont("Helvetica", 22)
    winstring = "Player %d wins!" % (win_status+1)
    label = winfont.render(winstring, 1, (0,0,0))
    screen.blit(label, (win_rect.left+30, win_rect.top+12))
    
def printDiscardPile(screen, discardPile):
    cardOnTop = discardPile[-1:][0]
    imageFile = getFilenameFromCardNumber(cardOnTop)
    image = pygame.image.load('..\\media\\cards_gif\\'+imageFile)
    init_x = (WINDOW_WIDTH/2)+DECK_DISCARD_GAP
    init_y = (WINDOW_HEIGHT-CARD_HEIGHT)/2
    screen.blit(image, (init_x,init_y))

def printAllHands(screen, cTS):
    hands = cTS.hands
    myIndex = cTS.myIndex
    forcedSuit = cTS.forcedSuit
    discardPile = cTS.discardPile
    activePlayer = cTS.activePlayer
    seven_streak = cTS.seven_streak
    printMyHand(screen, hands[myIndex], discardPile, forcedSuit, myIndex, activePlayer, seven_streak)
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
            
def printMyHand(screen, hand, discardPile, forcedSuit, myIndex, activePlayer, seven_streak):
    global hand_rect
    estimated_width = CARD_WIDTH + ((len(hand)-1)*CARD_GAP)
    init_x =(WINDOW_WIDTH-estimated_width)/2
    init_y = 50
    hand_rect = pygame.Rect((init_x, init_y),(estimated_width,CARD_HEIGHT))
    #pygame.draw.rect(screen, (0,0,0), hand_rect, 2)
    offset = 0
    #print hand
    cardOnTop = discardPile[-1:][0]
    norm_hand = [None]*len(hand)
    for i in range(len(hand)):
        norm_hand[i] = hand[i]%52
    #print norm_hand
    norm_hand.sort()
    #print norm_hand
    for card in norm_hand:
        #print "card = ", card
        isPlayable = isPlayableCard(card, cardOnTop, forcedSuit, seven_streak) and myIndex == activePlayer
        imageFile = getFilenameFromCardNumber(card,isPlayable)
        myvar = pygame.image.load('..\\media\\cards_gif\\'+imageFile)
        screen.blit(myvar, (init_x+offset,init_y))
        offset += CARD_GAP
        #print(imageFile)
        
def isPlayableCard(card, cardOnTop, forcedSuit, seven_streak):
    cardSuit = (card % 52)/13
    cardNumber = card % 13
    cardOnTopSuit = (cardOnTop % 52)/13
    cardOnTopNumber = cardOnTop % 13
    if forcedSuit < 0 and cardOnTopNumber == 0: # this means an Ace as a starting discard
        return cardNumber != 0
    elif seven_streak > 0: # only sevens are playable
        return cardNumber == 6
    elif forcedSuit >= 0:   # an Ace played during game
        return cardNumber != 0 and cardSuit == forcedSuit
    else:                   # no Ace on top
        return cardNumber == cardOnTopNumber or cardSuit == cardOnTopSuit or cardNumber == 0

def getFilenameFromCardNumber(card, isPlayable=True):
    suit = suits[int(card%52/13)]
    number = card % 13
    if number > 9:
        strnumber = facecards[number - 10]
    else:
        strnumber = str(number+1)
    if isPlayable:
        dark = ""
    else:
        dark = "_dark"
    return suit + strnumber + dark + ".gif"

def normalizeCard(card):
    return card % 52

def cardToString(card):
    global suits
    norm_card = normalizeCard(card)
    norm_cardNum = str(norm_card % 13)
    norm_cardSuit = suits[(norm_card / 13)]
    return norm_cardNum+norm_cardSuit
    
if __name__ == "__main__":
    main(sys.argv)
