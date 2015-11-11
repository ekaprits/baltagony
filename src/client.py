#!/usr/bin/python

import sys, socket, pickle
import pygame
from pygame.locals import *

suits = ['c', 'd', 'h', 's']
facecards = ['j', 'q', 'k']
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

def main(argv):
    arg_len = len(sys.argv)
    if arg_len < 3:
        print("usage: client.py <server IP> <serverPort>")
        sys.exit(2)
    
    serverIP = socket.gethostname()
    serverPort = int(sys.argv[2])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((serverIP, serverPort))
    hands_string = s.recv(512)
    hands = pickle.loads(hands_string)
    print(hands)
    myIndex = hands[0]
    #print("myindex = ", myindex)
    allhands = hands[3]
    discardPile = hands[4]
    #myhand = hands[3][myindex]
    #print("myhand is ", myhand)
    
    
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF)
    pygame.display.set_caption("Baltagony")
    printAllHands(screen, allhands, myIndex)
    printDiscardPile(screen, discardPile) 
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.update()

def printDiscardPile(screen, discardPile):
    cardOnTop = discardPile[-1:][0]
    imageFile = getFilenameFromCardNumber(cardOnTop)
    myvar = pygame.image.load('..\\media\\cards_gif\\'+imageFile)
    init_x = (WINDOW_WIDTH-71)/2
    init_y = (WINDOW_HEIGHT-96)/2
    screen.blit(myvar, (init_x,init_y))

def printAllHands(screen, hands, myIndex):
    printMyHand(screen, hands[myIndex])
    
    for i in range(len(hands)-1):
        offset = 0
        nextIndex = (myIndex + 1 + i) % len(hands)
        numCards = hands[nextIndex]
        cardBack = pygame.image.load('..\\media\\cards_gif\\b1fv.gif')
        estimated_width = 71 + (numCards*25)
        height = 96
        if i == 0:
            init_x =(3*WINDOW_WIDTH/4)-(estimated_width/2)
            init_y = WINDOW_HEIGHT/2 - 96/2
        elif i == 1:
            init_x =(WINDOW_WIDTH - estimated_width)/2
            init_y = WINDOW_HEIGHT - 50 - 96
        elif i == 2:
            init_x =(WINDOW_WIDTH/4)-(estimated_width/2)
            init_y = WINDOW_HEIGHT/2 - 96/2
            
        for j in range(numCards):
            screen.blit(cardBack, (init_x+offset,init_y))
            offset += 25
            
def printMyHand(screen, hand):
    estimated_width = 71 + (len(hand)*25)
    init_x =(WINDOW_WIDTH-estimated_width)/2
    init_y = 50
    offset = 0
    for card in hand:
        imageFile = getFilenameFromCardNumber(card)
        myvar = pygame.image.load('..\\media\\cards_gif\\'+imageFile)
        screen.blit(myvar, (init_x+offset,init_y))
        offset += 25
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
