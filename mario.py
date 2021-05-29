#Authors:
#Franco Minutti Simoni - A01733927
#Alan Mondragón Rivas - A01734565
#Created 20 May, 2021
#The game moves Mario across the surface.
#The fist is controlled using a matrix keyboard with an arduino using serial communication.
#The objective of the game is to hit Mario that is an image of 56x56 pixels, with a fist that with the same dimensions.
#It displays a table of points and a timer. #The game lasts 2 minutes and every 20 seconds the movement speed of Mario increases.
#The user gets 10 points for each time he hits Mario and loses 20 if he does not hit it.

#Import Modules
import os, pygame
from pygame.locals import *
from pygame.compat import geterror
import serial
from pygame import mixer
import random

pygame.mixer.init()
if not pygame.font: print ('Warning, fonts disabled')
if not pygame.mixer: print ('Warning, sound disabled')

main_dir = os.path.split(os.path.abspath(__file__))[0]
#Change directory depending on the PC
data_dir = os.path.join(main_dir, 'C:/Users/E5570/Documents/Tec/4to semestre/Sistemas de chip/Interfaces Python/PyGame')
#Global variables for image location and serial port
x = 0
y = 0
ser =  serial.Serial('COM6',baudrate=9600, timeout=0.005)
#functions to create our resources
def load_image(name, colorkey=None):
    fullname = os.path.join(data_dir, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print ('Cannot load image:', fullname)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

#classes for our game objects
class Fist(pygame.sprite.Sprite):
    """moves a clenched fist on the screen, following the mouse"""
    def __init__(self):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image, self.rect = load_image('fist.bmp', -1)
        self.punching = 0
    #Udates the coordinates of the Fist
    def update(self):
        global x,y
        "move the fist based on the mouse position"

        pos = (x,y)
        self.rect.midtop = pos
        if self.punching:
            self.rect.move_ip(5, 10)

    def punch(self, target):
        "returns true if the fist collides with the target"
        if not self.punching:
            self.punching = 1
            hitbox = self.rect.inflate(-5, -5)
            return hitbox.colliderect(target.rect)

    def unpunch(self):
        "called to pull the fist back"
        self.punching = 0


class Chimp(pygame.sprite.Sprite):
    """moves a monkey critter across the screen. it can spin the
       monkey when it is punched."""
    def __init__(self):
        pygame.sprite.Sprite.__init__(self) #call Sprite intializer
        self.image, self.rect = load_image('mario.jpg', -1)#Takes the Image of the Character
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect.topleft = 10, 10
        self.move = 10
        self.y = 4
        self.dizzy = 0

    #The character spins
    def update(self):
        "walk or spin, depending on the monkeys state"

        if self.dizzy:
            self._spin()
        else:
            self._walk()
    #Makes the character move all arround the window
    def _walk(self):
        "move the monkey across the screen, and turn at the ends"
        newpos = self.rect.move((self.move, self.y))
        if self.rect.left < self.area.left or self.rect.right > self.area.right:
            self.move = -self.move
            newpos = self.rect.move((self.move, self.y))
            self.image = pygame.transform.flip(self.image, 1, 0)
        if self.rect.top < self.area.top or self.rect.bottom > self.area.bottom:
            self.y = -self.y
            newpos = self.rect.move((self.move, self.y))
        self.rect = newpos

    def _spin(self):
        "spin the monkey image"
        center = self.rect.center
        self.dizzy = self.dizzy + 12
        if self.dizzy >= 360:
            self.dizzy = 0
            self.image = self.original
        else:
            rotate = pygame.transform.rotate
            self.image = rotate(self.original, self.dizzy)
        self.rect = self.image.get_rect(center=center)

    def punched(self):
        "this will cause the monkey to start spinning"
        if not self.dizzy:
            self.dizzy = 1
            self.original = self.image
    #Increases the character speed
    def moreSpeed(self):

        if (self.move < 0):
            self.move = ((-self.move) + 5)*-1
        else:
            self.move += 5


def main():
    """this function is called when the program starts.
       it initializes everything it needs, then runs in
       a loop until the function returns."""
#Initialize Everything
    pygame.init()
    screen = pygame.display.set_mode((480, 320))
    pygame.display.set_caption('TE2003')
    pygame.mouse.set_visible(0)
    pygame.mixer.music.load("super-electronicas-mario-bros-mix-2018.mp3")
    pygame.mixer.music.play()

#Create The Backgound
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((250, 250, 250))

#Put Text On The Background, Centered
    if pygame.font:
        font = pygame.font.Font(None, 36)
        text = font.render("TE2003 Embebidos avanzados", 1, (10, 10, 10))
        textpos = text.get_rect(centerx=background.get_width()/2)
        background.blit(text, textpos)

#Display The Background
    screen.blit(background, (0, 0))
    pygame.display.flip()

#Prepare Game Objects
    clock = pygame.time.Clock()
    global ser,x,y
    whiff_sound = pygame.mixer.Sound('bump.wav')
    punch_sound = pygame.mixer.Sound('kick.wav')
    end_plus_sound = pygame.mixer.Sound('stage_clear.wav')
    end_min_sound = pygame.mixer.Sound('gameover.wav')

    chimp = Chimp()
    fist = Fist()
    allsprites = pygame.sprite.RenderPlain((fist, chimp))


    ser.flush()
#Main Loop
    going = True
    points = 0
    # Used to manage how fast the screen updates and our timer
    reloj = pygame.time.Clock()
    # This is the font that we will use for the text that will appear on the screen (size 25)
    fuente = pygame.font.Font(None, 25)
    #Initializes the timer variables
    numero_de_fotogramas = 0
    tasa_fotogramas = 20
    instante_de_partida = 120
    #Sets the colors
    NEGRO = (0, 0, 0)
    BLANCO = (255, 255, 255)
    tmp = 40
    while going:
        clock.tick(60)
        #Handle Input Events
        for event in pygame.event.get():
            if event.type == QUIT:
                going = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                going = False
        #Reads the serial port
        line = ser.readline().decode('utf-8').rstrip()
        if line == "5":
            #Punch action
            if fist.punch(chimp):
                punch_sound.play() #punch
                chimp.punched()
                points += 10
            else:
                whiff_sound.play() #miss
                points -= 20
            pygame.time.delay(100)
            fist.unpunch()
        #Moves the fist depending on the key pressed on the xX axis
        if line == "6":
            x+=10

        if line == "4":
            x-=10
        #Moves the fist depending on the key pressed on the Y axis
        if line == "8":
            y+=10
        if line == "2":
            y-=10
        #The timer initializes
        segundos_totales = instante_de_partida - (numero_de_fotogramas // tasa_fotogramas)
        if segundos_totales < 0:
            segundos_totales = 0

        # We divide by 60 to get the total minutes
        minutos = segundos_totales // 60

        # We use the module to obtain the seconds
        segundos = segundos_totales % 60

        # We use the text string format to format leading zeros
        texto_de_salida = "Time left: {0:02}:{1:02}".format(minutos, segundos)
        if tmp < 0:
            tmp = 40
        #Increments the speed every 20 seconds
        if ((segundos == 0 or segundos == 20 or segundos == 40) and segundos == tmp):
                tmp -= 20
                chimp.moreSpeed()


        #initializes when the time is up
        if texto_de_salida == "Time left: 00:00":
            going = False
            pygame.mixer.music.pause()
            screen.fill(NEGRO)
            #Determines if the user had won
            if points <= 0:
                mens = fuente.render("You Lose", True, BLANCO)
                screen.blit(mens, [170, 150])
                pygame.display.flip()
                end_min_sound.play()
                pygame.time.delay(4500)
            elif points >= 10:
                mens = fuente.render("You Win", True, BLANCO)
                screen.blit(mens, [170, 150])
                pygame.display.flip()
                end_plus_sound.play()
                pygame.time.delay(6000)

        # Refresh the timer
        texto = fuente.render(texto_de_salida, True, NEGRO)

        allsprites.update()

        #Draw Everything
        screen.blit(background, (0, 0))
        screen.blit(texto, [170, 300])
        screen.blit(font.render(str(points), True, (0, 0, 0)), (32, 48))
        allsprites.draw(screen)
        pygame.display.flip()
        numero_de_fotogramas += 1

        # Set the limit to 20 frames
        reloj.tick(20)

    pygame.quit()

#Game Over


#this calls the 'main' function when this script is executed
if __name__ == '__main__':
    main()
