import pygame
import random
import os
import time
import neat
import visualize
import pickle

pygame.font.init()  # Init font in pygame
pygame.mixer.init() # Init Mixer in pygame

# Setting constants
WIN_WIDTH = 600
WIN_HEIGHT = 800
FLOOR = 730
STAT_FONT = pygame.font.SysFont(os.path.join('assets/font', 'flappy_bird.ttf'), 50)
END_FONT = pygame.font.SysFont(os.path.join('assets/font', 'flappy_bird.ttf'), 70)
DRAW_LINES = False

# Creating Window and Setting Title
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

# Loading assets
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets/images", "pipe.png")).convert_alpha())
BG_IMG = pygame.transform.scale(pygame.image.load(os.path.join("assets/images", "bg.png")).convert_alpha(), (600, 900))
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("assets/images", "bird" + str(x) + ".png"))) for x in range(1, 4)]
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets/images", "base.png")).convert_alpha())

JMP_SOUND = pygame.mixer.Sound(os.path.join('assets/audio', 'wing.wav'))
POINT_SOUND = pygame.mixer.Sound(os.path.join('assets/audio', 'point.wav'))
DEATH_SOUND = pygame.mixer.Sound(os.path.join('assets/audio', 'die.wav'))

#Generation Count (will be printed)
gen = 0


class Bird:
    
    MAX_ROTATION = 25   # For the rotation of bird, when moving up or down
    IMGS = BIRD_IMGS    # All of the images of the bird (different orientations)
    ROT_VEL = 20        # How much rotation on each jump/fall
    ANIMATION_TIME = 5  # How much the bird moves as the animation progresses

    def __init__(self, x, y):
        
        self.x = x
        self.y = y
        self.tilt = 0  # Degrees to tilt
        self.tick_count = 0 # Needed or physics, to make it smooth each frame
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):

        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):

        self.tick_count += 1

        # for downward acceleration
        displacement = self.vel*(self.tick_count) + 0.5 * \
            (3)*(self.tick_count)**2  # calculate displacement

        # terminal velocity
        if displacement >= 16:
            displacement = (displacement/abs(displacement)) * 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:  # tilt up
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:  # tilt down
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        
        self.img_count += 1

        # For animation of bird, loop through three images
        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # so when bird is nose diving it isn't flapping
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        # tilt the bird
        blitRotateCenter(win, self.img, (self.x, self.y), self.tilt)

    def get_mask(self):
        
        return pygame.mask.from_surface(self.img)


class Pipe():
    
    GAP = 200
    VEL = 5

    def __init__(self, x):
        
        self.x = x
        self.height = 0

        # where the top and bottom of the pipe is
        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False

        self.set_height()

    def set_height(self):
        
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        
        self.x -= self.VEL

    def draw(self, win):
        
        # draw top
        win.blit(self.PIPE_TOP, (self.x, self.top))
        # draw bottom
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird, win):
       
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if b_point or t_point:
            return True

        return False


class Base:
    
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
       
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def blitRotateCenter(surf, image, topleft, angle):
   
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(
        center=image.get_rect(topleft=topleft).center)

    surf.blit(rotated_image, new_rect.topleft)


def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
   
    if gen == 0:
        gen = 1
    win.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        # draw lines from bird to pipe
        if DRAW_LINES:
            try:
                pygame.draw.line(win, (255, 0, 0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height(
                )/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width()/2, pipes[pipe_ind].height), 5)
                pygame.draw.line(win, (255, 0, 0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height(
                )/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom), 5)
            except:
                pass
        # draw bird
        bird.draw(win)

    # score
    score_label = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))

    # generations
    score_label = STAT_FONT.render("Gens: " + str(gen-1), 1, (255, 255, 255))
    win.blit(score_label, (10, 10))

    # alive
    score_label = STAT_FONT.render(
        "Alive: " + str(len(birds)), 1, (255, 255, 255))
    win.blit(score_label, (10, 50))

    pygame.display.update()


# Default structure of the function that is provided to neat lib
def evaluation(genomes, config):
   
    global WIN, gen
    win = WIN
    gen += 1

    # Start by creating lists holding the genome itself, the
    # Neural network associated with the genome and the
    # Bird object that uses that network to play
    nets = []
    birds = []
    ge = []
    # Init the lists
    for genome_id, genome in genomes:
        genome.fitness = 0  # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        ge.append(genome)

    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0

    #needed for frame count
    clock = pygame.time.Clock()

    run = True
    while run and len(birds) > 0:
        clock.tick(30) # Can be changed to make game run faster

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        pipe_ind = 0
        if len(birds) > 0:
            # Checking whether to use the first or second...
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                # ...pipe on the screen for neural network input
                pipe_ind = 1

        # Give each bird a fitness of 0.1 for each frame it stays alive
        for x, bird in enumerate(birds):
            ge[x].fitness += 0.1
            bird.move()

            # Sending bird location, top pipe location and bottom pipe location and determine from network whether to jump or not (uses the activation function and NN)
            output = nets[birds.index(bird)].activate((bird.y, abs(
                bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            # Using a tanh activation function so result will be between -1 and 1. if over 0.5 jump
            if output[0] > 0.5:
                pygame.mixer.Sound.play(JMP_SOUND)
                pygame.mixer.music.stop()
                bird.jump()

        # Moving the ground as well
        base.move()

        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            # Checks if any bird in the list collides wih any pipe
            for bird in birds:
                # ...if it does, decrease fitness by 1 and remove the bird
                if pipe.collide(bird, win):
                    pygame.mixer.Sound.play(DEATH_SOUND)
                    pygame.mixer.music.stop()
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

            # Pipe out of screen, then remove it from list
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            # If bird has passed the current pipe, then, set flags to true
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

        # Add 5 to the fitness of every genome that passed the pipe and increase score by 1
        if add_pipe:
            score += 1
            pygame.mixer.Sound.play(POINT_SOUND)
            pygame.mixer.music.stop()
            for genome in ge:
                genome.fitness += 5
            pipes.append(Pipe(WIN_WIDTH))

        for r in rem:
            pipes.remove(r)

        # if bird hits the ground, remove it
        for bird in birds:
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                pygame.mixer.Sound.play(DEATH_SOUND)
                pygame.mixer.music.stop()
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))

        draw_window(WIN, birds, pipes, base, score, gen, pipe_ind)

        # break if score gets large enough
        if score > 20:
            pickle.dump(nets[0],open("best.pickle", "wb"))
            break


def run():

    # Loading the config file needed to initialize neat-python...
    # ...contains fitness limit, population size, activation function etc
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                os.path.join(os.path.dirname(__file__), 'config-feedforward.txt'))

    # Create the population, based on the config provided
    p = neat.Population(config)

    # This allows the neat-python package to output generation by generation details on the console
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Max number of generations to run this trainer for (50 here) along with the eval func
    winner = p.run(evaluation, 50)

    # Gives the final output of the best genome produced
    print('\nBest Genome:\n{!s}'.format(winner))


if __name__ == '__main__':
    run()
