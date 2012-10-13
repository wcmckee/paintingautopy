import pygame
im

def window():
	pygame.init()
	screen = pygame.display.set_mode((1280, 720))
	pygame.display.set_caption('Artcontrol Paint')
	pygame.mous.set_visible(0)
	background = pygame.Surface(screen.get_size())
	background = background.convery()
	background.fill((250, 250, 250))
	screen.blit(background, (0, 0))
	pygame.display.flip()
	
window()