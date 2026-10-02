import pygame
import random
import math
from array import array

# ============================================================
# INITIAL SETUP
# ============================================================

pygame.mixer.pre_init(
    frequency=22050,
    size=-16,
    channels=1,
    buffer=512
)
pygame.init()

# Window dimensions
WIDTH = 1200
HEIGHT = 700

# Create the window
screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.RESIZABLE
)

pygame.display.set_caption("Fireworks Show")

# Controls the frame rate
clock = pygame.time.Clock()

# ============================================================
# SOUND EFFECTS
# ============================================================

SAMPLE_RATE = 22050


def create_launch_sound():

    samples = array("h")
    phase = 0
    sample_count = int(SAMPLE_RATE * 0.32)

    for i in range(sample_count):

        progress = i / sample_count
        frequency = 350 + 1000 * progress
        phase += 2 * math.pi * frequency / SAMPLE_RATE
        envelope = (1 - progress) ** 1.5 * min(1, progress * 12)
        value = (
            math.sin(phase)
            + 0.25 * math.sin(phase * 2)
        ) * envelope * 0.35

        samples.append(int(value * 32767))

    return pygame.mixer.Sound(buffer=samples.tobytes())


def create_explosion_sound():

    samples = array("h")
    noise = random.Random(42)
    filtered_noise = 0
    phase = 0
    sample_count = int(SAMPLE_RATE * 0.6)

    for i in range(sample_count):

        progress = i / sample_count
        envelope = (1 - progress) ** 2.4
        filtered_noise = (
            filtered_noise * 0.72
            + noise.uniform(-1, 1) * 0.28
        )
        frequency = 90 - 45 * progress
        phase += 2 * math.pi * frequency / SAMPLE_RATE
        value = (
            filtered_noise * 0.8
            + math.sin(phase) * 0.7
        ) * envelope * 0.65

        samples.append(int(value * 32767))

    return pygame.mixer.Sound(buffer=samples.tobytes())


launch_sound = None
explosion_sound = None

if pygame.mixer.get_init() is not None:

    launch_sound = create_launch_sound()
    launch_sound.set_volume(0.35)

    explosion_sound = create_explosion_sound()
    explosion_sound.set_volume(0.5)

else:

    print("Audio is unavailable; fireworks will run without sound.")

# ============================================================
# COLORS
# ============================================================

BLACK = (2, 4, 15)

# Firework color palette
COLORS = [
    (255, 60, 60),       # Red
    (255, 120, 40),      # Orange
    (255, 220, 50),      # Yellow
    (80, 180, 255),      # Blue
    (100, 255, 150),     # Green
    (220, 80, 255),      # Purple
    (255, 100, 200),     # Pink
    (255, 255, 255),     # White
    (80, 255, 255),      # Cyan
]

# ============================================================
# STAR SYSTEM
# ============================================================

stars = []

for _ in range(180):

    stars.append({
        "x": random.randint(0, WIDTH),
        "y": random.randint(0, HEIGHT),
        "size": random.choice([1, 1, 1, 2]),
        "brightness": random.randint(80, 220),
        "twinkle": random.uniform(0.01, 0.05)
    })


def draw_stars():

    for star in stars:

        # Create a small twinkling effect
        brightness = int(
            star["brightness"]
            + math.sin(pygame.time.get_ticks() * star["twinkle"]) * 40
        )

        brightness = max(40, min(255, brightness))

        color = (
            brightness,
            brightness,
            brightness
        )

        pygame.draw.circle(
            screen,
            color,
            (int(star["x"]), int(star["y"])),
            star["size"]
        )


# ============================================================
# PARTICLE CLASS
# ============================================================

class Particle:

    def __init__(
        self,
        x,
        y,
        color,
        velocity_x,
        velocity_y,
        size=3,
        life=100,
        gravity=0.08,
        friction=0.985,
        glow=True
    ):

        # Particle position
        self.x = x
        self.y = y

        # Particle velocity
        self.vx = velocity_x
        self.vy = velocity_y

        # Particle appearance
        self.color = color
        self.size = size

        # Particle lifetime
        self.life = life
        self.max_life = life

        # Physics
        self.gravity = gravity
        self.friction = friction

        # Whether the particle gets a glow effect
        self.glow = glow

        # Previous position for trails
        self.previous_x = x
        self.previous_y = y

        # Small random variation
        self.rotation = random.random() * math.pi * 2

    # --------------------------------------------------------
    # UPDATE PARTICLE
    # --------------------------------------------------------

    def update(self):

        # Save previous position
        self.previous_x = self.x
        self.previous_y = self.y

        # Apply velocity
        self.x += self.vx
        self.y += self.vy

        # Gravity
        self.vy += self.gravity

        # Air resistance
        self.vx *= self.friction
        self.vy *= self.friction

        # Rotate particle
        self.rotation += 0.1

        # Reduce life
        self.life -= 1

    # --------------------------------------------------------
    # DRAW PARTICLE
    # --------------------------------------------------------

    def draw(self):

        if self.life <= 0:
            return

        # Calculate opacity based on remaining life
        alpha = self.life / self.max_life

        # Calculate particle brightness
        brightness = max(0.2, alpha)

        color = (
            int(self.color[0] * brightness),
            int(self.color[1] * brightness),
            int(self.color[2] * brightness)
        )

        # ----------------------------------------------------
        # Draw particle trail
        # ----------------------------------------------------

        trail_start = (
            int(self.previous_x),
            int(self.previous_y)
        )

        trail_end = (
            int(self.x),
            int(self.y)
        )

        pygame.draw.line(
            screen,
            color,
            trail_start,
            trail_end,
            max(1, self.size // 2)
        )

        # ----------------------------------------------------
        # Draw glow
        # ----------------------------------------------------

        if self.glow:

            glow_size = self.size * 4

            glow_surface = pygame.Surface(
                (glow_size * 2, glow_size * 2),
                pygame.SRCALPHA
            )

            pygame.draw.circle(
                glow_surface,
                (
                    self.color[0],
                    self.color[1],
                    self.color[2],
                    int(40 * alpha)
                ),
                (glow_size, glow_size),
                glow_size
            )

            screen.blit(
                glow_surface,
                (
                    int(self.x - glow_size),
                    int(self.y - glow_size)
                )
            )

        # ----------------------------------------------------
        # Main particle
        # ----------------------------------------------------

        pygame.draw.circle(
            screen,
            color,
            (int(self.x), int(self.y)),
            max(1, int(self.size * alpha))
        )


# ============================================================
# ROCKET CLASS
# ============================================================

class Rocket:

    def __init__(self, x=None):

        # Random horizontal position
        if x is None:
            x = random.randint(100, WIDTH - 100)

        self.x = x
        self.y = HEIGHT + 10

        # Target explosion height
        self.target_y = random.randint(
            int(HEIGHT * 0.15),
            int(HEIGHT * 0.55)
        )

        # Rocket speed
        self.vx = random.uniform(-1.2, 1.2)
        self.vy = random.uniform(-10.5, -13.5)

        # Firework color
        self.color = random.choice(COLORS)

        # Rocket particles
        self.trail = []

        # Rocket size
        self.size = 3

        # Explosion type
        self.explosion_type = random.choice([
            "circle",
            "ring",
            "willow",
            "spiral",
            "heart",
            "double"
        ])

    # --------------------------------------------------------
    # UPDATE ROCKET
    # --------------------------------------------------------

    def update(self):

        # Move rocket
        self.x += self.vx
        self.y += self.vy

        # Slow horizontal movement
        self.vx *= 0.99

        # Gravity slightly affects rocket
        self.vy += 0.08

        # Create rocket trail
        for _ in range(2):

            trail_particle = Particle(
                self.x,
                self.y,
                (
                    255,
                    random.randint(100, 220),
                    40
                ),
                random.uniform(-0.5, 0.5),
                random.uniform(1, 3),
                size=random.randint(1, 3),
                life=random.randint(15, 30),
                gravity=0.08,
                friction=0.95,
                glow=False
            )

            self.trail.append(trail_particle)

        # Remove old trail particles
        for particle in self.trail[:]:

            particle.update()

            if particle.life <= 0:
                self.trail.remove(particle)

        # Determine whether rocket should explode
        return (
            self.y <= self.target_y
            or self.vy >= -1
        )

    # --------------------------------------------------------
    # DRAW ROCKET
    # --------------------------------------------------------

    def draw(self):

        # Draw trail
        for particle in self.trail:
            particle.draw()

        # Draw rocket glow
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.x), int(self.y)),
            self.size
        )


# ============================================================
# FIREWORK CREATION
# ============================================================

particles = []
rockets = []


def create_circle_explosion(x, y, color):

    # Large circular explosion
    particle_count = random.randint(130, 190)

    for _ in range(particle_count):

        angle = random.uniform(0, math.pi * 2)

        speed = random.uniform(2.5, 7.5)

        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed

        particle = Particle(
            x,
            y,
            color,
            vx,
            vy,
            size=random.randint(2, 4),
            life=random.randint(55, 110),
            gravity=0.075,
            friction=0.985
        )

        particles.append(particle)


# ============================================================
# RING EXPLOSION
# ============================================================

def create_ring_explosion(x, y, color):

    # Create particles around a perfect ring
    particle_count = 150

    for i in range(particle_count):

        angle = (
            math.pi * 2
            * i
            / particle_count
        )

        speed = random.uniform(4.5, 6.5)

        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed

        particles.append(
            Particle(
                x,
                y,
                color,
                vx,
                vy,
                size=random.randint(2, 4),
                life=random.randint(70, 110),
                gravity=0.055,
                friction=0.99
            )
        )


# ============================================================
# WILLOW EXPLOSION
# ============================================================

def create_willow_explosion(x, y, color):

    # Willow fireworks have long hanging trails
    for _ in range(120):

        angle = random.uniform(0, math.pi * 2)

        speed = random.uniform(2, 6)

        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed

        particles.append(
            Particle(
                x,
                y,
                color,
                vx,
                vy,
                size=random.randint(2, 4),
                life=random.randint(100, 170),
                gravity=0.12,
                friction=0.985
            )
        )


# ============================================================
# SPIRAL EXPLOSION
# ============================================================

def create_spiral_explosion(x, y, color):

    for i in range(180):

        angle = (
            i * 0.25
            + random.uniform(-0.08, 0.08)
        )

        speed = (
            2
            + i / 40
        )

        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed

        particles.append(
            Particle(
                x,
                y,
                color,
                vx,
                vy,
                size=random.randint(2, 3),
                life=random.randint(70, 120),
                gravity=0.06,
                friction=0.988
            )
        )


# ============================================================
# HEART EXPLOSION
# ============================================================

def create_heart_explosion(x, y, color):

    for _ in range(2):

        for i in range(100):

            t = (
                math.pi * 2
                * i
                / 100
            )

            # Mathematical heart shape
            hx = 16 * math.sin(t) ** 3

            hy = (
                13 * math.cos(t)
                - 5 * math.cos(2 * t)
                - 2 * math.cos(3 * t)
                - math.cos(4 * t)
            )

            scale = 0.35

            vx = hx * scale
            vy = -hy * scale

            # Add slight randomness
            vx += random.uniform(-0.15, 0.15)
            vy += random.uniform(-0.15, 0.15)

            particles.append(
                Particle(
                    x,
                    y,
                    color,
                    vx,
                    vy,
                    size=random.randint(2, 4),
                    life=random.randint(80, 120),
                    gravity=0.05,
                    friction=0.99
                )
            )


# ============================================================
# DOUBLE EXPLOSION
# ============================================================

def create_double_explosion(x, y, color):

    # First explosion
    create_circle_explosion(
        x - 35,
        y,
        color
    )

    # Second explosion
    create_circle_explosion(
        x + 35,
        y,
        random.choice(COLORS)
    )


# ============================================================
# CREATE EXPLOSION
# ============================================================

def explode(rocket):

    if explosion_sound is not None:
        explosion_sound.play()

    x = rocket.x
    y = rocket.y
    color = rocket.color

    if rocket.explosion_type == "circle":

        create_circle_explosion(
            x,
            y,
            color
        )

    elif rocket.explosion_type == "ring":

        create_ring_explosion(
            x,
            y,
            color
        )

    elif rocket.explosion_type == "willow":

        create_willow_explosion(
            x,
            y,
            color
        )

    elif rocket.explosion_type == "spiral":

        create_spiral_explosion(
            x,
            y,
            color
        )

    elif rocket.explosion_type == "heart":

        create_heart_explosion(
            x,
            y,
            color
        )

    elif rocket.explosion_type == "double":

        create_double_explosion(
            x,
            y,
            color
        )


# ============================================================
# CREATE SMALL SECONDARY EXPLOSION
# ============================================================

def create_secondary_explosion(particle):

    # Small burst produced by dying particles
    for _ in range(12):

        angle = random.uniform(
            0,
            math.pi * 2
        )

        speed = random.uniform(
            0.5,
            2.5
        )

        particles.append(
            Particle(
                particle.x,
                particle.y,
                particle.color,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                size=1,
                life=random.randint(15, 30),
                gravity=0.04,
                friction=0.96,
                glow=False
            )
        )


# ============================================================
# LAUNCH FIREWORK
# ============================================================

def launch_firework(x=None):

    if launch_sound is not None:
        launch_sound.play()

    rockets.append(
        Rocket(x)
    )


# ============================================================
# FADE EFFECT
# ============================================================

fade_surface = pygame.Surface(
    (WIDTH, HEIGHT)
)

fade_surface.fill(BLACK)


# ============================================================
# MAIN LOOP
# ============================================================

running = True

while running:

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    for event in pygame.event.get():

        # Ignore the window close button.
        # The app should only close when ESC is pressed.
        if event.type == pygame.QUIT:

            continue

        # Click anywhere to launch a firework
        elif event.type == pygame.MOUSEBUTTONDOWN:

            launch_firework(
                event.pos[0]
            )

        # Keyboard controls
        elif event.type == pygame.KEYDOWN:

            # ESC closes the program
            if event.key == pygame.K_ESCAPE:

                running = False

    # --------------------------------------------------------
    # BACKGROUND
    # --------------------------------------------------------

    # Instead of clearing completely,
    # draw a transparent dark layer.
    # This creates natural particle trails.

    fade_surface.set_alpha(45)

    screen.blit(
        fade_surface,
        (0, 0)
    )

    # Draw stars
    draw_stars()

    # --------------------------------------------------------
    # UPDATE ROCKETS
    # --------------------------------------------------------

    for rocket in rockets[:]:

        should_explode = rocket.update()

        rocket.draw()

        if should_explode:

            explode(rocket)

            rockets.remove(rocket)


    # --------------------------------------------------------
    # UPDATE PARTICLES
    # --------------------------------------------------------

    for particle in particles[:]:

        particle.update()

        particle.draw()

        # Remove dead particles
        if particle.life <= 0:

            # Occasionally create tiny sparks
            if random.random() < 0.08:

                create_secondary_explosion(
                    particle
                )

            particles.remove(
                particle
            )


    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    pygame.display.flip()

    # Limit animation to 60 FPS
    clock.tick(60)


# ============================================================
# CLEANUP
# ============================================================

pygame.quit()