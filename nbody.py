"""N-body problem, implemented in pure Python.

This is just for demo purposes; any sensible implementation should
be based on Cython, Numba, or a GPGPU library.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import random
from typing import List


@dataclass
class Vector:
    """Generic 3D vector
    """

    __slots__ = ("x", "y", "z")

    x: float
    y: float
    z: float

    def __add__(self, other: Vector) -> Vector:
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vector) -> Vector:
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __iadd__(self, other: Vector) -> Vector:
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __isub__(self, other: Vector) -> Vector:
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self

    def __mul__(self, other: float) -> Vector:
        return Vector(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, other: float) -> Vector:
        return Vector(self.x / other, self.y / other, self.z / other)

    @property
    def lensq(self) -> float:
        return self.x ** 2 + self.y ** 2 + self.z ** 2


@dataclass
class Body:
    """State of a celestial object at a certain moment in time
    """

    __slots__ = ("mass", "position", "velocity")

    mass: float
    position: Vector
    velocity: Vector

    def attraction(self, other: Body) -> Vector:
        """Calculate attraction force between two bodies
        """
        dist = self.position - other.position
        dist_modsq = dist.lensq
        dist_unit = dist / math.sqrt(dist_modsq)  # Unit vector
        G = 6.674384e-11
        force_mod = G * self.mass * other.mass / dist_modsq
        return dist_unit * force_mod

    def move(self, force: Vector, dt: float) -> Body:
        """Apply force for dt seconds to this body.
        Return new body with updated velocity and position.
        This object is left unchanged.
        """
        velocity = self.velocity + force / self.mass * dt
        position = self.position + velocity * dt
        return Body(self.mass, position, velocity)


def nbody(bodies: List[Body], dt: float) -> List[Body]:
    """Have N bodies interact with each other, each applying gravitational force to
    each other for dt seconds and thus changing each other's position and velocity.

    :param bodies:
        Initial state of the bodies
    :param float dt:
        Time increment (in seconds). It should be set small enough that any change in
        velocity and position occurring during it should not materially impact the
        next iteration.
    :returns:
        New state of the bodies after dt. The initial state is left unaltered.
    """
    forces = [Vector(0.0, 0.0, 0.0) for _ in bodies]
    for b1, f1 in zip(bodies, forces):
        for b2, f2 in zip(bodies, forces):
            if b1 is not b2:
                force = b1.attraction(b2)
                f1 += force
                f2 -= force
    return [body.move(force, dt) for body, force in zip(bodies, forces)]


def rand_bodies(n: int) -> List[Body]:
    """Generate n bodies at rest, with random uniform weight distribution up to
    1 metric tonne, uniformly distributed within a 1 cubic metre space
    """
    return [
        Body(
            mass=random.uniform(0, 1000),
            position=Vector(random.random(), random.random(), random.random()),
            velocity=Vector(0.0, 0.0, 0.0),
        )
        for _ in range(n)
    ]


if __name__ == "__main__":
    bodies = rand_bodies(2)
    print(bodies)
    for _ in range(5):
        bodies = nbody(bodies, 0.1)
        print(bodies)
