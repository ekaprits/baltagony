#!/usr/bin/python

import sys, socket, pickle
import pygame
from pygame.locals import *

suits = ['c', 'd', 'h', 's']
facecards = ['j', 'q', 'k']
def main(argv):
    arg_len = len(sys.argv)
    if arg_len < 3:
        print("usage: client.py <server IP> <serverPort>")
        sys.exit(2)
    serverIP = socket.gethostname()
    serverPort = int(sys.argv[2])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((serverIP, serverPort))
    hand_string = s.recv(512)
    hand = pickle.loads(hand_string)
    print(hand)
    myindex = hand[0]
    #print("myindex = ", myindex)
    myhand = hand[3][myindex]
    #print("myhand is ", myhand)
    
    
    pygame.init()
    screen = pygame.display.set_mode((1024, 768), DOUBLEBUF)
    pygame.display.set_caption("Baltagony")
    printMyHand(screen, myhand, 50, 50)
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.update()

def printMyHand(screen, hand, x, y):
    offset = 0
    for card in hand:
        imageFile = getFilenameFromCardNumber(card)
        myvar = pygame.image.load('..\\media\\cards_gif\\'+imageFile)
        screen.blit(myvar, (x+offset,y))
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
